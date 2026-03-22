from os import path
from app.config import ServerConfig
from app.data.db import DataBase, RedisValue
from app.rdb.parser import RDBParser
from app.rdb.types import ParsedRDB


class RDBLoader:
    """Loads an RDB file from disk and populates a DataBase using its public API.

    It has three phases:
    1. _load (read bytes)
    2. _parse (bytes → ParsedRDB)
    3. _populate (entries → DataBase).
    """

    def __init__(self, server_config: ServerConfig):
        self.binary_rdb: bytes | None = None
        self.server_config = server_config

    def load_into(self, database: DataBase) -> None:
        self.binary_rdb = self._load()
        parsed_rdb = self._parse()
        self._populate(parsed_rdb, database)

    def _load(self) -> bytes | None:
        rdb_path = f"{self.server_config.dir}/{self.server_config.dbfilename}"
        if not path.exists(rdb_path):
            return None

        with open(rdb_path, "rb") as f:
            return f.read()

    def _parse(self) -> ParsedRDB | None:
        if self.binary_rdb:
            rdb_parser = RDBParser(self.binary_rdb)
            return rdb_parser.parse()

    def _populate(self, parsed: ParsedRDB | None, database: DataBase) -> None:
        if parsed is None:
            return

        for key, rdb_entry in parsed.data.items():
            database.set(
                key,
                RedisValue(
                    data=rdb_entry.value,
                    dtype=rdb_entry.dtype,
                    expiry=rdb_entry.expiry,
                ),
            )
        return
