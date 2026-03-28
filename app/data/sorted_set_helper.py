from app.data.db import DataBase, RedisValue
from app.data.sorted_set.sset import SortedSet


class SortedSetOps:
    def __init__(self, db: DataBase) -> None:
        self._db = db
    
    def add(self, key: str, score: float, value: str):
        redis_val = self._get_or_create(key)
        sset_entry = (score, value)
        redis_val.data.add(sset_entry)
    
    def _get_or_create(self, key: str):
        val = self._db.get(key)
        if val is None:
            val = RedisValue(dtype="sset", data=SortedSet())
            self._db.set(key, val)
            return val
        
        if val.dtype != "sset":
            raise TypeError(f"WRONGTYPE {key} is not a sorted set")
        
        return val
            
    
    def length(self, key) -> int | None:
        val = self._get_set(key)
        return len(val.data) if val else None
    
    def _get_set(self, key: str) -> RedisValue | None:
        redis_val = self._db.get(key)
        return redis_val if redis_val else None