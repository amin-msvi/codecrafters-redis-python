import select
import socket
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from app.blocking import BlockingState, WaitingClient
from app.commands.base import BlockingResponse, UnblockEvent
from app.config import DEFAULT_SERVER_CONFIG, ServerConfig
from app.logger import get_logger
from app.resp_encoder import encode_resp
from app.resp_parser import parse_resp
from app.types import NullArray, RESPError, RESPProtocolError

if TYPE_CHECKING:
    from app.commands.registry import CommandRegistry

logger = get_logger(__name__)


class RedisServer:
    def __init__(
        self,
        registry: "CommandRegistry",
        config: ServerConfig = DEFAULT_SERVER_CONFIG,
    ):
        self._config = config
        self._registry = registry
        self._server_socket: socket.socket | None = None
        self._connections: list[socket.socket] = []
        self._blocking_state = BlockingState()

    def start(self) -> None:
        logger.info("Starting server on %s:%d", self._config.host, self._config.port)
        self._server_socket = socket.create_server(
            (self._config.host, self._config.port), reuse_port=True
        )
        self._server_socket.setblocking(False)

        try:
            self._run_event_loop()
        finally:
            self._shutdown()

    def _run_event_loop(self) -> None:
        assert self._server_socket is not None

        while True:
            all_sockets: list[socket.socket] = [self._server_socket] + self._connections
            ready_to_read, _, _ = select.select(all_sockets, [], [], 0.1)

            for ready_socket in ready_to_read:
                if ready_socket == self._server_socket:
                    self._accept_connection()
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
            client.sendall(response)

    def _process_request(self, data: bytes, client: socket.socket) -> bytes | None:
        """Parse, execute, and encode a request."""
        try:
            parsed_data = parse_resp(data)[0]
            result = self._registry.execute(parsed_data)

            event = None
            if isinstance(result, tuple):
                result, event = result

            if isinstance(result, BlockingResponse):
                self._add_blocker(result, client)
                return None

            # Command produced data - check for waiters
            if isinstance(event, UnblockEvent):
                self._try_unblock(event.key)

            return encode_resp(result)

        except RESPProtocolError as e:
            logger.warning("Protocol error: %s", e)
            return encode_resp(RESPError("ERR protocol error"))

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

        key, value = result
        response = encode_resp([key, value])
        waiter.socket.sendall(response)

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
