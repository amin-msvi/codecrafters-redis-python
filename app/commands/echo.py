from typing import Any
from app.commands.base import Command


class EchoCommand(Command):
    """
    ECHO message

    Return the message
    """

    name = "ECHO"
    arity = (1, 1)

    def execute(self, args: list[str]) -> Any:
        return args[0]
