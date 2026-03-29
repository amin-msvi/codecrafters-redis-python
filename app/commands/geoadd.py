from app.commands.base import Command, CommandFlags, CommandResult
from app.data.db import DataBase
from app.data.zset_helper import ZSetOps


class GeoAddCommand(Command):
    name = "GEOADD"
    arity = (4, 4)
    write = CommandFlags(write=True)
    
    def __init__(self, database: DataBase):
        self._zset_ops = ZSetOps(database)
    
    def execute(self, args: list[str]) -> CommandResult:
        key, long, lat, member = args
        return CommandResult(response=1)
