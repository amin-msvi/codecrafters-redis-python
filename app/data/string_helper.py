from datetime import datetime
from app.data.db import DataBase, RedisValue
from app.types import RESPError


class StringOps:
    def __init__(self, database: DataBase):
        self._database = database

    def get(self, key: str):
        redis_val = self._database.get(key)

        if not redis_val:
            return None
        if redis_val.dtype != "string":
            return RESPError(
                "WRONGTYPE Operation against a key holding the wrong kind of value"
            )

        return redis_val.data

    def set(self, key: str, value: str, expiry: datetime | None):
        redis_val = RedisValue(dtype="string", data=value, expiry=expiry)
        self._database.set(key, redis_val)

    def has_data(self, key: str) -> bool:
        return self._database.exists(key)
