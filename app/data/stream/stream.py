from app.data.stream.stream_id import StreamID
from app.data.stream.stream_entry import StreamEntry


class Stream:
    """
    Represents a Redis Stream - an append-only log of entries.

    Responsibilities:
    - Store entries in order
    - Provide range queries
    - Track the top (latest) entry
    - Enforce ordering invariant (IDs must be monotonically increasing)

    This is a domain object - it knows nothing about storage or commands.
    """

    def __init__(self) -> None:
        self._entries: list[StreamEntry] = []

    def add(self, entry: StreamEntry) -> None:
        """
        Append an entry to the stream.

        Args:
            entry: The entry to add

        Raises:
            ValueError: If entry.id is not greater than current top ID

        Invariant: Entries are always in ascending ID order.
        """
        if entry.id.is_valid_successor_to(self.top_id()):
            self._entries.append(entry)

    def top(self) -> StreamEntry | None:
        """Return the most recent entry, or None if stream is empty."""
        return self._entries[-1] if not self.is_empty() else None

    def top_id(self) -> StreamID | None:
        """Return the ID of the most recent entry, or None if empty."""
        return self._entries[-1].id if not self.is_empty() else None

    def range(self, start: StreamID, end: StreamID) -> list[StreamEntry]:
        """
        Return all entries with IDs in the range [start, end] (inclusive).

        Args:
            start: Minimum ID (inclusive)
            end: Maximum ID (inclusive)

        Returns:
            List of entries in ascending order

        Note: For efficiency with large streams, consider binary search
        since entries are sorted. For now, linear scan is fine.
        """
        if start > end or self.is_empty():
            return []

        # TODO: I'll get back here to implement binary serach
        # Need to think how to find the inclusive start and end or the nearest
        # in the range
        return [ent for ent in self._entries if start <= ent.id <= end]

    def __len__(self) -> int:
        """Return number of entries in the stream."""
        return len(self._entries)

    def is_empty(self) -> bool:
        """Return True if stream has no entries."""
        return len(self._entries) == 0
