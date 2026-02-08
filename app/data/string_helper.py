from datetime import datetime
from app.data.db import DataBase, RedisValue
from app.types import RESPError


class StringOps:
    def __init__(self, database: DataBase):
        self._db = database

    def get(self, key: str) -> RedisValue | RESPError | None:
        redis_val = self._db.get(key)

        if not redis_val:
            return None
        if redis_val.dtype != "string":
            return RESPError(
                "WRONGTYPE Operation against a key holding the wrong kind of value"
            )

        return redis_val

    def set(self, key: str, value: str, expiry: datetime | None):
        redis_val = RedisValue(dtype="string", data=value, expiry=expiry)
        self._db.set(key, redis_val)

    def has_data(self, key: str) -> bool:
        return self._db.exists(key)

    def incr(self, key: str) -> int | RESPError:
        value = self._get_or_create_string(key)
        try:
            value.data = int(value.data) + 1
        except TypeError:
            return RESPError(
                f"key does not contain numerical value: {type(value.data)}"
            )
        return value.data

    # Private methods
    def _get_or_create_string(self, key: str) -> RedisValue:
        value = self._db.get(key)
        if not value:
            value = RedisValue(dtype="string", data=0)
        return value
