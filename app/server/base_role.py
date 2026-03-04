from abc import ABC, abstractmethod
import socket
from app.commands.base import CommandFlags, WaitBlocker


class ServerRole(ABC):
    """
    Strategy interface for role-specific server behavior.

    The server calls these hooks at specific points in its lifecycle.
    Each role decides what to do (or nothing)
    """

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

    def on_startup(self) -> None:
        """Called once before the event loop starts."""
        pass

    def after_command(self, data: bytes, flags: CommandFlags | None) -> None:
        """Called after a command is processed and response is sent"""
        pass

    def get_extra_sockets(self) -> list[socket.socket]:
        """Return additional sockets to monitor in select()."""
        return []

    def add_socket(self, sock: socket.socket) -> None:
        pass

    def on_wait(self, waiter_blocker: WaitBlocker, sock: socket.socket) -> None:
        pass

    def handle_expired_clients(self) -> None:
        pass
