from app.commands.base import Command, CommandResult
from app.types import SimpleString


class PingCommand(Command):
    """
    PING [message]

    Returns PONG if no argument, otherwise returns the message.
    """

    name = "PING"
    arity = (0, 1)

    def execute(self, args: list[str]) -> CommandResult:
        if len(args) == 0:
            return CommandResult(response=SimpleString("PONG"))
        return CommandResult(response=args[0])
