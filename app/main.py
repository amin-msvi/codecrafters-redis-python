from argparse import ArgumentParser, Namespace
from app.commands.registry import CommandRegistry
from app.config import ServerConfig, TCPServerConfig

from app.data.db import DataBase
from app.logger import setup_logging
from app.server import (
    MasterRole,
    MasterInfo,
    Replication,
    ReplicaRole,
    RedisServer,
    ServerInfo,
)
from app.server.connection import MasterConnection


def parse_cli_args() -> Namespace:
    parser = ArgumentParser(description="Redis server")
    parser.add_argument(
        "-p", "--port", type=int, default=6379, help="Port to listen on"
    )
    parser.add_argument(
        "--replicaof", type=str, default=None, help="'<host> <port>' of master"
    )
    parser.add_argument(
        "--dir", type=str, default=None, help="rdb directory"
    )
    parser.add_argument(
       "--dbfilename", type=str, default=None, help="rdb filename"
    )
    return parser.parse_args()


def get_server_info(args: Namespace) -> ServerInfo:
    replication = Replication(role="slave" if args.replicaof is not None else "master")
    return ServerInfo(replication=replication)


def get_server_config(args: Namespace) -> ServerConfig:
    server_config = ServerConfig()
    if args.dir:
        server_config.dir = args.dir
    if args.dbfilename:
        server_config.dbfilename = args.dbfilename
    return server_config
            

def main():
    setup_logging()

    # Configurations
    args = parse_cli_args()
    config = TCPServerConfig(port=args.port)

    # Dependencies
    server_info = get_server_info(args)
    server_config = get_server_config(args)
    dependencies = {
        DataBase: DataBase(),
        ServerInfo: server_info,
        ServerConfig: server_config
    }
    registry = CommandRegistry()
    registry.auto_discover(dependencies)

    # Role assignment
    if args.replicaof:
        master_info = MasterInfo.from_string(args.replicaof)
        connection = MasterConnection(master_info, config)
        master_socket, buffer = connection.establish()
        role = ReplicaRole(master_socket, server_info, registry, config, buffer)
    else:
        role = MasterRole(server_info, registry, config)

    # Create and start server
    server = RedisServer(role, registry, config, server_info)
    server.start()


if __name__ == "__main__":
    main()
