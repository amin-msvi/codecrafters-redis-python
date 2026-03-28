from app.commands.base import Command, CommandResult
from app.data.db import DataBase
from app.data.zset_helper import ZSetOps


class ZRankCommand(Command):
    name = "ZRANK"
    arity = (2, 2)
    
    def __init__(self, database: DataBase):
        self._zset_ops = ZSetOps(database)
    
    def execute(self, args: list[str]) -> CommandResult:
        key, member = args
        rank = self._zset_ops.rank(key, member)
        return CommandResult(response=rank)