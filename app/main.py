from app.commands.registry import CommandRegistry
from app.config import ServerConfig
from app.data_store import DataStore
from app.logger import setup_logging
from app.server import RedisServer


def main():
    setup_logging()
    config = ServerConfig()

    # Dependencies
    data_store = DataStore()
    registry = CommandRegistry()
    registry.auto_discover(data_store)

    # Create and start server
    server = RedisServer(registry, config)
    server.start()


if __name__ == "__main__":
    main()
