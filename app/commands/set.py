from typing import Any
from app.commands.base import Command
from app.data.data_store import DataStore, DataValue
from datetime import datetime, timedelta

from app.types import SimpleString


class SetCommand(Command):
    """
    SET key
    """

    name = "SET"
    arity = (2, float("inf"))

    def __init__(self, store: DataStore):
        self.store = store

    def execute(self, args: list[str]) -> Any:
        data_value = DataValue(value=args[1], expiry_date=self._get_expiry(args))
        self.store.set(key=args[0], value=data_value)
        return SimpleString("OK")

    def _get_expiry(self, args: list) -> datetime | None:
        for arg_idx in range(len(args)):
            if isinstance(args[arg_idx], str):
                if args[arg_idx].upper() == "PX":
                    mill_sec = (
                        float(args[arg_idx + 1]) if arg_idx + 1 < len(args) else None
                    )
                    if mill_sec:
                        return datetime.now() + timedelta(milliseconds=mill_sec)
                if args[arg_idx].upper() == "EX":
                    sec = float(args[arg_idx + 1]) if arg_idx + 1 < len(args) else None
                    if sec:
                        return datetime.now() + timedelta(seconds=sec)
        return None
