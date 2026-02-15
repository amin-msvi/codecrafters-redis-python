from app.commands.base import Command, CommandResult
from app.server.server_info import ServerInfo
from app.types import SimpleString
from app.utils.command_utils import parse_args


class ReplConfCommand(Command):
    name = "REPLCONF"
    arity = (2, 2)

    def __init__(self, server_info: ServerInfo):
        self._server_info = server_info

    def execute(self, args: list[str]) -> CommandResult:
        parsed_args = parse_args(args)
        if listening_port := parsed_args.get("listening-port"):  # noqa
            return CommandResult(response=SimpleString("OK"))
        if capa := parsed_args.get("capa"):  # noqa
            return CommandResult(response=SimpleString("OK"))
        return CommandResult(response=None)
