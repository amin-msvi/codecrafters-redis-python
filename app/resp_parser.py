from app.types import ParseResult, RESPError, RESPProtocolError


def parse_bulk_string(data: bytes) -> tuple[str | None, bytes]:
    """
    Parse a bulk string from RESP format.

    Format: $<length>\r\n<data>\r\n
    Example: $5\r\nhello\r\n

    Returns: (parsed string, remaining_bytes)
    """

    if not data.startswith(b"$"):
        raise RESPProtocolError(
            "Invalid bulk string: must start with '$'", data=data, position=0
        )

    try:
        length_end_idx = data.index(b"\r\n")
    except ValueError:
        raise RESPProtocolError(
            "Invalid bulk string: missing \\r\\n after length", data=data
        )

    # Parse the length
    try:
        length = int(data[1:length_end_idx].decode("utf-8"))
    except ValueError:
        raise RESPProtocolError(
            "Invalid bulk string: could not parse length", data=data, position=1
        )

    # Handle null bulk string
    if length == -1:
        remaining = data[length_end_idx + 2 :]
        return None, remaining
    # Handle emptry string
    if length == 0:
        # Emptry string: $0\r\n\r\n
        data_start = length_end_idx + 2
        if not data[data_start:].startswith(b"\r\n"):
            raise RESPProtocolError(
                "Invalid bulk string: missing \\r\\n after empty data",
                data=data,
                position=data_start,
            )
        remaining = data[data_start + 2 :]
        return "", remaining

    # Parse the actual string data
    data_start = length_end_idx + 2
    data_end = data_start + length

    if len(data) < data_end + 2:
        raise RESPProtocolError(
            f"Bulk string complete: expected {length} bytes...",
            data=data,
            position=data_start,
        )

    if data[data_end : data_end + 2] != b"\r\n":
        raise RESPProtocolError(
            "Invalid bulk string: missing \\r\\n after data",
            data=data,
            position=data_end,
        )

    string_data = data[data_start:data_end].decode("utf-8")
    remaining = data[data_end + 2 :]
    return string_data, remaining


def parse_simple_string(data: bytes) -> tuple[str, bytes]:
    """
    Parse a RESP simple string.

    Format: +<string>\r\n
    Example: +OK\r\n

    Returns: (parsed_string, remaining_bytes)
    """
    if not data.startswith(b"+"):
        raise RESPProtocolError(
            "Invalid simple string: must start with '+'",
            data=data,
            position=0,
        )

    try:
        end_idx = data.index(b"\r\n")
    except ValueError:
        raise RESPProtocolError(
            "Invalid simple string: missing \\r\\n terminator", data=data
        )

    # Extract string
    string_value = data[1:end_idx].decode("utf-8")
    remaining = data[end_idx + 2 :]

    return string_value, remaining


def parse_error(data: bytes) -> tuple[RESPError, bytes]:
    """
    Parse a RESP error.

    Format: -<error message>\r\n
    Example: -ERR unknown command\r\n

    Returns: (RESPError)
    """

    if not data.startswith(b"-"):
        raise RESPProtocolError(
            "Invalid error: must start with '-'",
            data=data,
            position=0,
        )

    try:
        # Find the \r\n terminator
        end_idx = data.index(b"\r\n")
    except ValueError:
        raise RESPProtocolError(
            "Invalid error: missing \\r\\n terminator",
            data=data,
        )

    error_message = data[1:end_idx].decode("utf-8")
    remaining = data[end_idx + 2 :]

    return RESPError(message=error_message), remaining


def parse_integer(data: bytes) -> tuple[int, bytes]:
    """
    Parse a RESP integer.

    Format: :<number>\r\n
    Example: :42\r\n or :-1\r\n

    Returns: parsed_integer
    """

    if not data.startswith(b":"):
        raise RESPProtocolError(
            "Invalid integer: must start with ':'", data=data, position=0
        )

    try:
        end_idx = data.index(b"\r\n")
    except ValueError:
        raise RESPProtocolError(
            "Invalid integer: missing \r\n terminator",
            data=data,
        )

    try:
        int_value = int(data[1:end_idx].decode("utf-8"))
    except ValueError:
        raise RESPProtocolError(
            "Invalid integer: could not parse number",
            data=data,
            position=1,
        )
    remaining = data[end_idx + 2 :]
    return int_value, remaining


def parse_array(
    data: bytes, depth: int = 0, max_depth: int = 10
) -> tuple[list | None, bytes]:
    """
    Parse a RESP array (recursively)

    Format: *<count>\r\n<element1><element2>...<elementN>
    Example: *2\r\n$5\r\nhello\r\n$5world\r\n
    Special: *-1\r\n (null array)

    Returns parsed_array_or_none
    """
    if depth > max_depth:
        raise RESPProtocolError(
            f"Array nesting too deep (max depth: {max_depth}",
            data=data,
            position=0,
        )

    if not data.startswith(b"*"):
        raise RESPProtocolError(
            "Invalid array: must start with '*'",
            data=data,
            position=0,
        )

    try:
        # Finding the first \r\n which is the end of count specification
        count_end_idx = data.index(b"\r\n")
    except ValueError:
        raise RESPProtocolError(
            "Invalid array: missing \\r\\n after count",
            data=data,
        )

    # Parse the count
    try:
        count = int(data[1:count_end_idx].decode("utf-8"))
    except ValueError:
        raise RESPProtocolError(
            "Invalid array: could not parse count",
            data=data,
            position=1,
        )

    # Handle null array
    if count == -1:
        remaining = data[count_end_idx + 2 :]
        return None, remaining

    # Handle empty array
    if count == 0:
        remaining = data[count_end_idx + 2 :]
        return [], remaining

    # Parse array elements recursively
    remaining = data[count_end_idx + 2 :]
    elements = []

    for i in range(count):
        if not remaining:
            raise RESPProtocolError(
                f"Array incomplete: expected {count} elements, got {i}",
                data=data,
                position=len(data),
            )
        # Recursively parse each element
        element, remaining = parse_resp(remaining, depth=depth + 1, max_depth=max_depth)
        elements.append(element)

    return elements, remaining


def parse_resp(data: bytes, depth: int = 0, max_depth: int = 10) -> ParseResult:
    """
    Parse one RESP value from data.

    Dispatcher function that routes to the appropriate parser based on the first byte.

    Returns:
        (parsed_value, remaining_bytes)

    Return types by RESP type:
        Simple String (+) → str
        Error (-)         → RESPError
        Integer (:)       → int
        Bulk String ($)   → str | None (None for null bulk strings)
        Array (*)         → list | None (None for null arrays)

    Raises:
        RESPProtocolError: if data is malformed or empty
    """

    if not data:
        raise RESPProtocolError("Cannot parse empty data")

    first_byte = data[0:1]

    if first_byte == b"+":
        return parse_simple_string(data)
    elif first_byte == b"-":
        return parse_error(data)
    elif first_byte == b":":
        return parse_integer(data)
    elif first_byte == b"$":
        return parse_bulk_string(data)
    elif first_byte == b"*":
        return parse_array(data, depth=depth, max_depth=max_depth)
    else:
        raise RESPProtocolError(
            f"Unknown RESP type indicator: {first_byte!r}", data=data, position=0
        )
