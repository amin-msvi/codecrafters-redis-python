from app.data.db import DataBase, RedisValue
from app.data.stream.stream_entry import StreamEntry
from app.data.stream.stream_id import StreamID, StreamIDGenerator
from app.types import RESPError
from app.data.stream.stream import Stream


class StreamOps:
    """
    Operations layer for Redis Streams.

    Responsibilies:
        - Interface between commands and storage
        - Orchestrate domain object (Stream, StreamID, StreamEntry)
        - Handle storage-level concerns (get/create from database)
    """

    def __init__(self, database: DataBase) -> None:
        self._db = database
        self._id_gen = StreamIDGenerator()

    def add(
        self, key: str, id_pattern: str, fields: dict[str, str]
    ) -> StreamID | RESPError:
        """
        Add an entry to a stream.

        Args:
            key: The stream key
            id_pattern: ID pattern ("*", "1234-*", or "1234-5")
            fields: Key-value pairs for the entry

        Returns:
            The generated StreamID on success, or RESPError on failure
        """
        stream = self._get_or_create_stream(key)
        id = self._id_gen.generate(id_pattern, stream.top_id())
        entry = StreamEntry(id=id, fields=fields)
        try:
            stream.add(entry)
        except ValueError as e:
            return RESPError("-ERR " + str(e))  # Domain error -> RESP error
        return id

    def xrange(self, key: str, start_id: str, end_id: str) -> list[StreamEntry]:
        """
        Get entries in a range.

        Args:
            key: The stream key
            start_id: Start ID or "-" for minimum
            end_id: End ID or "+" for maximum

        Returns:
            List of entries in the range (empty if stream doesn't exist)
        """
        stream = self._get_stream(key)

        return (
            stream.range(
                start=StreamID.parse(start_id),
                end=StreamID.parse(end_id),
            )
            if stream
            else []
        )

    def xread(self, key: str, id: str) -> list[StreamEntry] | None:
        """Get entry for an id"""
        stream = self._get_stream(key)
        if not stream:
            return None
        return stream.read(StreamID.parse(id))

    def has_data(self, key: str) -> bool:
        return self._get_stream(key) is not None

    def top_id(self, key: str) -> StreamID | None:
        stream = self._get_stream(key)
        if stream:
            return stream.top_id()

    # Private Methods
    def _get_stream(self, key: str) -> Stream | None:
        """Get a stream from the database, or None if it doesn't exist."""
        redis_val = self._db.get(key)
        return redis_val.data if redis_val else None

    def _get_or_create_stream(self, key: str) -> Stream:
        """Get existing stream or create a new empty one."""
        redis_val = self._db.get(key)
        if not redis_val:
            redis_val = RedisValue(dtype="stream", data=Stream())
            self._db.set(key, redis_val)
        return redis_val.data
