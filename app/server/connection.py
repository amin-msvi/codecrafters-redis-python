from app.logger import get_logger
import socket
from app.config import TCPServerConfig
from app.resp_encoder import encode_resp
from app.server.buffer import RESPBuffer
from app.server.server_info import MasterInfo

logger = get_logger(__name__)


class MasterConnection:
    def __init__(self, master_info: MasterInfo, config: TCPServerConfig):
        self._buffer = RESPBuffer(config)
        self._master_info = master_info
        self._config = config

    def establish(self) -> tuple[socket.socket, bytes]:
        """Connect, handshake, read RDB, return a ready non-blocking socket."""
        sock = self._connect()
        self._handshake(sock)
        self._buffer.read_rdb(sock)
        return sock, self._buffer.get_data()

    def _connect(self) -> socket.socket:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect((self._master_info.host, self._master_info.port))
            logger.info(
                f"Connected to master server at '{self._master_info.host}:{self._master_info.port}'"
            )
        except socket.error as e:
            logger.error("Connection Failed", e)

        return sock

    def _handshake(self, sock) -> None:
        """Applies 3-step Redis handshake protocol between replica and master"""

        # Step 1
        sock.sendall(encode_resp(["PING"]))
        response = self._buffer.read_one(sock)
        if response != "PONG":
            return

        # Step 2
        replconf: bytes = encode_resp(
            ["REPLCONF", "listening-port", str(self._config.port)]
        )
        sock.sendall(replconf)
        response = self._buffer.read_one(sock)
        if response != "OK":
            return

        replconf = encode_resp(["REPLCONF", "capa", "psync2"])
        sock.sendall(replconf)
        response = self._buffer.read_one(sock)
        if response != "OK":
            return

        # Step 3
        psync: bytes = encode_resp(["PSYNC", "?", "-1"])
        sock.sendall(psync)
        response = self._buffer.read_one(sock)
