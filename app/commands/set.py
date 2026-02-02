from typing import Any
from app.commands.base import Command
from app.data.db import DataBase
from datetime import datetime, timedelta

from app.data.string_helper import StringOps
from app.types import SimpleString
from app.utils.command_utils import parse_args


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
        self.string_ops.set(key, value, self._get_expiry(args[2:]))
        return SimpleString("OK")

    def _get_expiry(self, pairs: list) -> datetime | None:
        pair_map = parse_args(pairs)
        if sec := pair_map.get("EX"):
            return datetime.now() + timedelta(seconds=float(sec))
        if mill_sec := pair_map.get("PX"):
            return datetime.now() + timedelta(milliseconds=float(mill_sec))
        return None
