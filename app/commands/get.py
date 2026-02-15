from app.commands.base import Command, CommandResult
from app.data.db import DataBase
from app.data.string_helper import StringOps
from app.types import RESPError


class GetCommand(Command):
    name = "GET"
    arity = (1, 1)  # Exactly 1 argument

    def __init__(self, database: DataBase):
        self.string_ops = StringOps(database)

    def execute(self, args: list[str]) -> CommandResult:
        val = self.string_ops.get(args[0])
        if val is None:
            return CommandResult(response=None)
        if isinstance(val, RESPError):
            return CommandResult(response=val)
        return CommandResult(response=val.data)
