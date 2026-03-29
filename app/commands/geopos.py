from app.commands.base import Command, CommandResult
from app.data.db import DataBase
from app.data.zset_helper import ZSetOps
from app.types import NullArray

_MIN_LAT = -85.05112878
_MAX_LAT = 85.05112878
_MIN_LONG = -180.0
_MAX_LONG = 180.0

_LAT_RANGE = _MAX_LAT - _MIN_LAT
_LONG_RANGE = _MAX_LONG - _MIN_LONG


def _decode_score_to_long_lat(score: float) -> list[float]:
    """
    TODO: This is my own solution. Check out the codecrafter solution later.
    CodeCrafters Solution: https://github.com/codecrafters-io/redis-geocoding-algorithm

    """
    # Step 1: Separate long and lat
    # Remove '0b' from the beginning of the str
    interleaved_value = bin(int(score))[2:].zfill(52)

    # Skip the other value starting from index 0 to get long binary
    long = interleaved_value[::2]

    # Skip the other value starting from index 1 to get lat binary
    lat = interleaved_value[1::2]

    # Convert string binaries to int
    long, lat = int(long, 2), int(lat, 2)

    # Normalize back to the (valid-min, valid-max) range
    # Also, I'm using (x + 0.5) to return the midpoint of the bucket, not the start
    long = (((long + 0.5) / 2**26) * (_LONG_RANGE)) - (_LONG_RANGE / 2)
    lat = (((lat + 0.5) / 2**26) * (_LAT_RANGE)) - (_LAT_RANGE / 2)

    return [long, lat]


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
            if score is None:
                result = None
            else:
                result = _decode_score_to_long_lat(score)
            locations.append(
                [str(el) for el in result] if result is not None else NullArray()
            )

        return CommandResult(response=locations)
