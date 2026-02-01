from app.commands.registry import CommandRegistry
from app.config import ServerConfig

from app.data.key_space import KeySpace
from app.logger import setup_logging
from app.server import RedisServer


def main():
    setup_logging()
    config = ServerConfig()

    # Dependencies
    key_space = KeySpace()
    registry = CommandRegistry()
    registry.auto_discover(key_space)

    # Create and start server
    server = RedisServer(registry, key_space, config)
    server.start()


if __name__ == "__main__":
    main()
