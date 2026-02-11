from argparse import ArgumentParser, Namespace
from app.commands.registry import CommandRegistry
from app.config import ServerConfig

from app.data.db import DataBase
from app.logger import setup_logging
from app.server import RedisServer
from app.server_info import Replication, ServerInfo


def parse_cli_args() -> Namespace:
    parser = ArgumentParser(description="Redis server")
    parser.add_argument(
        "-p", "--port", type=int, default=6379, help="Port to listen on"
    )
    parser.add_argument(
        "--replicaof", type=str, default=None, help="'<host> <port>' of master"
    )
    return parser.parse_args()


def main():
    setup_logging()

    # Configurations
    args = parse_cli_args()
    config = ServerConfig(port=args.port)
    replication = Replication(
        role="slave"
        if args.replicaof is not None
        else "master"
    )

    # Dependencies
    registry = CommandRegistry()
    dependencies = {
        ServerInfo: ServerInfo(replication=replication),
        DataBase: DataBase(),
    }
    registry.auto_discover(dependencies)

    # Create and start server
    server = RedisServer(registry, config)
    server.start()


if __name__ == "__main__":
    main()
