from dataclasses import dataclass


@dataclass(frozen=True, order=False)
class StreamID:
    """
    Value object representing a Redis ID.

    A stream ID consists of:
        - timestamp: milliseconds since epoch (or logical timestamp)
        - sequence: sequence number within that millisecond

    Format: "<timestamp>-<sequence>"

    Special values handled during parsing:
        - "*" = auto-generate both parts
        - "<ts>-*" = auto-generate sequence only
        - "-" = maximum possible ID (for XRANGE)
        - "+" = maximum possible ID (for XRANGE)
    """

    timestamp: int
    sequence: int

    # Factory Methods
    @classmethod
    def parse(cls, id_string: str) -> "StreamID":
        """
        Parse a stream ID string into a StreamID object.

        Args:
            id_string: String like "135-5"

        Returns:
            StreamID instance

        Raises:
            ValueError: If the string is not a valid stream ID format.
        """
        if id_string == "-":
            return cls.minimum()
        if id_string == "+":
            return cls.maximum()

        if "-" not in id_string:
            raise ValueError(f"Invalid stream ID format: {id_string}")

        parts = id_string.split("-")
        if len(parts) != 2:
            raise ValueError(f"Invalid stream ID format: {id_string}")
        ts, seq = map(int, id_string.split("-"))
        return cls(timestamp=ts, sequence=seq)

    @classmethod
    def minimum(cls) -> "StreamID":
        """
        Returns the minimum possible StreamID.
        Used to represent "-" in XRANGE (meaning: from the beginning).
        """
        return cls(timestamp=0, sequence=0)

    @classmethod
    def maximum(cls) -> "StreamID":
        """Return the maximum possible StreamID (represents "+" in XRANGE)."""
        import sys

        return cls(timestamp=sys.maxsize, sequence=sys.maxsize)

    # Comparison Methods
    def __lt__(self, other: "StreamID") -> bool:
        """
        Compare two StreamID.

        Comparison rules:
            1. First compare timestamps
            2. If timestamps equal, compare sequences
        """
        if self.timestamp < other.timestamp:
            return True
        if self.timestamp == other.timestamp and self.sequence < other.sequence:
            return True
        return False

    def __le__(self, other: "StreamID") -> bool:
        return self < other or self == other

    def __gt__(self, other: "StreamID") -> bool:
        return not self <= other

    def __ge__(self, other: "StreamID") -> bool:
        return not self < other

    def __str__(self) -> str:
        """Return the canonical string representation: '<timestamp>-<sequence>'"""
        return f"{self.timestamp}-{self.sequence}"

    # Validation Method
    def is_valid_successor_to(self, previous: "StreamID | None") -> bool:
        """
        Check if this ID can legally follow the previous ID.

        Rules:
            - If previous is None, any ID > 0-0 is valid
            - Otherwise, this ID must be strictly greater than previous
        """
        if self == StreamID.minimum():
            raise ValueError("The ID specified in XADD must be greater than 0-0")
        if previous and self <= previous:
            raise ValueError(
                "The ID specified in XADD is equal or smaller than the target stream top item"
            )
        return True


class StreamIDGenerator:
    """
    Handles the generation of new stream IDs from patterns.

    Separated from StreamID because generation needs context
    (current timestamp, previosu ID in stream).

    Patterns:
        - "*" = auto-generated timestamp-sequence
        - "<ts>-*" = use given timestamp, auto-generate sequence
    """

    def generate(self, pattern: str, top_id: StreamID | None) -> StreamID:
        """
        Generate a concrete StreamID from a pattern.

        Args:
            - pattern: The ID pattern ("*", "1234-*", or "1234-5")
            top_id: The current highest ID in the stream (None if empty)

        Returns:
            A new StreamID

        Raises:
            ValueError: If the pattern would produce an invalid ID
        """

        if self._is_full_auto(pattern):
            return self._generate_full_auto(top_id)
        if self._is_sequence_auto(pattern):
            timestamp = int(pattern.split("-")[0])
            return self._generate_sequence_auto(timestamp, top_id)
        return StreamID.parse(pattern)

    @staticmethod
    def _is_full_auto(pattern) -> bool:
        return pattern == "*"

    @staticmethod
    def _is_sequence_auto(pattern) -> bool:
        if "-" in pattern:
            _, seq = pattern.split("-")
            return seq == "*"
        return False

    def _generate_full_auto(self, top_id: StreamID | None) -> StreamID:
        ts = self._current_timestamp_ms()
        if not top_id:
            return StreamID(ts, 0)
        if ts == top_id.timestamp:
            return StreamID(ts, top_id.sequence + 1)
        return StreamID(ts, 0)

    def _generate_sequence_auto(
        self, timestamp: int, top_id: StreamID | None
    ) -> StreamID:
        if top_id and top_id.timestamp == timestamp:
            return StreamID(timestamp, top_id.sequence + 1)
        if timestamp == 0:
            # Special case for Redis: Illegal 0-0 -> Returns 0-1
            return StreamID(timestamp, 1)
        return StreamID(timestamp, 0)

    @staticmethod
    def _current_timestamp_ms() -> int:
        """Return current time in milliseconds since epoch."""
        from datetime import datetime
        return int(datetime.now().timestamp()) * 1000
