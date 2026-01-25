import select
import socket
from typing import TYPE_CHECKING

from app.config import DEFAULT_SERVER_CONFIG, ServerConfig
from app.logger import get_logger
from app.resp_encoder import encode_resp
from app.resp_parser import parse_resp
from app.types import RESPError, RESPProtocolError

if TYPE_CHECKING:
    from app.commands.registry import CommandRegistry

logger = get_logger(__name__)


class RedisServer:
    def __init__(
        self, registry: "CommandRegistry", config: ServerConfig = DEFAULT_SERVER_CONFIG
    ):
        self._config = config
        self._registry = registry
        self._server_socket: socket.socket | None = None
        self._connections: list[socket.socket] = []

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
        while True:
            all_sockets = [self._server_socket] + self._connections
            ready_to_read, _, _ = select.select(all_sockets, [], [])

            for ready_socket in ready_to_read:
                if ready_socket == self._server_socket:
                    self._accept_connection()
                else:
                    self._handle_client(
                        ready_socket  # pyright: ignore [reportArgumentType]
                    )

    def _accept_connection(self) -> None:
        connection, address = self._server_socket.accept()  # pyright: ignore [reportOptionalMemberAccess]
        logger.info("Connection received from %s", address)
        self._connections.append(connection)

    def _handle_client(self, client: socket.socket) -> None:
        data = client.recv(self._config.recv_buffer_size)

        if data == b"":
            self._remove_client(client)
            return

        response = self._process_request(data)
        client.sendall(response)

    def _process_request(self, data: bytes) -> bytes:
        """Parse, execute, and encode a request."""
        try:
            parsed_data = parse_resp(data)[0]
            result = self._registry.execute(parsed_data)
        except RESPProtocolError as e:
            logger.warning("Protocol error: %s", e)
            result = RESPError("ERR protocol error")

        return encode_resp(result)

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
