from dataclasses import dataclass


@dataclass
class RDBEntry:
    value: str
    dtype: str
    expiry: int | None


@dataclass
class ParsedRDB:
    version: str
    metadata: dict[str, str]
    data: dict[str, RDBEntry]


class SpecialStringEncoded:
    pass


class RDBProtocolError(Exception):
    def __init__(self, message):
        super().__init__(message)
