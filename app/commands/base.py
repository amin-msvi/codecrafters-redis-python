from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
import socket
from typing import Any, Callable

from app.types import RDB, EncodeableValue, SimpleString


@dataclass
class BlockingResponse:
    keys: list[str]
    timeout: float  # 0 = wait forever
    unblock_callback: Callable[[str], tuple[str, Any] | list[Any] | None]


@dataclass
class UnblockEvent:
    key: str


@dataclass
class RDBSync:
    response: SimpleString
    rdb: RDB


@dataclass
class WaitBlocker:
    min_replicas: int
    target_offset: int
    timeout: datetime | None
    socket: socket.socket | None = None
    acked: int = 0


@dataclass
class CommandFlags:
    write: bool = False


@dataclass
class CommandResult:
    """Every command returns this to the server."""

    response: EncodeableValue
    event: UnblockEvent | None = None
    ack_master: bool = False


class Command(ABC):
    """
    Abstract base class for all Redis commands.

    Every command must define:
    - name: The command name (e.g., "GET")
    - arity: Tuple of (min_args, max_args), use float('inf') for unlimited
    - execute(): The command logic

    If the object that implements Command needs to contain some specific
    flags, they should be specified in the flags attribute.
    """

    name: str
    arity: tuple[int, int | float]  # (min, max) -- max can be infinity
    flags: CommandFlags = CommandFlags()

    @abstractmethod
    def execute(
        self, args: list[str]
    ) -> (
        CommandResult
        | BlockingResponse
        | RDBSync
        | WaitBlocker
    ):
        """
        Execute the command with the given arguments.

        Args:
            args: List of arguments (command name already removed)

        Returns:
            CommandResult for normal responses (with optional UnblockEvent),
            BlockingResponse to park the client,
            RDBSync for replication sync.
        """
        raise NotImplementedError

    def validate(self, args: list[str] | None) -> str | None:
        """
        Validate argument count against arity.

        Returns:
            Error message string if invalid, None if valid
        """
        if args is None:
            return None

        min_args, max_args = self.arity
        if min_args <= len(args) <= max_args:
            return None
        if min_args == max_args:
            return f"ERR wrong number of arguments for '{self.name.lower()}' command"
        return f"{self.name.lower()} must have minimum {min_args} and maximum {max_args} arguments."
