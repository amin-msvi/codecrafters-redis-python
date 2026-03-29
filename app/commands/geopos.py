from app.commands.base import Command, CommandResult
from app.data.db import DataBase
from app.data.zset_helper import ZSetOps
from app.types import NullArray


class GeoPosCommand(Command):
    name = "GEOPOS"
    arity = (2, float("inf"))

    def __init__(self, databse: DataBase):
        self._zset_ops = ZSetOps(databse)

    def execute(self, args: list[str]) -> CommandResult:
        key = args[0]
        members = args[1:]
        locations = []
        for member in members:
            score = self._zset_ops.score(key, member)
            long, lat = "0", "0"  # todo in next step -> decode score to long and lat
            locations.append([long, lat] if score is not None else NullArray())

        return CommandResult(response=locations)
