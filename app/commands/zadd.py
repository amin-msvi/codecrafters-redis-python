from app.commands.base import Command, CommandFlags, CommandResult
from app.data.db import DataBase
from app.data.zset_helper import ZSetOps
from app.types import RESPError


class ZAddCommand(Command):
    name = "ZADD"
    arity = (3, 3)
    flags = CommandFlags(write=True)
    
    def __init__(self, database: DataBase):
        self._zset_ops = ZSetOps(database)
    
    def execute(self, args: list[str]) -> CommandResult:
        key, score_str, member = args
        try:
            score = float(score_str)
        except ValueError:
            return CommandResult(response=RESPError("score is not a valid float"))
        
        is_new = self._zset_ops.add(key, score, member)
        return CommandResult(response=1 if is_new else 0)

        