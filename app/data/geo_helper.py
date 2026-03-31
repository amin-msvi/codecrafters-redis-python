from math import asin, cos, radians, sin, sqrt
from app.data.db import DataBase
from app.data.zset_helper import ZSetOps
from app.types import NullArray, RESPError

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

    4bit example:
        v = 0b1011
        v ->              1     0     1     1
        v_spreaded -> (0, 1, 0, 0, 0, 1, 0, 1)
    """
    # Ensure only lower 32 bits are non-zero.
    v = v & 0xFFFFFFFF  # bin: 0b11111111111111111111111111111111

    # Bitwise operations to spread 32 bits into 64 bits with zeroes in-between
    # 0x0000FFFF0000FFFF  => bin: 0000000000000000111111111111111100000000000000001111111111111111
    v = (v | (v << 16)) & 0x0000FFFF0000FFFF

    # 0x00FF00FF00FF00FF  => bin: 0000000011111111000000001111111100000000111111110000000011111111
    v = (v | (v << 8)) & 0x00FF00FF00FF00FF

    # 0x0F0F0F0F0F0F0F0F  => bin: 0000111100001111000011110000111100001111000011110000111100001111
    v = (v | (v << 4)) & 0x0F0F0F0F0F0F0F0F

    # 0x3333333333333333  => bin: 0011001100110011001100110011001100110011001100110011001100110011
    v = (v | (v << 2)) & 0x3333333333333333

    # 0x5555555555555555  => bin: 0101010101010101010101010101010101010101010101010101010101010101
    v = (v | (v << 1)) & 0x5555555555555555

    return v


def _interleave(x: int, y: int) -> int:
    """Bit interleaving approach is also called 'Morton Code' or 'Z-order Curve'"""
    # First, the values are spread from 32-bit to 64-bit integers.
    # This is done by inserting 32 zero bits in-between.
    #
    # Before spread: x1  x2  ...  x31  x32
    # After spread:  0   x1  ...   0   x16  ... 0  x31  0  x32
    x = _spread_int32_to_int64(x)
    y = _spread_int32_to_int64(y)

    # The y value is then shifted 1 bit to the left. (To land y bits in the odd positions)
    # Before shift: 0   y1   0   y2 ... 0   y31   0   y32
    # After shift:  y1   0   y2 ... 0   y31   0   y32   0
    y_shifted = y << 1

    # Next, x and y_shifted are combined using a bitwise OR.
    #
    # Before bitwise OR (x): 0   x1   0   x2   ...  0   x31    0   x32
    # Before bitwise OR (y): y1  0    y2  0    ...  y31  0    y32   0
    # After bitwise OR     : y1  x2   y2  x2   ...  y31  x31  y32
    return x | y_shifted


def _haversine(lat1: float, long1: float, lat2: float, long2: float) -> float:
    R = 6372797.560856  # Earth radius in KM

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


class GeoOps:
    def __init__(self, database: DataBase):
        self._zset_ops = ZSetOps(database)

    def validate(self, lat: float, long: float) -> RESPError | None:
        if not (_MIN_LAT <= lat <= _MAX_LAT):
            return RESPError(f"-ERR invalid longtitude, latitude pair {long}, {lat}")
        if not (_MIN_LONG <= long <= _MAX_LONG):
            return RESPError(f"-ERR invalid longitude,latitude pair {long}, {lat}")

    def encode(self, long: float, lat: float) -> float:
        """
        3 Steps to convert long and lat to a zset score:
            1. normalize each long and lat to [0, 2**26] range.
            2. truncate the normalized values to integer.
            3. interleave the integers to get a 52bits (26 + 26) integer.

        - 2 Cool points:
            1. Why not just concatenating the lat and longs?!
                It can be reversible and technically it's possible. However, interleaving approach
                gives a usefull property:
                    Nearby scores corresponds to nearby points in 2D space -> in range
                    query: Spacially coherent regions! cool cool!
            2. Don't we lose information when we truncate values to int?!
                The value is recovered in one quantization step:
                    (_LAT_RANGE / 2^26) ≈ (170.1 / 67 million) ≈ 0.0000025°
                it's about 28 cm! So mathematically, it's not exact. but for geo applications? enough!

        """
        # Step 1:
        normalized_lat = 2**26 * (lat - _MIN_LAT) / _LAT_RANGE
        normalized_long = 2**26 * (long - _MIN_LONG) / _LONG_RANGE

        # Step 2:
        lat_truncated = int(normalized_lat)
        long_truncated = int(normalized_long)

        # Step 3:
        return _interleave(x=lat_truncated, y=long_truncated)

    def distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        return _haversine(lat1, lon1, lat2, lon2)

    def decode(self, score: float) -> list[float]:
        return _decode_score_to_long_lat(score)

    def positions(self, key: str, members: list[str]) -> list[float | NullArray]:
        locations = []
        for member in members:
            score = self._zset_ops.score(key, member)
            if score is None:
                result = None
            else:
                result = self.decode(score)
            locations.append(
                [str(el) for el in result] if result is not None else NullArray()
            )
        return locations

    def search(
        self,
        key: str,
        search_type: str,
        lon: float,
        lat: float,
        by: str,
        distance: float,
        unit: str,
    ) -> list[str]:
        # In CodeCrafters we only work with FROMLONLAT and BYRADIUS.
        if by != "BYRADIUS" or search_type != "FROMLONLAT":
            return []

        within_distance = []
        if unit == "km":
            distance *= 1000
        members = self._zset_ops.range(key, 0, -1)
        for member in members:
            score = self._zset_ops.score(key, member)
            if score is None:
                continue
            mem_lon, mem_lat = self.decode(score)
            if self.distance(lat, lon, mem_lat, mem_lon) < distance:
                within_distance.append(member)
        return within_distance
