import socket  # noqa: F401
from app.logger import setup_logging, get_logger
import select

from app.resp_encoder import encode_resp
from app.resp_parser import parse_resp
from app.command_handlers import handle_command

logger = get_logger(__name__)

SERVER_ADDRESS = "localhost"
SERVER_PORT = 6379


def main():
    setup_logging()

    logger.info("Starting the server...")

    with socket.create_server(
        (SERVER_ADDRESS, SERVER_PORT), reuse_port=True
    ) as server_socket:
        server_socket.setblocking(False)
        sockets_list = [server_socket]

        while True:
            ready_to_read, _, _ = select.select(sockets_list, [], [])

            for ready_socket in ready_to_read:
                if ready_socket == server_socket:
                    connection, _ = ready_socket.accept()
                    logger.info("Connection received from %s", connection)
                    sockets_list.append(connection)
                else:
                    data = ready_socket.recv(1024)
                    # Empty data
                    if data == b"":
                        logger.info("Client %s disconnected", ready_socket)
                        sockets_list.remove(ready_socket)
                        ready_socket.close()
                    else:
                        parsed_data = parse_resp(data)[0]
                        result = handle_command(parsed_data)
                        encoded_result = encode_resp(result)
                        ready_socket.sendall(encoded_result)


if __name__ == "__main__":
    main()
