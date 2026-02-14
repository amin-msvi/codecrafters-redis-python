from typing_extensions import Any
from app.commands.base import Command
from app.server import ServerInfo


class InfoCommand(Command):
    name = "INFO"
    arity = (1, float("inf"))

    def __init__(self, server_info: ServerInfo):
        self._server_info = server_info

    def execute(self, args: list[str]) -> Any:
        if args[0] == "replication":
            return self._server_info.replication.format()
