from app.resp_parser import RESPError
from app.command_handlers import SimpleString


def encode_simple_string(s: str) -> bytes:
    """Encodes as +OK\r\n"""
    return f"+{s}\r\n".encode("utf-8")


def encode_error(message: str) -> bytes:
    """Encode as -ERR message\r\n"""
    return f"-ERR {message}\r\n".encode("utf-8")


def encode_integer(n: int) -> bytes:
    """Encode as :42\r\n"""
    return f":{n}\r\n".encode("utf-8")


def encode_bulk_string(s: str | None) -> bytes:
    """Encode as $3\r\nhey\r\n or $-1\r\n for None"""
    if s is None:
        return "$-1\r\n".encode("utf-8")
    return f"${len(s)}\r\n{s}\r\n".encode("utf-8")


def encode_array(items: list | None) -> bytes:
    """Encode as *2\r\n..., recursively calling encode_resp()"""
    if items is None:
        return b"*-1\r\n"
    count = len(items)
    parts = [f"*{count}\r\n".encode("utf-8")]
    for item in items:
        parts.append(encode_resp(item))
    return b"".join(parts)


def encode_resp(value) -> bytes:
    """Generic encoder that auto-detects type and routes"""
    if isinstance(value, SimpleString):
        return encode_simple_string(value.s)
    elif isinstance(value, str):
        return encode_bulk_string(value)
    elif isinstance(value, int):
        return encode_integer(value)
    elif isinstance(value, list):
        return encode_array(value)
    elif isinstance(value, RESPError):
        return encode_error(value.message)
    elif value is None:
        return encode_bulk_string(None)
    else:
        raise ValueError(f"Cannot encode type: {type(value)}")
