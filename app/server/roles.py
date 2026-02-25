from datetime import datetime
import socket
from app.commands.base import CommandFlags, CommandResult, WaitBlocker
from app.commands.registry import CommandRegistry
from app.logger import get_logger
from app.resp_encoder import encode_resp
from app.server.base_role import ServerRole
from app.server.buffer import RESPBuffer
from app.server.server_info import ServerInfo

logger = get_logger(__name__)


class ReplicaRole(ServerRole):
    def __init__(
        self,
        master_socket: socket.socket,
        server_info: ServerInfo,
        registry: CommandRegistry,
        buffer: bytes,
    ):
        self._master_socket: socket.socket | None = master_socket
        self._server_info = server_info
        self._registry = registry
        self._buffer: RESPBuffer = RESPBuffer(buffer)

    def on_startup(self) -> None:
        assert self._master_socket is not None
        self._master_socket.setblocking(False)
        self._process_buffer()

    def handle_socket(self, sock: socket.socket) -> None:
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

    def on_wait(self, waiter_blocker: WaitBlocker, sock: socket.socket) -> None:
        return

    def handle_expired_clients(self) -> None:
        return


class MasterRole(ServerRole):
    def __init__(self, server_info: ServerInfo, registry: CommandRegistry):
        self._registry = registry
        self._server_info = server_info
        self._replicas: list[socket.socket] = []
        self._buffer: RESPBuffer = RESPBuffer()
        self._wait_waiter: WaitBlocker | None = None

    def on_startup(self) -> None:
        return

    def after_command(self, data: bytes, flags: CommandFlags | None) -> None:
        if self._replicas and flags and flags.write:
            self._server_info.replication.incr_offset(len(data))
            for replica in self._replicas:
                replica.sendall(data)
            return

    def owns_socket(self, sock: socket.socket) -> bool:
        return self._replicas is not None and sock in self._replicas

    def add_socket(self, sock: socket.socket) -> None:
        self._server_info.replication.incr_slaves()
        return self._replicas.append(sock)

    def get_extra_sockets(self) -> list[socket.socket]:
        return self._replicas

    def on_wait(self, waiter_blocker: WaitBlocker, sock: socket.socket) -> None:
        if self._server_info.replication.connected_slaves == 0:
            sock.sendall(encode_resp(0))
            return
        if waiter_blocker.target_offset == 0:
            sock.sendall(encode_resp(self._server_info.replication.connected_slaves))
            return

        waiter_blocker.socket = sock
        self._wait_waiter = waiter_blocker

        replconf: bytes = encode_resp(["REPLCONF", "GETACK", "*"])
        for replica in self._replicas:
            replica.sendall(replconf)

    def handle_expired_clients(self) -> None:
        if not self._wait_waiter:
            return

        now = datetime.now()
        if (
            self._wait_waiter.socket
            and self._wait_waiter.timeout
            and now >= self._wait_waiter.timeout
        ):
            self._wait_waiter.socket.sendall(encode_resp(self._wait_waiter.acked))
            self._wait_waiter = None

    def handle_socket(self, sock: socket.socket) -> None:
        try:
            data = sock.recv(1024)
        except BlockingIOError:
            return

        if data == b"":
            self._replicas.remove(sock)
            return

        self._buffer.append(data)
        self._process_buffer()

    def _process_buffer(self):
        if not self._buffer:
            return

        requests = self._buffer.parse_all()

        if not self._wait_waiter:
            self._buffer.flush()
            return

        for parsed_data, cmd_name, offset in requests:
            if cmd_name == "REPLCONF" and parsed_data[1] == "ACK":
                # Here we get the offset count of the replica.
                offset = int(parsed_data[2])
                if offset >= self._server_info.replication.master_repl_offset:
                    if self._wait_waiter:
                        self._wait_waiter.acked += 1
                if (
                    self._wait_waiter
                    and self._wait_waiter.min_replicas <= self._wait_waiter.acked
                ):
                    assert isinstance(self._wait_waiter.socket, socket.socket)
                    self._wait_waiter.socket.sendall(
                        encode_resp(self._wait_waiter.acked)
                    )
                    self._wait_waiter.acked = 0
                    self._wait_waiter = None
        self._buffer.flush()
