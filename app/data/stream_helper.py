from datetime import timedelta
from random import randint
from typing import Any

from app.data.db import DataBase, RedisValue
from app.types import RESPError


class StreamOps:
    def __init__(self, database: DataBase) -> None:
        self._database = database

    def get(self, key: str) -> RedisValue | None:
        return self._database.get(key)

    def set(self, key: str, id: str, pairs: dict[str, Any]) -> RESPError | None:
        redis_val = self._get_or_create(key)
        # id = id if id != "*" else self._generate_id()
        if err := self._validate(key, id):
            return err
        data = {"id": id, **pairs}
        redis_val.data.append(data)
        self._database.set(key, RedisValue(dtype="stream", data=redis_val.data))

    # Private methods
    def _validate(self, key: str, new_id: str) -> RESPError | None:
        new_id_mill_sec, new_id_seq_num = map(int, new_id.split("-"))

        # Check if ID is 0-0 (always invalid)
        if new_id == "0-0":
            return RESPError("The ID specified in XADD must be greater than 0-0")

        stream = self.get(key)
        if stream and stream.data:
            last: dict = stream.data[-1]
            mill_sec, seq_num = map(int, last["id"].split("-"))

            if mill_sec > new_id_mill_sec:
                return RESPError(
                    "The ID specified in XADD is equal or smaller than the target stream top item"
                )
            elif mill_sec == new_id_mill_sec:
                if new_id_seq_num <= seq_num:
                    return RESPError(
                        "The ID specified in XADD is equal or smaller than the target stream top item"
                    )

    def _generate_id(self) -> str:
        return str(randint(1, 100))

    def _get_or_create(self, key) -> RedisValue:
        val = self._database.get(key)
        if not val:
            val = RedisValue(dtype="stream", data=[])
            self._database.set(key, val)
            return val
        if val.dtype != "stream":
            raise TypeError(f"WRONGTYPE {key} is not a stream")
        return val
