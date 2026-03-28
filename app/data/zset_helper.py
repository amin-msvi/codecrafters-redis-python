from app.data.db import DataBase, RedisValue
from app.data.zset.zset import ZSet


class ZSetOps:
    def __init__(self, db: DataBase) -> None:
        self._db = db
    
    def add(self, key: str, score: float, member: str) -> bool:
        """Returns True if member was newly added"""
        zset = self._get_or_create(key)
        return zset.add(member, score)
    
    def rank(self, key: str, member: str) -> int | None:
        zset = self._get_zset(key)
        if not zset:
            return None
        return zset.rank(member)
    # Private Methods
    def _get_or_create(self, key: str) -> ZSet:
        val = self._db.get(key)
        if val is None:
            val = RedisValue(dtype="zset", data=ZSet())
            self._db.set(key, val)
            return val.data

        if val.dtype != "zset":
            raise TypeError(f"WRONGTYPE {key} is not a sorted set")
        return val.data

    def _get_zset(self, key: str) -> ZSet | None:
        redis_val = self._db.get(key)
        return redis_val.data if redis_val and redis_val.dtype == "zset" else None
