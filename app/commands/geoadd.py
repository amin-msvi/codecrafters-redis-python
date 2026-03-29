from app.commands.base import Command, CommandFlags, CommandResult
from app.data.db import DataBase
from app.data.zset_helper import ZSetOps
from app.types import RESPError

_MIN_LAT = -85.05112878
_MAX_LAT = 85.05112878
_MIN_LONG = -180.0
_MAX_LONG = 180.0

_LAT_RANGE = _MAX_LAT - _MIN_LAT
_LONG_RANGE = _MAX_LONG - _MIN_LONG

def _spread_int32_to_int64(v: int) -> int:
    """
    Spreads a 32-bit integer to a 64-bit integer by inserting
    32 zero bits in-between.
    
    Before spread: x1  x2  ...  x31  x32
    After spread:  0   x1  ...   0   x16  ... 0  x31  0  x32
    """
    # Ensure only lower 32 bits are non-zero.
    v = v & 0xFFFFFFFF
    
    # Bitwise operations to spread 32 bits into 64 bits with zeroes in-between
    v = (v | (v << 16)) & 0x0000FFFF0000FFFF
    v = (v | (v << 8))  & 0x00FF00FF00FF00FF
    v = (v | (v << 4))  & 0x0F0F0F0F0F0F0F0F
    v = (v | (v << 2))  & 0x3333333333333333
    v = (v | (v << 1))  & 0x5555555555555555

    return v

def _interleave(x: int, y: int) -> int:
    # First, the values are spread from 32-bit to 64-bit integers.
    # This is done by inserting 32 zero bits in-between.
    #
    # Before spread: x1  x2  ...  x31  x32
    # After spread:  0   x1  ...   0   x16  ... 0  x31  0  x32
    x = _spread_int32_to_int64(x)
    y = _spread_int32_to_int64(y)
    
    # The y value is then shifted 1 bit to the left.
    # Before shift: 0   y1   0   y2 ... 0   y31   0   y32
    # After shift:  y1   0   y2 ... 0   y31   0   y32   0
    y_shifted = y << 1

    # Next, x and y_shifted are combined using a bitwise OR.
    #
    # Before bitwise OR (x): 0   x1   0   x2   ...  0   x31    0   x32
    # Before bitwise OR (y): y1  0    y2  0    ...  y31  0    y32   0
    # After bitwise OR     : y1  x2   y2  x2   ...  y31  x31  y32
    return x | y_shifted



class GeoAddCommand(Command):
    name = "GEOADD"
    arity = (4, 4)
    write = CommandFlags(write=True)

    def __init__(self, database: DataBase):
        self._zset_ops = ZSetOps(database)

    def execute(self, args: list[str]) -> CommandResult:
        key, long, lat, member = args
        validate = self._validate_geo(lat=float(lat), long=float(long))
        if validate is not None:
            return CommandResult(validate)

        score = self._calc_score(lat=float(lat), long=float(long))
        is_new = self._zset_ops.add(key, score, member)
        return CommandResult(response=1 if is_new else 0)

    def _calc_score(self, lat: float, long: float) -> int:
        """
        3 Steps to convert long and lat to a zset score:
            1. normalize each long and lat to [0, 2**26] range.
            2. truncate the normalized values to integer.
            3. interleave the integers to get a 52bits (26 + 26) integer.
        """
        # Step 1:
        normalized_lat = 2**26 * (lat - _MIN_LAT) / _LAT_RANGE
        normalized_long = 2**26 * (long - _MIN_LONG) / _LONG_RANGE
        
        # Step 2:
        lat_truncated = int(normalized_lat)
        long_truncated = int(normalized_long)
        
        # Step 3:
        return _interleave(x=lat_truncated, y=long_truncated)

    @staticmethod
    def _validate_geo(lat: float, long: float) -> RESPError | None:
        if not (_MIN_LAT <= lat <= _MAX_LAT):
            return RESPError(f"invalid longtitude, latitude pair {long}, {lat}")
        if not (_MIN_LONG <= long <= _MAX_LONG):
            return RESPError(f"invalid longitude,latitude pair {long}, {lat}")


        
    
    
