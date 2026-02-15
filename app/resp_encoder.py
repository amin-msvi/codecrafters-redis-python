from typing import assert_never

from app.types import RDB, EncodeableValue, NullArray, RESPError, SimpleString


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


def encode_rdb(s: str | None) -> bytes:
    """Encode as $<length>\r\n<binary-data> or $<len-of-binary>\r\n<empty-rdb-hex>\r\n"""
    if s is None:
        empty_rdb = bytes.fromhex(
            "524544495330303131fa0972656469732d76657205372e322e30fa0a72656469732d62697473c040fa056374696d65c26d08bc65fa08757365642d6d656dc2b0c41000fa08616f662d62617365c000fff06e3bfec0ff5aa2"
        )
        header = f"${len(empty_rdb)}\r\n".encode("utf-8")
        return header + empty_rdb

    header = f"${len(bytes.fromhex(s))}\r\n".encode("utf-8")
    body = bytes.fromhex(s)
    return header + body


def encode_array(items: list[EncodeableValue]) -> bytes:
    """Encode as *2\r\n..., recursively calling encode_resp()"""
    count = len(items)
    parts = [f"*{count}\r\n".encode("utf-8")]
    for item in items:
        parts.append(encode_resp(item))
    return b"".join(parts)


def encode_null_array() -> bytes:
    return b"*-1\r\n"


def encode_resp(value: EncodeableValue) -> bytes:
    """Generic encoder that auto-detects type and routes"""
    match value:
        case SimpleString():
            return encode_simple_string(value.string)
        case RESPError():
            return encode_error(value.message)
        case NullArray():
            return encode_null_array()
        case RDB():
            return encode_rdb(value.string)
        case str():
            return encode_bulk_string(value)
        case int():
            return encode_integer(value)
        case list():
            return encode_array(value)
        case None:
            return encode_bulk_string(None)
        case _:
            assert_never(value)
