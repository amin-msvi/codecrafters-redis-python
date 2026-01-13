import socket  # noqa: F401
from app.logger import setup_logging, get_logger

# Initialize logger for this module
logger = get_logger(__name__)


def main():
    setup_logging()
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    logger.info("Logs from your program will appear here!")

    # Uncomment the code below to pass the first stage
    server_socket = socket.create_server(("localhost", 6379), reuse_port=True)
    server_socket.accept() # wait for client


if __name__ == "__main__":
    main()
