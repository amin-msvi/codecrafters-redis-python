from abc import ABC, abstractmethod
from typing import Any


class Command(ABC):
    """
    Abstract base class for all Redis commands.

    Every command must define:
    - name: The command name (e.g., "GET")
    - arity: Tuple of (min_args, max_args), use float('inf') for unlimited
    - execute(): The command logic
    """
    name: str
    arity: tuple[int, int | float]  # (min, max) -- max can be infinity

    @abstractmethod
    def execute(self, args: list[str]) -> Any:
        """
        Execute the command with the given arguments.

        Args:
            args: List of arguments (command name already removed)

        Returns:
            The result to be encoded and sent to client
        """
        pass

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
