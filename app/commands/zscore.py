from app.commands.base import Command, CommandResult
from app.data.db import DataBase
from app.data.zset_helper import ZSetOps


class ZScoreCommand(Command):
    name = "ZSCORE"
    arity = (2, 2)

    def __init__(self, database: DataBase):
        self._zset_ops = ZSetOps(database)

    def execute(self, args: list[str]) -> CommandResult:
        key, member = args
        score = self._zset_ops.score(key, member)
        return CommandResult(response=str(score))
