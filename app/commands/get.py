from typing import Any
from app.commands.base import Command
from app.data.db import DataBase
from app.data.string_helper import StringOps
from app.types import RESPError


class GetCommand(Command):
    name = "GET"
    arity = (1, 1)  # Exactly 1 argument

    def __init__(self, database: DataBase):
        self.string_ops = StringOps(database)

    def execute(self, args: list[str]) -> Any:
        val = self.string_ops.get(args[0])
        if val is None:
            return None
        if isinstance(val, RESPError):
            return val

        return val.data
