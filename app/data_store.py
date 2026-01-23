# class DataStoreKeyError(Exception):
#     def __init__(self, key, value=None):
#         self.key = key

#         message = f"key {key} not found."

#         super().__init__(message)


from typing import Any
from pydantic import BaseModel
from datetime import datetime, timedelta


class DataValue(BaseModel):
    value: Any
    expiry_ms: datetime | None = None


class DataStore:
    def __init__(self):
        self.data: dict[Any, DataValue] = {}

    def set(self, key: Any, value: DataValue, expiry_ms: float | None = None) -> None:
        self.data.update(
            {
                key: DataValue(
                    value=value,
                    expiry_ms=(
                        datetime.now() + timedelta(milliseconds=expiry_ms)
                        if expiry_ms
                        else None
                    ),
                ),
            }
        )

    def get(self, key: Any) -> Any:
        data_value: DataValue | None = self.data.get(key)
        if not data_value:
            return None
        if data_value.expiry_ms:
            if data_value.expiry_ms < datetime.now():
                del self.data[key]
                return None
        return data_value.value
