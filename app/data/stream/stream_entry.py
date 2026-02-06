from dataclasses import dataclass
from app.data.stream.stream_id import StreamID


@dataclass(frozen=True)
class StreamEntry:
    """
    Immutable value object representing a single entry in a Redis Stream.

    An entry consists of:
        - id: The unique StreamID
        - fields: Key-value pairs of data
    """

    id: StreamID
    fields: dict[str, str]

    def format(self) -> list:
        """Format for RESP response."""
        return [str(self.id), [field for pair in self.fields.items() for field in pair]]
