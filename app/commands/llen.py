from app.commands.base import Command
from app.data.db import DataBase
from app.data.list_helper import ListOps


class LLenCommand(Command):
    name = "LLEN"
    arity = (1, 1)

    def __init__(self, database: DataBase):
        self.list_ops = ListOps(database)

    def execute(self, args: list[str]) -> int:
        key = args[0]
        return self.list_ops.llen(key)
