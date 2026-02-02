from typing import Any
from app.commands.base import Command
from app.data.db import DataBase
from datetime import datetime, timedelta

from app.data.string_helper import StringOps
from app.types import SimpleString


class SetCommand(Command):
    """
    SET key
    """

    name = "SET"
    arity = (2, float("inf"))

    def __init__(self, database: DataBase):
        self.string_ops = StringOps(database)

    def execute(self, args: list[str]) -> Any:
        key = args[0]
        value = args[1]
        self.string_ops.set(key, value, self._get_expiry(args))
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
