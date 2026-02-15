from app.commands.base import Command, CommandResult
from app.server.server_info import ServerInfo


class InfoCommand(Command):
    name = "INFO"
    arity = (1, float("inf"))

    def __init__(self, server_info: ServerInfo):
        self._server_info = server_info

    def execute(self, args: list[str]) -> CommandResult:
        if args[0] == "replication":
            return CommandResult(response=self._server_info.replication.format())
        return CommandResult(response=None)
