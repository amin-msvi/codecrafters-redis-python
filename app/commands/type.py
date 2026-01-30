from typing_extensions import Any
from app.commands.base import Command
from app.data.data_store import DataStore
from app.types import SimpleString
from app.commands.get import GetCommand


class TypeCommand(Command):
    name = "TYPE"
    arity = (1, 1)
    
    def __init__(self, store: DataStore) -> None:
        self.store = store
    
    def execute(self, args: list[str]) -> SimpleString:
        key = args[0]
        value = self._get_value(key)
        if value:
            if isinstance(value, str):
                return SimpleString("string")
        return SimpleString("none")
    
    def _get_value(self, key) -> Any:
       return GetCommand(self.store).execute([key])
       