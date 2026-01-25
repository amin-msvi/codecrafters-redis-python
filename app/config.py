from dataclasses import dataclass


@dataclass(frozen=True)
class ServerConfig:
    host: str = "localhost"
    port: int = 6379
    recv_buffer_size: int = 1024
    socket_backlog: int = 5


@dataclass(frozen=True)
class ParserConfig:
    max_array_depth: int = 10
    max_bulk_string_length: int = 512 * 1024 * 1024  # 512MB


# Default Configs
DEFAULT_SERVER_CONFIG = ServerConfig()
DEFAULT_PARSER_CONFIG = ParserConfig()
