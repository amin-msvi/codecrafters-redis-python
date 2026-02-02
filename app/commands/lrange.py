from app.commands.base import Command
from app.data.db import DataBase
from app.data.list_helper import ListOps


class LRangeCommand(Command):
    name = "LRANGE"
    arity = (3, 3)

    def __init__(self, database: DataBase):
        self.list_ops = ListOps(database)

    def execute(self, args: list[str]) -> list:
        key = args[0]
        start = int(args[1])
        stop = int(args[2])
        return self.list_ops.lrange(key, start, stop)
