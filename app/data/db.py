from dataclasses import dataclass
from typing import Any
from datetime import datetime


@dataclass
class RedisValue:
    dtype: str
    data: Any
    expiry: datetime | None = None


class DataBase:
    def __init__(self, store: dict[str, RedisValue] | None = None):
        if store is None:
            self.store = {}
        else:
            self.store = store

    def get(self, key: str) -> RedisValue | None:
        val = self.store.get(key)
        if val and val.expiry and val.expiry < datetime.now():
            self.delete(key)
            return None
        return val

    def get_keys(self, key_pattern: str) -> list[str] | None:
        if key_pattern == "*":
            keys = []
            for key in list(self.store.keys()):
                if self.get(key) is not None:
                    keys.append(key)
            return keys

        # I'll assume "*" is always at the end for simplicity, for now
        if "*" in key_pattern:
            keys = []
            for key in list(self.store.keys()):
                if self.get(key) is not None:
                    if key.startswith(key_pattern[:-1]):
                        keys.append(key)
            return keys

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
