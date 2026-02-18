import socket
from typing_extensions import TYPE_CHECKING
from app.commands.base import CommandFlags, CommandResult
from app.config import ServerConfig
from app.logger import get_logger
from app.resp_encoder import encode_resp
from app.resp_parser import parse_resp
from app.server.base_role import ServerRole
from app.server.server_info import MasterInfo, ServerInfo
from app.types import RESPProtocolError, RESPValue

if TYPE_CHECKING:
    from app.server.server import RedisServer


logger = get_logger(__name__)


class ReplicaRole(ServerRole):
    def __init__(self, master_info: MasterInfo, server_info: ServerInfo, config: ServerConfig):
        self._master_info = master_info
        self._server_info = server_info
        self._config = config
        self._buffer: bytes = b""

    def on_startup(self, server: "RedisServer") -> None:
        self._server = server
        self._connect_to_master()
        self._handshake()
    
    def _process_buffer(self, sock):
        responses = self._server.run_command(self._buffer)
        self._buffer = b""
        for response in responses:
            if isinstance(response["response"], CommandResult):
                print("RESPONSE", response)
                # self._server_info.replication.incr_offset(response["offset_count"])
                if response["response"].ack_master:
                    sock.sendall(encode_resp(response["response"].response))

    def handle_socket(self, sock: socket.socket) -> None:
        self._recv_into_buffer()
        if not self._buffer:
            return
        self._process_buffer(sock)

    # Private Methods
    def _recv_into_buffer(self) -> None:
        data = self._master_socket.recv(1024)
        if data == b"":
            return
        self._buffer += data

    def _read_message(self) -> RESPValue:
        self._recv_into_buffer()
        
        while self._buffer:
            try:
                parsed_data, remaining = parse_resp(self._buffer)
                self._buffer = remaining
                return parsed_data
            except RESPProtocolError:
                self._recv_into_buffer()

    def _read_rdb(self) -> bytes:
        self._recv_into_buffer()
        while self._buffer:
            length_end_idx = self._buffer.index(b"\r\n")
            length = int(self._buffer[1:length_end_idx].decode("utf-8"))
            data_start = length_end_idx + 2
            data_end = data_start + length
            string_data = self._buffer[data_start:data_end]
            self._buffer = self._buffer[data_end:]
            return string_data

    def _connect_to_master(self):
        """
        This method runs when this server is a replica and
        wants to connect to the master server
        """

        self._master_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # self._master_socket.setblocking(False)
        try:
            self._master_socket.connect(
                (self._master_info.host, self._master_info.port)
            )
            logger.info(
                f"Connected to master server at '{self._master_info.host}:{self._master_info.port}'"
            )
        except socket.error as e:
            logger.error("Connection Failed", e)

    def _handshake(self):
        """Applies 3-step Redis handshake protocol between replica and master"""

        # Step 1
        self._master_socket.sendall(encode_resp(["PING"]))
        response = self._read_message()
        if response != "PONG":
            return

        # Step 2
        replconf: bytes = encode_resp(
            ["REPLCONF", "listening-port", str(self._config.port)]
        )
        self._master_socket.sendall(replconf)
        response = self._read_message()
        if response != "OK":
            return

        replconf = encode_resp(["REPLCONF", "capa", "psync2"])
        self._master_socket.sendall(replconf)
        response = self._read_message()
        if response != "OK":
            return

        # Step 3
        psync: bytes = encode_resp(["PSYNC", "?", "-1"])
        self._master_socket.sendall(psync)
        response = self._read_message()
        self._read_rdb()
        self._process_buffer(self._master_socket)

    def get_extra_sockets(self) -> list[socket.socket]:
        return [self._master_socket]

    def owns_socket(self, sock: socket.socket) -> bool:
        return sock == self._master_socket

    def add_socket(self, sock: socket.socket) -> None:
        return

    def after_command(self, data: bytes, flags: CommandFlags | None) -> None:
        return

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
