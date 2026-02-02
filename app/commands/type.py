from app.commands.base import Command
from app.data.db import DataBase
from app.types import SimpleString


class TypeCommand(Command):
    name = "TYPE"
    arity = (1, 1)

    def __init__(self, database: DataBase) -> None:
        self.database = database

    def execute(self, args: list[str]) -> SimpleString:
        key = args[0]
        value = self.database.get(key)
        if value:
            return SimpleString(value.dtype)
        return SimpleString("none")
