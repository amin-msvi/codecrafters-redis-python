from abc import ABC, abstractmethod
import socket

from app.server.server import RedisServer


class ServerRole(ABC):
    """
    Strategy interface for role-specific server behavior.
    
    The server calls these hooks at specific points in its lifecycle.
    Each role decides what to do (or nothing)
    """
    
    @abstractmethod
    def on_startup(self, server: "RedisServer") -> None:
        """Called once before the event loop starts."""
        ...
    
    @abstractmethod
    def after_command(self, data: bytes) -> None:
        """Called after a command is processed and response is sent"""
        ...
    
    @abstractmethod
    def get_extra_sockets(self) -> list[socket.socket]:
        """Return additional sockets to monitor in select()."""
        ...
    
    @abstractmethod
    def handle_socket(self, sock: socket.socket) -> None:
        """Handle data from role-specific socket (e.g., master socket)"""
        ...

    @abstractmethod
    def owns_socket(self, sock: socket.socket) -> bool:
        ...
