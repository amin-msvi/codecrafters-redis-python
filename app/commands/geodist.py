from app.commands.base import Command, CommandResult
from app.data.db import DataBase
from app.data.geo_helper import GeoOps
from app.types import RESPError


class GeoDistCommand(Command):
    name = "GEODIST"
    arity = (3, 3)
    
    def __init__(self, database: DataBase):
        self._geo_ops = GeoOps(database)
    
    def execute(self, args: list[str]) -> CommandResult:
        key, loc1, loc2 = args
        score_loc1 = self._geo_ops.score(key, loc1)
        score_loc2 = self._geo_ops.score(key, loc2)
        if score_loc1 is None or score_loc2 is None:
            return CommandResult(response=RESPError("Locations not found."))

        lon1, lat1 = self._geo_ops.decode(score_loc1)
        lon2, lat2 = self._geo_ops.decode(score_loc2)
        
        distance = self._geo_ops.distance(lat1, lon1, lat2, lon2)
        return CommandResult(response=str(distance))
