import socket  # noqa: F401
from app.logger import setup_logging, get_logger

# Initialize logger for this module
logger = get_logger(__name__)

SERVER_ADDRESS = "localhost"
SERVER_PORT = 6379

def main():
    setup_logging()
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    logger.info("Logs from your program will appear here!")

    with socket.create_server((SERVER_ADDRESS, SERVER_PORT), reuse_port=True) as server_socket:
        connection, address = server_socket.accept() # wait for client
        logger.info("Connection received from: %s", address)
        data = connection.recv(1024)
        logger.info("Received data: %s", data)
        if b"PING" in data:
            connection.sendall(b"+PONG\r\n")


if __name__ == "__main__":
    main()
