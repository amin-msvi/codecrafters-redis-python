from app.commands.base import Command, CommandResult
from app.data.db import DataBase
from app.data.zset_helper import ZSetOps


class ZRangeCommand(Command):
    name = "ZRANGE"
    arity = (3, 3)

    def __init__(self, database: DataBase):
        self._zset_ops = ZSetOps(database)

    def execute(self, args: list[str]) -> CommandResult:
        key, start_str, end_str = args
        range = self._zset_ops.range(key, int(start_str), int(end_str))
        return CommandResult(response=range)
