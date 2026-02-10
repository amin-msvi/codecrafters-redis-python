from argparse import ArgumentParser, Namespace
from app.commands.registry import CommandRegistry
from app.config import ServerConfig

from app.data.db import DataBase
from app.logger import setup_logging
from app.server import RedisServer


def parse_cli_args() -> Namespace:
    parser = ArgumentParser(description="Redis server")
    parser.add_argument("--port", type=int, default=6379, help="Port to listen on")
    return parser.parse_args()


def main():
    setup_logging()
    
    args = parse_cli_args()
    config = ServerConfig(port=args.port)

    # Dependencies
    database = DataBase()
    registry = CommandRegistry()
    registry.auto_discover(database)

    # Create and start server
    server = RedisServer(registry, config)
    server.start()


if __name__ == "__main__":
    main()
