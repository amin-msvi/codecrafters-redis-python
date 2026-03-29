from app.commands.base import Command, CommandResult
from app.data.db import DataBase
from app.data.geo_helper import GeoOps


class GeoPosCommand(Command):
    name = "GEOPOS"
    arity = (2, float("inf"))

    def __init__(self, database: DataBase):
        self._geo_ops = GeoOps(database)

    def execute(self, args: list[str]) -> CommandResult:
        key = args[0]
        members = args[1:]
        locations = self._geo_ops.positions(key, members)

        return CommandResult(response=locations)
