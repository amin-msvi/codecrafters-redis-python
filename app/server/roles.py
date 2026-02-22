import socket
from app.commands.base import CommandFlags, CommandResult
from app.commands.registry import CommandRegistry
from app.logger import get_logger
from app.resp_encoder import encode_resp
from app.server.base_role import ServerRole
from app.server.buffer import RESPBuffer
from app.server.server_info import ServerInfo


logger = get_logger(__name__)


class ReplicaRole(ServerRole):
    def __init__(self, master_socket: socket.socket, server_info: ServerInfo, registry: CommandRegistry, buffer: bytes):
        self._master_socket: socket.socket | None = master_socket
        self._server_info = server_info
        self._registry = registry
        self._buffer = RESPBuffer(buffer)

    def on_startup(self) -> None:
        assert self._master_socket is not None
        self._master_socket.setblocking(False)
        self._process_buffer()

    def handle_socket(self) -> None:
        if self._master_socket is None:
            return
        try:
            data = self._master_socket.recv(1024)
        except BlockingIOError:
            return

        if data == b"":
            self._master_socket = None
            return

        self._buffer.append(data)
        self._process_buffer()

    # Private Methods
    def _process_buffer(self):
        if not self._buffer:
            return

        requests = self._buffer.parse_all()

        for parsed_data, _, offset in requests:
            response = self._registry.execute(parsed_data)
            self._server_info.replication.incr_offset(offset)
            if isinstance(response, CommandResult) and response.ack_master:
                if self._master_socket is not None:
                    self._master_socket.sendall(encode_resp(response.response))
        self._buffer.flush()

    def get_extra_sockets(self) -> list[socket.socket]:
        return [self._master_socket] if self._master_socket else []

    def owns_socket(self, sock: socket.socket) -> bool:
        return self._master_socket is not None and sock == self._master_socket

    def add_socket(self, sock: socket.socket) -> None:
        return

    def after_command(self, data: bytes, flags: CommandFlags | None) -> None:
        return


class MasterRole(ServerRole):
    def __init__(self):
        self._replicas: list[socket.socket] = []

    def on_startup(self) -> None:
        return

    def after_command(self, data: bytes, flags: CommandFlags | None) -> None:
        if self._replicas and flags and flags.write:
            for replica in self._replicas:
                replica.sendall(data)

    def owns_socket(self, sock: socket.socket) -> bool:
        return False

    def add_socket(self, sock: socket.socket) -> None:
        return self._replicas.append(sock)

    def get_extra_sockets(self) -> list[socket.socket]:
        return []

    def handle_socket(self) -> None:
        return
