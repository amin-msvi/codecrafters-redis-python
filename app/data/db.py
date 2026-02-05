from dataclasses import dataclass
from typing import Any
from datetime import datetime


@dataclass
class RedisValue:
    dtype: str
    data: Any
    expiry: datetime | None = None


class DataBase:
    def __init__(self):
        self.store: dict[str, RedisValue] = {}

    def get(self, key: str) -> RedisValue | None:
        val = self.store.get(key)
        if val and val.expiry and val.expiry < datetime.now():
            self.delete(key)
            return None
        return val

    def set(self, key: str, value: RedisValue) -> None:
        self.store[key] = value

    def exists(self, key: str) -> bool:
        return self.get(key) is not None

    def delete(self, key: str) -> bool:
        if key in self.store:
            del self.store[key]
            return True
        return False

    def get_type(self, key: str) -> str | None:
        val = self.get(key)
        return val.dtype if val else None
