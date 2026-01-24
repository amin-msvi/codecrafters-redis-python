from app.commands.base import Command
from app.types import SimpleString


class PingCommand(Command):
    """
    PING [message]

    Returns PONG if no argument, otherwise returns the message.
    """

    name = "PING"
    arity = (0, 1)

    def execute(self, args: list[str]) -> SimpleString | str:
        # TODO: Implement PING logic
        # Hint: Return SimpleString("PONG") or the message
        if len(args) == 0:
            return SimpleString(string="PONG")
        return args[0]
