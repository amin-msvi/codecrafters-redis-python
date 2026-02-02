from app.data.db import DataBase, RedisValue


class ListOps:
    def __init__(self, database: DataBase):
        self._database = database

    def lpush(self, key: str, values: list) -> int:
        """Prepend values to list and return new length"""
        redis_val = self._get_or_create(key)
        redis_val.data = values[::-1] + redis_val.data
        return len(redis_val.data)

    def rpush(self, key: str, values: list) -> int:
        """Append values to list and return new length"""
        redis_val = self._get_or_create(key)
        redis_val.data.extend(values)
        return len(redis_val.data)

    def lpop(self, key: str, count: int = 1) -> str | list | None:
        redis_val = self._get_list(key)
        if redis_val is None or not redis_val.data:
            return None
        if count == 1:
            return redis_val.data.pop(0)
        result = redis_val.data[:count]
        del redis_val.data[:count]
        return result

    def lrange(self, key: str, start: int, stop: int) -> list[str]:
        redis_val = self._get_list(key)
        if redis_val is None:
            return []

        # Negative indexes
        data = redis_val.data
        if start < 0:
            start = max(0, start + len(data))
        if stop < 0:
            stop = max(0, stop + len(data))

        return data[start : stop + 1]

    def llen(self, key: str) -> int:
        redis_val = self._get_list(key)
        return len(redis_val.data) if redis_val is not None else 0

    def has_data(self, key: str) -> bool:
        redis_val = self._get_list(key)
        return redis_val is not None and len(redis_val.data) > 0

    # Private methods
    def _get_or_create(self, key):
        val = self._database.get(key)
        if val is None:
            val = RedisValue(dtype="list", data=[])
            self._database.set(key, val)
            return val
        if val.dtype != "list":
            raise TypeError(f"WRONGTYPE {key} is not a list")
        return val

    def _get_list(self, key: str) -> RedisValue | None:
        val = self._database.get(key)
        if val is None:
            return None
        if val.dtype != "list":
            raise TypeError(f"WRONGTYPE {key} is not a list")
        return val
