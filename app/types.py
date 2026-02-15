"""
RESP (Redis Serialization Protocol) type definitions.

Two categories of types flow through the system:

1. Protocol types - what the parser produces from raw bytes:
   str, int, list, None, RESPError
   Aliased as: RESPValue

2. Response wrapper types - encoding hints that commands use
   to control the wire format:
   SimpleString  -> encodes as +OK\\r\\n (not bulk string)
   NullArray     -> encodes as *-1\\r\\n (not null bulk string)
   RDB           -> encodes as binary RDB transfer
"""

from dataclasses import dataclass


# Protocol Types
@dataclass
class RESPError:
    message: str


@dataclass
class SimpleString:
    string: str


class NullArray:
    pass


@dataclass
class RDB:
    string: str | None


class RESPProtocolError(Exception):
    """Exception raised when RESP protocol is violated."""

    def __init__(self, message: str, data=None, position: int | None = None):
        """
        Args:
            message: Human-readable error description
            data: The invalid RESP data (optional)
            position: Position in the data where error occurred (optional)
        """

        self.message = message
        self.data = data
        self.position = position

        full_message = f"RESP Protocol Error: {message}"

        if position is not None:
            full_message += f" at {position}"
        if data is not None:
            # Showing a snippet of the problematic data (first 50 bytes)
            data_review = data[:50]
            full_message += f"\nData: {data_review!r}"
            if len(data) > 50:
                full_message += "..."

        super().__init__(full_message)


RESPValue = str | int | list | None | RESPError
ParseResult = tuple[RESPValue, bytes]
EncodeableValue = str | int | list | None | RESPError | SimpleString | NullArray | RDB
