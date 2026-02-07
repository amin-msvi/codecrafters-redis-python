from typing import Any

from app.commands.base import BlockingResponse, Command
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

    def execute(
        self, args: list[str]
    ) -> list[list[Any]] | RESPError | None | BlockingResponse:
        """
        Execute XREAD command.

        Args:
            args: [BLOCK, timeout, STREAMS, key1, ..., keyN, id1, ..., idN]

        Returns:
            List of [key, entries] pairs for streams with data,
            None if no data available,
            RESPError if arguments are invalid
        """

        # Parsing arguments
        parsed_args = self._parse_streams_args(args)
        if isinstance(parsed_args, RESPError):
            return parsed_args
        keys, ids, expiry = parsed_args

        # Read immediately
        responses = []
        for i, (key, stream_id) in enumerate(zip(keys, ids)):
            if ids[i] == "$":
                ids[i] = str(self.stream_ops.top_id(key))
                stream_id = ids[i]
            entries = self.stream_ops.xread(key, stream_id)
            if entries:
                responses.append(self._format_stream(key, entries))
        if responses:
            return responses

        # Need to block - build a callback that remembers that IDs
        ids_by_key = dict(zip(keys, ids))

        def unblock_for_xread(key: str) -> list[Any] | None:
            if not self.stream_ops.has_data(key):
                return None
            stream_id = ids_by_key[key]
            entries = self.stream_ops.xread(key, stream_id)
            if entries:
                return [self._format_stream(key, entries)]

        if expiry is not None:
            return BlockingResponse(
                keys=keys,
                timeout=expiry / 1000,
                unblock_callback=unblock_for_xread,
            )

        return None

    @staticmethod
    def _format_stream(key: str, entries: list[StreamEntry]) -> list[Any]:
        """Format a single stream's response as [key, [entries]]."""
        return [key, [entry.format() for entry in entries]]

    @staticmethod
    def _parse_streams_args(
        args: list[str],
    ) -> tuple[list[Any], list[Any], float | None] | RESPError:
        # if len(args) % 2 != 0:
        #     return RESPError(
        #         f"ERR unbalanced XREAD list of streams: {args}"
        #     )
        for arg_idx in range(len(args)):
            if args[arg_idx].upper() == "STREAMS":
                args[arg_idx] = args[arg_idx].upper()
            if args[arg_idx].upper() == "BLOCK":
                args[arg_idx] = args[arg_idx].upper()

        stream_idx = args.index("STREAMS") if "STREAMS" in args else None
        if stream_idx is None:
            return RESPError("ERR syntax error")

        block_idx = args.index("BLOCK") if "BLOCK" in args else None
        expiry: float | None = (
            float(args[block_idx + 1]) if block_idx is not None else None
        )
        streams = args[stream_idx + 1 :]
        mid = len(streams) // 2

        keys: list[str] = streams[:mid]
        ids: list[str] = streams[mid:]
        return keys, ids, expiry
