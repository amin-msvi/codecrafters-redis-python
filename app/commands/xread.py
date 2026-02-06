from typing_extensions import Any
from app.commands.base import Command
from app.data.db import DataBase
from app.data.stream.stream_entry import StreamEntry
from app.data.stream_helper import StreamOps


class XReadCommand(Command):
    name = "XREAD"
    arity = (3, float('inf'))
    
    def __init__(self, database: DataBase):
        self.stream_ops = StreamOps(database)
    
    def execute(self, args: list[str]) -> Any:
        # type_ = args[0]
        key = args[1]
        id = args[2]
        entries = self.stream_ops.xread(key, id)
        if not entries:
            return []
        return self._format(key, entries)

    @staticmethod
    def _format(key, entries: list[StreamEntry]) -> list[Any]:
        return [[key, [entry.format()]] for entry in entries]
