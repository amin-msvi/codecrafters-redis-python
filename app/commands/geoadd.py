from app.commands.base import Command, CommandFlags, CommandResult
from app.data.db import DataBase
from app.data.zset_helper import ZSetOps
from app.types import RESPError


class GeoAddCommand(Command):
    name = "GEOADD"
    arity = (4, 4)
    write = CommandFlags(write=True)
    
    def __init__(self, database: DataBase):
        self._zset_ops = ZSetOps(database)
    
    def execute(self, args: list[str]) -> CommandResult:
        key, long, lat, member = args
        validate = self._validate_geo(float(long), float(lat))
        if validate is not None:
            return CommandResult(validate)

        return CommandResult(response=1)
    
    @staticmethod
    def _validate_geo(long: float, lat: float) -> RESPError | None:
        if not (-180.0 <= long <= 180.0):
            return RESPError(f"invalid longitude,latitude pair {long}, {lat}")
        if not (-85.05112878 <= lat <= 85.05112878):
            return RESPError(f"invalid longtitude, latitude pair {long}, {lat}")
            
        
