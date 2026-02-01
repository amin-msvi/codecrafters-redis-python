"""
RESP (Redis Serialization Protocol) type definitions.

This module contains all types used for RESP protocol encoding/decoding:
- SimpleString: RESP simple string type (+)
- RESPError: RESP error type (-)
- RESPProtocolError: Exception for protocol violations

Type aliases:
- RESPValue: Union of all possible RESP values (str, int, list, None, RESPError)
- ParseResult: Tuple of parsed RESP value and remaining bytes
- EncodeableValue: Union of all values that can be encoded to RESP format
"""

from dataclasses import dataclass


@dataclass
class SimpleString:
    string: str


@dataclass
class RESPError:
    message: str


class NullArray:
    pass


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
EncodeableValue = str | int | list | None | RESPError | SimpleString | NullArray
