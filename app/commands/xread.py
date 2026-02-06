from typing import Any

from app.commands.base import Command
from app.data.db import DataBase
from app.data.stream.stream_entry import StreamEntry
from app.data.stream_helper import StreamOps
from app.types import RESPError


class XReadCommand(Command):
    """
    XREAD command - Read data from streams.

    Syntax: XREAD STREAMS key1 [key2 ...] id1 [id2 ...]
    """

    name = "XREAD"
    arity = (3, float("inf"))

    def __init__(self, database: DataBase):
        self.stream_ops = StreamOps(database)

    def execute(self, args: list[str]) -> list[list[Any]] | RESPError | None:
        """
        Execute XREAD command.

        Args:
            args: [STREAMS, key1, ..., keyN, id1, ..., idN]

        Returns:
            List of [key, entries] pairs for streams with data,
            None if no data available,
            RESPError if arguments are invalid
        """

        if args[0].upper() != "STREAMS":
            return RESPError("ERR syntax error")

        result = self._parse_streams_args(args[1:])
        if isinstance(result, RESPError):
            return result
        keys, ids = result

        responses = []
        for key, stream_id in zip(keys, ids):
            entries = self.stream_ops.xread(key, stream_id)
            if entries:
                responses.append(self._format_stream(key, entries))

        return responses if responses else None

    @staticmethod
    def _format_stream(key: str, entries: list[StreamEntry]) -> list[Any]:
        """Format a single stream's response as [key, [entries]]."""
        return [key, [entry.format() for entry in entries]]

    @staticmethod
    def _parse_streams_args(args: list[str]) -> tuple[list[str], list[str]] | RESPError:
        if len(args) % 2 != 0:
            return RESPError(
                "ERR unbalanced XREAD list of streams."
            )
        mid = len(args) // 2
        return args[:mid], args[mid:]
