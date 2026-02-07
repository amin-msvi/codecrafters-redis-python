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
            return RESPError(str(e))  # Domain error -> RESP error
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


# I'm gonna keep it here if some issues rises later on.
# # ============== POC OLD METHODS ==============
# def __init__(self, database: DataBase) -> None:
#     self._database = database

# def get(self, key: str) -> RedisValue | None:
#     return self._database.get(key)

# def set(self, key: str, new_id: str, pairs: dict[str, Any]) -> RESPError | str:
#     redis_val = self._get_or_create(key)
#     if err := self._validate(key, new_id):
#         return err
#     new_id = self._get_id(key, new_id)
#     redis_val.data.append({"id": new_id, **pairs})
#     self._database.set(key, RedisValue(dtype="stream", data=redis_val.data))
#     return new_id

# # Private methods
# def _validate(self, key: str, new_id: str) -> RESPError | None:
#     if new_id == "*":
#         return
#     new_ts, new_seq = self._split_id(new_id)
#     if not new_ts or not new_seq:
#         return

#     if new_id == "0-0":
#         return RESPError("The ID specified in XADD must be greater than 0-0")

#     if top := self._get_top(key):
#         top_ts, top_seq = map(int, top["id"].split("-"))
#         if top_ts > int(new_ts):
#             return RESPError(
#                 "The ID specified in XADD is equal or smaller than the target stream top item"
#             )
#         elif top_ts == int(new_ts):
#             if int(new_seq) <= top_seq:
#                 return RESPError(
#                     "The ID specified in XADD is equal or smaller than the target stream top item"
#                 )

# def _get_id(self, key: str, id: str) -> str:
#     if id == "0-*":
#         return "0-1"

#     top = self._get_top(key)
#     top_ts, top_seq = self._split_id(top["id"]) if top else (None, None)

#     if id == "*":
#         if top_ts and top_seq:
#             new_ts = self._ts_now()
#             new_seq = "0" if new_ts != top_ts else str(int(top_seq) + 1)
#             return new_ts + "-" + new_seq
#         else:
#             return self._ts_now() + "-" + "0"
#     else:
#         new_ts, new_seq = self._split_id(id)


#     # auto-generating first entry in the stream
#     if not top_seq and not new_seq:
#         new_seq = "0"
#     # auto-generating next sequence entry in the existing stream
#     elif top_seq and not new_seq:
#         # Increment for identical timestamp otherwise initialize with 0
#         new_seq = str(int(top_seq) + 1) if top_ts == new_ts else "0"
#     return new_ts + "-" + new_seq if new_seq else "0"

# def xrange(self, key: str, start_id: str, end_id: str) -> list | None:
#     redis_val = self.get(key)
#     if not(redis_val and redis_val.data):
#         return

#     if start_id == "-":
#         start_ts, start_seq = "0", "0"
#     else:
#         start_ts, start_seq = self._split_id(start_id)

#     if end_id == "+":
#         end_ts, end_seq = float('inf'), float('inf')
#     else:
#         end_ts, end_seq = self._split_id(end_id)
#         end_ts, end_seq = int(end_ts), int(end_seq)
#     start_seq = start_seq if start_seq else "0"

#     range_list = []
#     for stream in redis_val.data:
#         ts, seq = self._split_id(stream["id"])
#         if int(start_ts) <= int(ts) <= end_ts:
#             if end_seq and int(start_seq) <= int(seq) <= end_seq:
#                 range_list.append(stream)
#             elif not end_seq and int(start_seq) <= int(seq):
#                 range_list.append(stream)
#     return self._xrange_format(range_list)

# def _xrange_format(self, streams: list[dict]):
#     final = []
#     for stream in streams:
#         id = stream.pop("id")
#         pairs = [item for pair in stream.items() for item in pair]
#         final.append([id, pairs])
#     return final

# @staticmethod
# def _split_id(id: str) -> tuple[str, str | None]:
#     """Splits the string defined id to separate millisecond timestamp and sequence number"""
#     ts, seq = id.split("-")
#     if seq == "*":
#         seq = None
#     return ts, seq

# @staticmethod
# def _ts_now() -> str:
#     return str(int(datetime.now().timestamp() * 1000))

# def _get_top(self, key: str) -> dict | None:
#     redis_val = self.get(key)
#     if redis_val and redis_val.data:
#         return redis_val.data[-1]
#     return None

# def _get_or_create(self, key) -> RedisValue:
#     val = self._database.get(key)
#     if not val:
#         val = RedisValue(dtype="stream", data=[])
#         self._database.set(key, val)
#         return val
#     if val.dtype != "stream":
#         raise TypeError(f"WRONGTYPE {key} is not a stream")
#     return val
