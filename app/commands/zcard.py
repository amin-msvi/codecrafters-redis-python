from app.commands.base import Command, CommandResult
from app.data.db import DataBase
from app.data.zset_helper import ZSetOps


class ZCardCommand(Command):
    name = "ZCARD"
    arity = (1, 1)

    def __init__(self, database: DataBase):
        self._zset_ops = ZSetOps(database)

    def execute(self, args: list[str]) -> CommandResult:
        key = args[0]
        lenght = self._zset_ops.length(key)
        return CommandResult(response=lenght)
