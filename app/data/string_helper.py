from datetime import datetime
from app.data.key_space import KeySpace, RedisValue
from app.types import RESPError


class StringOps:
    def __init__(self, keyspace: KeySpace):
        self._keyspace = keyspace

    def get(self, key: str):
        redis_val = self._keyspace.get(key)

        if not redis_val:
            return None
        if redis_val.dtype != "string":
            return RESPError(
                "WRONGTYPE Operation against a key holding the wrong kind of value"
            )

        return redis_val.data

    def set(self, key: str, value: str, expiry: datetime | None):
        redis_val = RedisValue(dtype="string", data=value, expiry=expiry)
        self._keyspace.set(key, redis_val)

    def has_data(self, key: str) -> bool:
        return self._keyspace.exists(key)
