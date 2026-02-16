from abc import ABC, abstractmethod
import socket
from typing_extensions import TYPE_CHECKING

from app.commands.base import CommandFlags

if TYPE_CHECKING:
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
    def after_command(self, data: bytes, flags: CommandFlags | None) -> None:
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
        """Checking whether the role has to handle a socket
        (e.g, Replica has to handle master socket)
        """
        ...

    @abstractmethod
    def add_socket(self, sock: socket.socket) -> None: ...
