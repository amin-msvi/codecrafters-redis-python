from app.commands.base import Command, CommandFlags, CommandResult
from app.data.db import DataBase
from app.data.string_helper import StringOps


class IncrCommand(Command):
    name = "INCR"
    arity = (1, 1)
    flags = CommandFlags(write=True)

    def __init__(self, database: DataBase):
        self._string_obs = StringOps(database)

    def execute(self, args: list[str]) -> CommandResult:
        key = args[0]
        response = self._string_obs.incr(key)
        return CommandResult(response=response)
