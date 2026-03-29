from app.commands.base import Command, CommandFlags, CommandResult
from app.data.db import DataBase
from app.data.geo_helper import GeoOps


class GeoAddCommand(Command):
    name = "GEOADD"
    arity = (4, 4)
    write = CommandFlags(write=True)

    def __init__(self, database: DataBase):
        self._geo_ops = GeoOps(database)

    def execute(self, args: list[str]) -> CommandResult:
        key, long, lat, member = args
        validate = self._geo_ops.validate(lat=float(lat), long=float(long))
        if validate is not None:
            return CommandResult(validate)

        score = self._geo_ops.encode(lat=float(lat), long=float(long))
        is_new = self._geo_ops.add(key, score, member)
        return CommandResult(response=1 if is_new else 0)
