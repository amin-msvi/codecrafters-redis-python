import select
import socket
from datetime import datetime, timedelta

from app.blocking import BlockingState, WaitingClient
from app.commands.base import (
    BlockingResponse,
    CommandResult,
    RDBSync,
    WaitBlocker,
)
from app.commands.registry import CommandRegistry
from app.config import TCPServerConfig
from app.logger import get_logger
from app.resp_encoder import encode_resp
from app.resp_parser import parse_request
from app.server.base_role import ParkClient, SendResponse, TransferToRole
from app.server.pubsub import PubSubState
from app.server.roles import ServerRole
from app.server.server_info import ServerInfo, User
from app.server.transaction import ExecResult, TransactionState
from app.types import EncodeableValue, NullArray, RESPError, RESPProtocolError, SimpleString

logger = get_logger(__name__)


class RedisServer:
    def __init__(
        self,
        role: ServerRole,
        registry: CommandRegistry,
        config: TCPServerConfig,
        server_info: ServerInfo,
        pubsub_state: PubSubState,
        user: User,
    ):
        self._role = role
        self._config = config
        self._registry = registry
        self._server_socket: socket.socket | None = None
        self._connections: list[socket.socket] = []
        self._blocking_state: BlockingState = BlockingState()
        self._transaction_state = TransactionState(registry)
        self._server_info = server_info
        self._pubsub_state = pubsub_state
        self._user = user
        self._authenticated_users = []

    def start(self):
        logger.info("Starting server on %s:%d", self._config.host, self._config.port)
        self._server_socket = socket.create_server(
            (self._config.host, self._config.port), reuse_port=True
        )
        self._server_socket.setblocking(False)
        self._role.on_startup()
        try:
            self._run_event_loop()
        finally:
            self._shutdown()

    def _run_event_loop(self):
        while True:
            all_sockets = [self._server_socket] + self._connections
            all_sockets += self._role.get_extra_sockets()
            ready, _, _ = select.select(
                all_sockets, [], [], self._config.select_timeout
            )

            for sock in ready:
                assert sock is not None
                if sock == self._server_socket:
                    self._accept_connection()
                elif self._role.owns_socket(sock):
                    self._role.handle_socket(sock)
                else:
                    self._handle_client(sock)

            self._handle_expired_blockers()
            self._role.handle_expired_clients()

    def _handle_client(self, client: socket.socket):
        data = client.recv(self._config.recv_buffer_size)

        if data == b"":
            self._remove_client(client)
            return

        reader_pointer = 0
        parsed_requests = parse_request(data)
        for parsed_data, cmd_name, consumed in parsed_requests:
            action = self._process_request(parsed_data, cmd_name, client)
            cmd_flag = self._registry.get_flags(cmd_name)

            match action:
                case TransferToRole(header, rdb):
                    client.sendall(header)
                    client.sendall(rdb)
                    self._role.add_socket(client)
                    self._connections.remove(client)
                case SendResponse(response):
                    client.sendall(response)
                case ParkClient():
                    pass

            command_bytes = data[reader_pointer : reader_pointer + consumed]
            reader_pointer += consumed
            self._role.after_command(command_bytes, cmd_flag)

    def _process_request(
        self, parsed_data: list[str], cmd_name: str, client: socket.socket
    ) -> SendResponse | TransferToRole | ParkClient:
        """Execute, and encode a request."""

        try:
            # Authentication
            auth_result = self._auth_user(client, parsed_data, cmd_name)
            if auth_result is not None:
                return SendResponse(response=encode_resp(auth_result))

            # Transactions
            transaction_result = self._transaction_state.intercept(
                client, parsed_data, cmd_name
            )
            if transaction_result is not None:
                if isinstance(transaction_result, ExecResult):
                    for key in transaction_result.events:
                        self._try_unblock(key)
                    return SendResponse(response=encode_resp(transaction_result.result))
                return SendResponse(response=encode_resp(transaction_result))

            # PubSub
            pubsub_result = self._pubsub_state.intercept(client, parsed_data, cmd_name)

            if pubsub_result is not None:
                return SendResponse(response=encode_resp(pubsub_result))

            # Execution
            result = self._registry.execute(parsed_data)

            match result:
                case CommandResult(response, event):
                    if event:
                        self._try_unblock(event.key)
                    return SendResponse(response=encode_resp(response))
                case BlockingResponse():
                    self._add_blocker(result, client)
                    return ParkClient()
                case RDBSync(response, rdb):
                    return TransferToRole(
                        header=encode_resp(response), rdb=encode_resp(rdb)
                    )
                case WaitBlocker():
                    self._role.on_wait(result, client)
                    return ParkClient()
                case RESPError():
                    return SendResponse(response=encode_resp(result))
                case _:
                    raise ValueError(f"Unexpected result type: {type(result)}")

        except RESPProtocolError as e:
            logger.warning("Protocol error: %s", e)
            return SendResponse(response=encode_resp(RESPError("-ERR protocol error")))

    def _accept_connection(self) -> None:
        if self._server_socket is None:
            return
        connection, address = self._server_socket.accept()
        logger.info("Connection received from %s", address)
        self._connections.append(connection)

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

    # Authentication
    def _auth_user(self, client: socket.socket, parsed_data: list[str], cmd_name: str) -> EncodeableValue:
    
        if cmd_name == "ACL":
            if parsed_data[1] == "SETUSER":
                username, password = parsed_data[2:]
                self._authenticated_users.append(client)
                return self._user.info.set_user(password)

        if cmd_name == "AUTH":
            username, password = parsed_data[1:]
            auth_result = self._user.auth(username, password)
            if isinstance(auth_result, SimpleString):
                self._authenticated_users.append(client)
            return auth_result

        if "nopass" in self._user.info.flags:
            return

        if client in self._authenticated_users:
            return

        return RESPError("-NOAUTH Authentication required.")

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
