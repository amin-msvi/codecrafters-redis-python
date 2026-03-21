from app.commands.base import (
    BlockingResponse,
    Command,
    CommandResult,
    RDBSync,
    WaitBlocker,
)
from app.config import ServerConfig


class ConfigCommand(Command):
    name = "CONFIG"
    arity = (2, float("inf"))

    def __init__(self, server_config: ServerConfig):
        self._server_info = server_config

    def execute(
        self, args: list[str]
    ) -> (
        CommandResult | BlockingResponse | RDBSync | WaitBlocker
    ):  # pyright: ignore[reportReturnType] -> I'll fix it in upcoming lessons
        operation_type = args[0]
        arguments = args[1:]
        if operation_type.upper() == "GET":
            if arguments[0].lower() == "dir":
                return CommandResult(response=["dir", self._server_info.dir])
            if arguments[0].lower() == "dbfilename":
                return CommandResult(
                    response=["dbfilename", self._server_info.dbfilename]
                )
