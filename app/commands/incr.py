from typing_extensions import Any
from app.commands.base import Command
from app.data.db import DataBase
from app.data.string_helper import StringOps


class IncrCommand(Command):
    name = "INCR"
    arity = (1, 1)

    def __init__(self, database: DataBase):
        self._string_obs = StringOps(database)

    def execute(self, args: list[str]) -> Any:
        key = args[0]
        return self._string_obs.incr(key)
