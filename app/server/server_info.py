from dataclasses import field, dataclass, fields
from uuid import uuid4


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
class ACLState:
    whoami: str = field(default_factory=lambda: "default")
    flags: list[str] = field(default_factory=lambda: [])
    