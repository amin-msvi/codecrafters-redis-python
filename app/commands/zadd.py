from app.commands.base import Command, CommandFlags, CommandResult
from app.data.db import DataBase
from app.data.sorted_set_helper import SortedSetOps


class ZAddCommand(Command):
    name = "ZADD"
    arity = (3, 3)
    flags = CommandFlags(write=True)
    
    def __init__(self, database: DataBase):
        self._sorted_set_ops = SortedSetOps(database)
    
    def execute(self, args: list[str]) -> CommandResult:
        key, score, member = args
        self._sorted_set_ops.add(key, float(score), member)
        count = self._sorted_set_ops.length(key)
        return CommandResult(response=count)
