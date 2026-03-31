from dataclasses import field, dataclass, fields
from hashlib import sha256
from uuid import uuid4

from app.types import RESPError, SimpleString


@dataclass
class InfoSection:
    def format(self):
        formatted = f"# {self.__class__.__name__}\n"
        for f in fields(self):
            value = getattr(self, f.name)
            formatted += f"{f.name}:{value}\n"
        return formatted


@dataclass
class Server(InfoSection):
    pass


@dataclass
class Replication(InfoSection):
    role: str = field(default_factory=lambda: "master")
    connected_slaves: int = 0
    master_replid: str = field(default_factory=lambda: uuid4().hex)
    master_repl_offset: int = field(default_factory=lambda: 0)

    def incr_offset(self, count: int):
        self.master_repl_offset += count

    def incr_slaves(self):
        self.connected_slaves += 1


@dataclass
class Clients(InfoSection):
    pass


@dataclass
class Memory(InfoSection):
    pass


@dataclass
class ServerInfo:
    server: Server | None = None
    replication: Replication = field(default_factory=Replication)
    clients: Clients | None = None
    memory: Memory | None = None


@dataclass
class MasterInfo:
    host: str | None
    port: int | None

    @classmethod
    def from_string(cls, string: str) -> MasterInfo:
        info = string.split(" ")
        if len(info) != 2:
            raise ValueError("server info must be '<host> <port>'")
        host, port = info[0], int(info[1])
        return cls(host=host, port=port)


@dataclass
class ACLUser:
    flags: list[str] = field(default_factory=lambda: ["nopass"])
    passwords: list[str] = field(default_factory=lambda: [])

    def add_flags(self, flag: str):
        if flag in self.flags:
            return
        self.flags.append(flag)

    def get_states(self):
        result = []
        for f in fields(self):
            result.append(f.name)
            result.append(getattr(self, f.name))
        return result

    def set_user(self, password: str) -> SimpleString:
        if password[0] == ">":
            self.passwords.append(sha256(password[1:].encode()).hexdigest())
        self.flags.remove("nopass")
        return SimpleString("OK")

    def auth(self, password: str) -> bool:
        hashed_pass = sha256(password.encode()).hexdigest()
        if hashed_pass in self.passwords:
            return True
        return False


@dataclass
class User:
    username: str = field(default_factory=lambda: "default")
    info: ACLUser = field(default_factory=ACLUser)

    def auth(self, username: str, password: str) -> RESPError | SimpleString:
        if self.info.auth(password):
            return SimpleString("OK")
        return RESPError(
            "-WRONGPASS invalid username-password pair or user is disabled."
        )
