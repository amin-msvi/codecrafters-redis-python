from typing import Any
from app.commands.base import Command


class EchoCommand(Command):
    name = "ECHO"
    arity = (1, 1)

    def execute(self, args: list[str]) -> Any:
        return args[0]
