import socket

from app.resp_parser import parse_request, parse_resp
from app.types import RESPProtocolError, RESPValue


class RESPBuffer:
    def __init__(self, buffer: bytes = b""):
        self._buffer = buffer

    def append(self, data: bytes):
        self._buffer += data

    def read_rdb(self, sock) -> bytes | None:
        if not self._buffer:
            self.recv(sock)
        if not self._buffer:
            return

        length_end_idx = self._buffer.index(b"\r\n")
        length = int(self._buffer[1:length_end_idx].decode("utf-8"))
        data_start = length_end_idx + 2
        data_end = data_start + length
        string_data = self._buffer[data_start:data_end]
        self._buffer = self._buffer[data_end:]
        return string_data

    def recv(self, sock) -> None:
        data = sock.recv(1024)
        if data == b"":
            return
        self.append(data)

    def read_one(self, sock: socket.socket) -> RESPValue:
        self.recv(sock)
        while self:
            try:
                parsed_data, remaining = parse_resp(self._buffer)
                self.update(remaining)
                return parsed_data
            except RESPProtocolError:
                self.recv(sock)

    def parse_all(self) -> list[tuple[list, str, int]]:
        return parse_request(self._buffer)

    def update(self, data: bytes):
        self._buffer = data

    def flush(self):
        self._buffer = b""

    def get_data(self) -> bytes:
        return self._buffer

    def __bool__(self):
        return self._buffer != b""
