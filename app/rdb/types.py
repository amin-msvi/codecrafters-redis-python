from dataclasses import dataclass
from datetime import datetime
from enum import IntEnum


@dataclass
class RDBEntry:
    value: str
    dtype: str
    expiry: datetime | None


@dataclass
class ParsedRDB:
    version: str
    metadata: dict[str, str]
    data: dict[str, RDBEntry]


class RDBProtocolError(Exception):
    def __init__(self, message):
        super().__init__(message)


class RDBOp(IntEnum):
    # Special Operator for different sections in RDB
    OP_METADATA = 0xFA
    OP_DB = 0xFE
    OP_DB_MARKER = 0xFB
    OP_EXPIRY_TIMESTAMP_SEC = 0xFD
    OP_EXPIRY_TIMESTAMP_MILLSEC = 0xFC
    OP_END_OF_RDB = 0xFF
    
    # Special values
    SEC_BYTES = 4
    MILL_SEC_BYTES = 8
    
    