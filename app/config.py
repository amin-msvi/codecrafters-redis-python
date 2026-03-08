from dataclasses import dataclass


@dataclass(frozen=True)
class TCPServerConfig:
    port: int
    host: str = "localhost"
    recv_buffer_size: int = 1024
    select_timeout: float = 0.1


@dataclass
class ServerConfig:
    dir: str = "./rdb/redis-files"
    dbfilename: str = "db.rdb"


@dataclass(frozen=True)
class RespParserConfig:
    max_array_depth: int = 10
    max_bulk_string_length: int = 512 * 1024 * 1024  # 512MB


# Default Configs
DEFAULT_RESP_PARSER_CONFIG = RespParserConfig()
