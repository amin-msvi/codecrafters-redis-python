from math import asin, cos, radians, sin, sqrt
from app.commands.base import Command, CommandResult
from app.data.db import DataBase
from app.data.zset_helper import ZSetOps
from app.types import RESPError

_MIN_LAT = -85.05112878
_MAX_LAT = 85.05112878
_MIN_LONG = -180.0
_MAX_LONG = 180.0

_LAT_RANGE = _MAX_LAT - _MIN_LAT
_LONG_RANGE = _MAX_LONG - _MIN_LONG


def haversine(lat1: float, long1: float, lat2: float, long2: float) -> float:
    R = 6372797.560856 # Earth radius in KM
    
    dLat = radians(lat2 - lat1)
    dLong = radians(long2 - long1)
    lat1 = radians(lat1)
    lat2 = radians(lat2)
    
    a = sin(dLat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dLong / 2) ** 2
    c = 2 * asin(sqrt(a))
    
    return R * c


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


class GeoDistCommand(Command):
    name = "GEODIST"
    arity = (3, 3)
    
    def __init__(self, database: DataBase):
        self._zset_ops = ZSetOps(database)
    
    def execute(self, args: list[str]) -> CommandResult:
        key, loc1, loc2 = args
        score_loc1 = self._zset_ops.score(key, loc1)
        score_loc2 = self._zset_ops.score(key, loc2)
        if score_loc1 is None or score_loc2 is None:
            return CommandResult(response=RESPError("Locations not found."))

        long1, lat1 = _decode_score_to_long_lat(score_loc1)
        long2, lat2 = _decode_score_to_long_lat(score_loc2)
        
        # lat1: float, long1: float, lat2: float, long2: float
        distance = haversine(lat1, long1, lat2, long2)
        return CommandResult(response=str(distance))
