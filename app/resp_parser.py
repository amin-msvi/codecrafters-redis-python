import re


class RESPProtocolError(Exception):
    """Exception raised when RESP protocl is violated."""
    
    def __init__(self, message: str, data = None, position: int | None = None):
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


def parse_bulk_string(data: bytes) -> str | None:
    """
    Parse a bulk string from RESP format.
    
    Format: $<length>\r\n<data>\r\n
    Example: $5\r\nhello\r\n
    
    Returns: (parsed string, remaining_bytes)
    """
    
    # Find length of bulk string
    pattern = r"\$(\d+)\r\n"
    match = re.match(pattern , data.decode())
    
    if not match:
        raise RESPProtocolError(
            "Invalid bulk string format: missing length specification.",
            data=data,
            position=0,
        )
    
    length = int(match.group(1))
    data_start = match.end()
    # bulk string
    if length == -1:
        return None
    # Empty string
    elif length == 0:
        return ""
    
    parsed_data = data[data_start:data_start+length]
    if data[data_start + length:] != b"\r\n":
        raise RESPProtocolError(
            f"Bulk String is incomplete. expected {length} bytes but got {len(data) - data_start - 2}",
            data=data,
            position=data_start
            
        )
        
    return parsed_data.decode()
