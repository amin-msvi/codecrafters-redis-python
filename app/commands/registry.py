import inspect
from typing import Any
from app.blocking import BlockingState
from app.commands.base import Command
from app.data.data_store import DataStore
from app.data.lists import Lists
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

    def auto_discover(
        self, store: DataStore, lists: Lists, blocking_state: BlockingState
    ) -> None:
        """Find all Command subclasses and register them."""
        subclasses = Command.__subclasses__()

        for subclass in subclasses:
            instance = self._instantiate_command(subclass, store, lists, blocking_state)
            self.register(instance)

    def _instantiate_command(
        self,
        command_class: type[Command],
        store: DataStore,
        lists: Lists,
        blocking_state: BlockingState,
    ) -> Command:
        signature = inspect.signature(command_class.__init__)
        params = signature.parameters

        kwargs = {}
        if "store" in params:
            kwargs["store"] = store
        if "lists" in params:
            kwargs["lists"] = lists
        if "blocking_state" in params:
            kwargs["blocking_state"] = blocking_state
        return command_class(**kwargs)
