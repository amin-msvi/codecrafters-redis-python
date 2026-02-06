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
        keys, ids = self._pairs(args[1:])

        final = []
        for key, id in zip(keys, ids):
            entry = self.stream_ops.xread(key, id)
            if entry:
                final.append(self._format(key, entry))
        return final

    @staticmethod
    def _format(key, entries: list[StreamEntry]) -> list[Any]:
        return [key] + [[entry.format() for entry in entries]]
    
    @staticmethod
    def _pairs(args: list[str]) -> tuple[list[str], list[str]]:
        mid = len(args) // 2
        return args[:mid], args[mid:]
