from app.commands.base import Command
from app.data.key_space import KeySpace
from app.types import SimpleString


class TypeCommand(Command):
    name = "TYPE"
    arity = (1, 1)
    
    def __init__(self, keyspace: KeySpace) -> None:
        self.keyspace = keyspace
    
    def execute(self, args: list[str]) -> SimpleString:
        key = args[0]
        value = self.keyspace.get(key)
        if value:
            return SimpleString(value.dtype)
        return SimpleString("none")
