from typing import Any
from app.commands.base import Command
from app.data.db import DataBase
from app.data.stream.stream_entry import StreamEntry
from app.data.stream_helper import StreamOps


class XRangeCommand(Command):
    name = "XRANGE"
    arity = (3, 3)

    def __init__(self, database: DataBase):
        self.stream_ops = StreamOps(database)

    def execute(self, args: list[str]) -> list[StreamEntry | None]:
        key = args[0]
        start_id = args[1]
        end_id = args[2]
        result = self.stream_ops.xrange(key, start_id, end_id)
        return self._format(result)

    @staticmethod
    def _format(entries: list[StreamEntry]) -> list[Any]:
        return [entry.format() for entry in entries]
