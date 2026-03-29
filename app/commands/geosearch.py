from app.commands.base import Command, CommandResult
from app.data.db import DataBase
from app.data.geo_helper import GeoOps


class GeoSearchCommand(Command):
    name = "GEOSEARCH"
    arity = (7, 7)
    
    def __init__(self, database: DataBase):
        self._geo_ops = GeoOps(database)
    
    def execute(self, args: list[str]) -> CommandResult:
        # places FROMLONLAT 2 48 BYRADIUS 100 m
        key, search_type, lon, lat, by, distance, unit = args
        members = self._geo_ops.search(key, search_type, float(lon), float(lat), by, float(distance), unit)
        return CommandResult(response=members)