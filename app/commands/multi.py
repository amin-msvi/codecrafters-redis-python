from typing import Any
from app.commands.base import Command
from app.types import SimpleString


class MultiCommand(Command):
    name = "MULTI"
    arity = (0, 0)
    
    def execute(self, args: list[str]) -> Any:
        print(args)
        return SimpleString("OK")
