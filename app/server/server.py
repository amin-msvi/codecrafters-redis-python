import select
import socket
from datetime import datetime, timedelta

from app.blocking import BlockingState, WaitingClient
from app.commands.base import BlockingResponse, CommandFlags, CommandResult, RDBSync
from app.commands.registry import CommandRegistry
from app.config import ServerConfig
from app.logger import get_logger
from app.resp_encoder import encode_resp
from app.resp_parser import parse_resp
from app.server.roles import ServerRole
from app.types import NullArray, RESPError, RESPProtocolError, RESPValue, SimpleString

logger = get_logger(__name__)


class RedisServer:
    def __init__(
        self, role: ServerRole, registry: CommandRegistry, config: ServerConfig
    ):
        self._role = role
        self._config = config
        self._registry = registry
        self._server_socket: socket.socket | None = None
        self._connections: list[socket.socket] = []
        self._blocking_state: BlockingState = BlockingState()
        self._transactions: dict[socket.socket, list[RESPValue]] = {}

    def start(self):
        logger.info("Starting server on %s:%d", self._config.host, self._config.port)
        self._server_socket = socket.create_server(
            (self._config.host, self._config.port), reuse_port=True
        )
        self._server_socket.setblocking(False)
        self._role.on_startup(self)
        try:
            self._run_event_loop()
        finally:
            self._shutdown()

    def run_command(
        self, data: bytes
    ) -> list[dict[str, CommandResult | BlockingResponse | RDBSync | RESPError]]:
        requests = self._parse_request(data)
        responses = []
        for parsed_data, cmd_name, _ in requests:
            responses.append(
                {"response": self._registry.execute(parsed_data), "cmd_name": cmd_name,
                    "offset_count": len(data)}
            )
        return responses

    def _run_event_loop(self):
        while True:
            all_sockets = [self._server_socket] + self._connections
            all_sockets += self._role.get_extra_sockets()
            ready, _, _ = select.select(all_sockets, [], [], 0.1)

            for sock in ready:
                assert sock is not None
                if sock == self._server_socket:
                    self._accept_connection()
                elif self._role.owns_socket(sock):
                    self._role.handle_socket(sock)
                else:
                    self._handle_client(sock)

            self._handle_expired_blockers()

    def _handle_client(self, client: socket.socket):
        data = client.recv(self._config.recv_buffer_size)

        if data == b"":
            self._remove_client(client)
            return

        parsed_requests = self._parse_request(data)
        for parsed_data, cmd_name, cmd_flags in parsed_requests:
            response = self._process_request(parsed_data, cmd_name, client)

            if response:
                if isinstance(response, tuple):
                    client.sendall(response[0])
                    client.sendall(response[1])
                    self._role.add_socket(client)
                else:
                    client.sendall(response)

            self._role.after_command(data, cmd_flags)

    def _parse_request(
        self, data: bytes
    ) -> list[tuple[list, str, CommandFlags | None]]:
        requests = []
        remaining = data

        while remaining:
            parsed_data, remaining = parse_resp(remaining)
            if not isinstance(parsed_data, list):
                continue
            cmd = parsed_data[0].upper()
            cmd_flags = self._registry.get_flags(cmd)
            requests.append((parsed_data, cmd, cmd_flags))
        return requests

    def _process_request(
        self, parsed_data: list[str], cmd_name: str, client: socket.socket
    ) -> tuple[bytes, bytes] | bytes | None:
        """Execute, and encode a request."""
        try:
            # Transactions
            if cmd_name == "MULTI":
                self._transactions[client] = []
                return encode_resp(SimpleString("OK"))

            if cmd_name == "EXEC":
                result = self._execute_transaction_commands(client)
                return encode_resp(result)

            if cmd_name == "DISCARD":
                if client in self._transactions:
                    del self._transactions[client]
                    return encode_resp(SimpleString("OK"))
                else:
                    return encode_resp(RESPError("DISCARD without MULTI"))

            if client in self._transactions:
                self._transactions[client].append(parsed_data)
                return encode_resp(SimpleString("QUEUED"))

            result = self._registry.execute(parsed_data)

            if isinstance(result, BlockingResponse):
                self._add_blocker(result, client)
                return None

            if isinstance(result, RDBSync):
                return encode_resp(result.response), encode_resp(result.rdb)

            if isinstance(result, CommandResult):
                if result.event:
                    self._try_unblock(result.event.key)
                return encode_resp(result.response)

            return encode_resp(result)

        except RESPProtocolError as e:
            logger.warning("Protocol error: %s", e)
            return encode_resp(RESPError("ERR protocol error"))

    def _accept_connection(self) -> None:
        assert self._server_socket is not None
        connection, address = self._server_socket.accept()
        logger.info("Connection received from %s", address)
        self._connections.append(connection)

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
            result = self._registry.execute(arg)
            if isinstance(result, CommandResult):
                if result.event:
                    self._try_unblock(result.event.key)
                results.append(result.response)
            else:
                results.append(result)
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
