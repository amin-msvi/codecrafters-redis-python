from random import randint
from typing import Any

from app.data.db import DataBase, RedisValue


class StreamOps:
    def __init__(self, database: DataBase) -> None:
        self._database = database

    def get(self, stream_key: str) -> RedisValue | None:
        return self._database.get(stream_key)

    def set(self, key, id, pairs: dict[str, Any]) -> None:
        redis_val = self._get_or_create(key)
        stream_id = id if id else self._generate_id()
        data = {id: stream_id, **pairs}
        self._database.set(
            key, RedisValue(dtype='stream', data=redis_val.data.update(data))
        )

    # Private methods
    def _generate_id(self) -> str:
        return str(randint(1, 100))
        
    def _get_or_create(self, key) -> RedisValue:
        val = self._database.get(key)
        if not val:
            val = RedisValue(dtype="stream", data={})
            self._database.set(key, val)
            return val
        if val.dtype != "stream":
            raise TypeError(f"WRONGTYPE {key} is not a stream")
        return val
    
