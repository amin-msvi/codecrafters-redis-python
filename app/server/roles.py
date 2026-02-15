import socket
from typing_extensions import TYPE_CHECKING
from app.commands.base import CommandFlags
from app.config import ServerConfig
from app.logger import get_logger
from app.resp_encoder import encode_resp
from app.resp_parser import parse_resp
from app.server.base_role import ServerRole
from app.server.server_info import MasterInfo

if TYPE_CHECKING:
    from app.server.server import RedisServer


logger = get_logger(__name__)


class ReplicaRole(ServerRole):
    def __init__(self, master_info: MasterInfo, config: ServerConfig):
        self._master_info = master_info
        self._config = config

    def on_startup(self, server: "RedisServer") -> None:
        self._connect_to_master()

    def handle_socket(self, sock: socket.socket) -> None:
        pass

    def get_extra_sockets(self) -> list[socket.socket]:
        return [self._master_socket]

    def owns_socket(self, sock: socket.socket) -> bool:
        return sock == self._master_socket

    def add_socket(self, sock: socket.socket) -> None:
        return

    def after_command(self, data: bytes, flags: CommandFlags | None) -> None:
        return

    # Private Methods
    def _connect_to_master(self):
        """
        This method runs when this server is a replica and
        wants to connect to the master server
        """

        self._master_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self._master_socket.connect(
                (self._master_info.host, self._master_info.port)
            )
            logger.info(
                f"Connected to master server at '{self._master_info.host}:{self._master_info.port}'"
            )

            self._handshake()

        except socket.error as e:
            logger.error("Connection Failed", e)

    def _handshake(self):
        """Applies 3-step Redis handshake protocol between replica and master"""

        # Step 1
        self._master_socket.sendall(encode_resp(["PING"]))
        data = self._master_socket.recv(1024)
        if parse_resp(data)[0] != "PONG":
            return

        # Step 2
        replconf: bytes = encode_resp(
            ["REPLCONF", "listening-port", str(self._config.port)]
        )
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


class MasterRole(ServerRole):
    def __init__(self):
        self._replicas: list[socket.socket] = []

    def on_startup(self, server: "RedisServer") -> None:
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

    def handle_socket(self, sock: socket.socket) -> None:
        return
