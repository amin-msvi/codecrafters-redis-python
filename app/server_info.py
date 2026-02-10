from dataclasses import field, dataclass, fields


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
    role: str


@dataclass
class Clients(InfoSection):
    pass


@dataclass
class Memory(InfoSection):
    pass


@dataclass
class ServerInfo:
    server: Server | None = None
    replication: Replication = field(default_factory=lambda: Replication(role="master"))
    clients: Clients | None = None
    memory: Memory | None = None
