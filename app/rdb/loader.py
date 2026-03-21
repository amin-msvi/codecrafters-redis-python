from os import path
from datetime import datetime
from app.config import ServerConfig
from app.data.db import DataBase, RedisValue
from app.rdb.parser import RDBParser
from app.rdb.types import ParsedRDB


class RDBLoader:
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
        store: dict[str, RedisValue] = {}
        
        if parsed is None:
            database.store = store
            return
        
        for key, rdb_entry in parsed.data.items():
            expiry = None
            if rdb_entry.expiry:
                expiry = datetime.fromtimestamp(rdb_entry.expiry / 1000)
                if datetime.now() > expiry:
                    continue
            
            store[key] = RedisValue(
                data=rdb_entry.value,
                dtype=rdb_entry.dtype,
                expiry=expiry,
            )
        database.store = store
        return

    