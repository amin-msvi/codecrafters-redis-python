import inspect
from typing import Any
from app.commands.base import Command
from app.data_store import DataStore
from app.types import RESPError, RESPValue


class CommandRegistry:
    """Central registry for all commands."""

    def __init__(self):
        self._commands: dict[str, Command] = {}

    def register(self, command: Command) -> None:
        """Register a command instance"""
        self._commands[command.name.upper()] = command

    def get(self, name: str) -> Command | None:
        """Look up a command by name"""
        return self._commands.get(name)

    def execute(self, command_input: RESPValue) -> Any:
        """Main entry point - parse input, validate, and execute."""
        if command_input is None:
            return RESPError("empty command")

        if isinstance(command_input, RESPError):
            return command_input

        if isinstance(command_input, (str, int)):
            return RESPError("Invalid command format: expected array")

        cmd_name = command_input[0].upper()
        args = list(command_input[1:])

        command = self._commands.get(cmd_name)
        if command is None:
            return RESPError(message=f"Unknown command '{command_input[0]}'")

        # Check validation result
        error = command.validate(args)
        if error:
            return RESPError(message=error)

        return command.execute(args)

    def auto_discover(self, store: DataStore) -> None:
        """Find all Command subclasses and register them."""
        subclasses = Command.__subclasses__()

        for subclass in subclasses:
            signature = inspect.signature(subclass.__init__)
            instance = subclass(store) if "store" in signature.parameters else subclass()  # type: ignore[call-arg]
            self.register(instance)
