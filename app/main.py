from app.commands.registry import CommandRegistry
from app.config import ServerConfig

from app.data.db import DataBase
from app.logger import setup_logging
from app.server import RedisServer


def main():
    setup_logging()
    config = ServerConfig()

    # Dependencies
    database = DataBase()
    registry = CommandRegistry()
    registry.auto_discover(database)

    # Create and start server
    server = RedisServer(registry, config)
    server.start()


if __name__ == "__main__":
    main()
