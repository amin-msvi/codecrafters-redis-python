from app.commands.base import Command, CommandFlags
from app.data.db import DataBase
from app.data.string_helper import StringOps
from app.types import RESPError


class IncrCommand(Command):
    name = "INCR"
    arity = (1, 1)
    flags = CommandFlags(write=True)

    def __init__(self, database: DataBase):
        self._string_obs = StringOps(database)

    def execute(self, args: list[str]) -> int | RESPError:
        key = args[0]
        return self._string_obs.incr(key)
