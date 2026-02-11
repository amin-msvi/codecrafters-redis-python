from dataclasses import field, dataclass, fields
from uuid import UUID, uuid4



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
    master_replid: UUID = field(default_factory=uuid4)
    master_repl_offset: int = field(default_factory=lambda: 0)


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
