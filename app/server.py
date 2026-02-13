import select
import socket
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from app.blocking import BlockingState, WaitingClient
from app.commands.base import BlockingResponse, UnblockEvent
from app.commands.psync import RDBSync
from app.config import ServerConfig
from app.logger import get_logger
from app.resp_encoder import encode_resp
from app.resp_parser import parse_resp
from app.server_info import MasterInfo
from app.types import NullArray, RESPError, RESPProtocolError, RESPValue, SimpleString

if TYPE_CHECKING:
    from app.commands.registry import CommandRegistry

logger = get_logger(__name__)


class RedisServer:
    def __init__(
        self,
        registry: "CommandRegistry",
        config: ServerConfig,
        master_info: MasterInfo | None,
    ):
        self._config = config
        self._registry = registry
        self._server_socket: socket.socket | None = None
        self._connections: list[socket.socket] = []
        self._blocking_state = BlockingState()
        self._transactions: dict[socket.socket, list[RESPValue]] = {}
        self.master_info = master_info
        self._master_socket = None

    def start(self) -> None:
        logger.info("Starting server on %s:%d", self._config.host, self._config.port)
        self._server_socket = socket.create_server(
            (self._config.host, self._config.port), reuse_port=True
        )
        self._server_socket.setblocking(False)
        
        self._connect_to_server()
        
        try:
            self._run_event_loop()
        finally:
            self._shutdown()

    # Private Methods
    def _run_event_loop(self) -> None:
        assert self._server_socket is not None

        while True:
            all_sockets: list[socket.socket] = [self._server_socket] + self._connections
            if self._master_socket:
                all_sockets.append(self._master_socket)
            ready_to_read, _, _ = select.select(all_sockets, [], [], 0.1)

            for ready_socket in ready_to_read:
                if ready_socket == self._server_socket:
                    self._accept_connection()
                elif ready_socket == self._master_socket:
                    pass
                else:
                    self._handle_client(ready_socket)

            self._handle_expired_blockers()

    def _accept_connection(self) -> None:
        assert self._server_socket is not None
        connection, address = self._server_socket.accept()
        logger.info("Connection received from %s", address)
        self._connections.append(connection)

    def _handle_client(self, client: socket.socket) -> None:
        data = client.recv(self._config.recv_buffer_size)

        if data == b"":
            self._remove_client(client)
            return

        response = self._process_request(data, client)

        if response:
            if isinstance(response, tuple):
                client.sendall(response[0])
                client.sendall(response[1])
            else:
                client.sendall(response)

    def _process_request(self, data: bytes, client: socket.socket) -> tuple[bytes, bytes] | bytes | None:
        """Parse, execute, and encode a request."""
        try:
            parsed_data = parse_resp(data)[0]

            # Transactions
            if isinstance(parsed_data, list):
                cmd = parsed_data[0].upper()
                if cmd == "MULTI":
                    self._transactions[client] = []
                    return encode_resp(SimpleString("OK"))

                if cmd == "EXEC":
                    result = self._execute_transaction_commands(client)
                    return encode_resp(result)

                if cmd == "DISCARD":
                    if client in self._transactions:
                        del self._transactions[client]
                        return encode_resp(SimpleString("OK"))
                    else:
                        return encode_resp(RESPError("DISCARD without MULTI"))

            if client in self._transactions:
                self._transactions[client].append(parsed_data)
                return encode_resp(SimpleString("QUEUED"))

            result = self._registry.execute(parsed_data)

            # Expiry
            event = None
            if isinstance(result, tuple):
                result, event = result

            if isinstance(result, BlockingResponse):
                self._add_blocker(result, client)
                return None

            if isinstance(event, UnblockEvent):
                self._try_unblock(event.key)

            if isinstance(result, RDBSync):
                return encode_resp(result.response), encode_resp(result.rdb)

            return encode_resp(result)

        except RESPProtocolError as e:
            logger.warning("Protocol error: %s", e)
            return encode_resp(RESPError("ERR protocol error"))
    
    # Server Connection Method
    def _connect_to_server(self):
        if self.master_info is None:
            return
        
        self._master_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self._master_socket.connect((self.master_info.host, self.master_info.port))
            logger.info(
                f"Connected to master server at '{self.master_info.host}:{self.master_info.port}'"
            )

            self._handshake()

        except socket.error as e:
            logger.error("Connection Failed", e)
    
    def _handshake(self):
        if not self._master_socket:
            return

        # Step 1
        self._master_socket.sendall(encode_resp(["PING"]))
        data = self._master_socket.recv(1024)
        if parse_resp(data)[0] != "PONG":
            return
            
        # Step 2
        replconf: bytes = encode_resp(["REPLCONF", "listening-port", str(self._config.port)])
        self._master_socket.sendall(replconf)
        data = self._master_socket.recv(1024)
        if parse_resp(data)[0] != "OK":
            return

        replconf = encode_resp(["REPLCONF", "capa", "psync2"])
        self._master_socket.sendall(replconf)
        data = self._master_socket.recv(1024)
        if parse_resp(data)[0] != "OK":
            return

        # Step 3
        psync: bytes = encode_resp(["PSYNC", "?", "-1"])
        self._master_socket.sendall(psync)
        data = self._master_socket.recv(1024)
        master_response = parse_resp(data)[0]  # noqa

    # Transaction Methods
    def _execute_transaction_commands(self, client: socket.socket):
        args = self._transactions.get(client)
        results = []
        if args is None:
            return RESPError("EXEC without MULTI")
        if args == []:
            del self._transactions[client]
            return []
        for arg in args:
            results.append(self._registry.execute(arg))
        del self._transactions[client]
        return results

    # Blocking Methods
    def _add_blocker(self, response: BlockingResponse, client: socket.socket) -> None:
        """Register a client as blocked waiting for keys."""
        timeout_at = (
            datetime.now() + timedelta(seconds=response.timeout)
            if response.timeout != 0
            else None  # Wait forever
        )
        waiter = WaitingClient(
            socket=client,
            keys=response.keys,
            timeout_at=timeout_at,
            callback=response.unblock_callback,
        )
        self._blocking_state.add(waiter)

    def _try_unblock(self, key: str) -> None:
        """Wake the first waiter for a key if data exists."""
        waiter = self._blocking_state.pop(key)
        if waiter is None:
            return

        result = waiter.callback(key)
        if result is None:
            return

        if isinstance(result, tuple):
            key, value = result
            waiter.socket.sendall(encode_resp([key, value]))

        if isinstance(result, list):
            waiter.socket.sendall(encode_resp(result))

    def _handle_expired_blockers(self) -> None:
        """Send null array to clients whose timeout has passed."""
        now = datetime.now()
        for client in self._blocking_state.get_expired(now):
            client.socket.sendall(encode_resp(NullArray()))
            self._blocking_state.remove(client)

    def _remove_client(self, client: socket.socket) -> None:
        """Clean up a disconnected client."""
        logger.info("Client disconnected: %s", client.getpeername())
        self._connections.remove(client)
        client.close()

    def _shutdown(self) -> None:
        """Clean up all connections and server socket."""
        logger.info("Shutting down server")
        for connection in self._connections:
            connection.close()
        self._connections.clear()

        if self._server_socket:
            self._server_socket.close()
            self._server_socket = None
