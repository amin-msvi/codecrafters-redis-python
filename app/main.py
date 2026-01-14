import socket  # noqa: F401
from app.logger import setup_logging, get_logger
import select

logger = get_logger(__name__)

SERVER_ADDRESS = "localhost"
SERVER_PORT = 6379

def main():
    setup_logging()

    logger.info("Starting the server...")

    with socket.create_server((SERVER_ADDRESS, SERVER_PORT), reuse_port=True) as server_socket:
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
                    elif b"PING" in data:
                        ready_socket.sendall(b"+PONG\r\n")


if __name__ == "__main__":
    main()
