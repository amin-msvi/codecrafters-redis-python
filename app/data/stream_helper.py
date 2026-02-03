from random import randint
from typing import Any

from app.data.db import DataBase, RedisValue
from app.types import RESPError


class StreamOps:
    def __init__(self, database: DataBase) -> None:
        self._database = database

    def get(self, key: str) -> RedisValue | None:
        return self._database.get(key)

    def set(self, key: str, new_id: str, pairs: dict[str, Any]) -> RESPError | str:
        redis_val = self._get_or_create(key)
        # id = id if id != "*" else self._generate_id()
        if err := self._validate(key, new_id):
            return err
        new_id = self._get_id(key, new_id)
        data = {"id": new_id, **pairs}
        redis_val.data.append(data)
        self._database.set(key, RedisValue(dtype="stream", data=redis_val.data))
        return new_id

    # Private methods
    def _validate(self, key: str, new_id: str) -> RESPError | None:
        new_id_mill_sec, new_id_seq_num = self._split_id(new_id)
        if not new_id_mill_sec or not new_id_seq_num:
            return None

        if new_id == "0-0":
            return RESPError("The ID specified in XADD must be greater than 0-0")

        if top := self._get_top(key):
            mill_sec, seq_num = map(int, top["id"].split("-"))
            if mill_sec > int(new_id_mill_sec):
                return RESPError(
                    "The ID specified in XADD is equal or smaller than the target stream top item"
                )
            elif mill_sec == int(new_id_mill_sec):
                if int(new_id_seq_num) <= seq_num:
                    return RESPError(
                        "The ID specified in XADD is equal or smaller than the target stream top item"
                    )

    def _get_id(self, key: str, id: str) -> str:
        if id == "0-*":
            return "0-1"

        new_mill_sec, new_seq_num = self._split_id(id)

        top = self._get_top(key)
        top_mill_sec, top_seq_num = self._split_id(top["id"]) if top else (None, None)

        if not top_seq_num and not new_seq_num:
            new_seq_num = "0"
        elif top_seq_num and not new_seq_num:
            if top_mill_sec == new_mill_sec:
                new_seq_num = str(int(top_seq_num) + 1)
            elif top_mill_sec != new_mill_sec:
                new_seq_num = "0"
        elif top_seq_num and new_seq_num:
            pass
        elif not top_seq_num and new_seq_num:
            pass

        return new_mill_sec + "-" + new_seq_num

    @staticmethod
    def _split_id(id: str) -> tuple[str | None, str | None]:
        mill_sec, seq_num = id.split("-")
        if mill_sec == "*":
            mill_sec = None
        if seq_num == "*":
            seq_num = None
        return mill_sec, seq_num
        
            
    def _get_top(self, key: str) -> dict | None:
        redis_val = self.get(key)
        if redis_val and redis_val.data:
            return redis_val.data[-1]
        return None

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
