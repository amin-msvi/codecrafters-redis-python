from typing import Any
from app.commands.base import Command
from app.data.data_store import DataStore


class GetCommand(Command):
    name = "GET"
    arity = (1, 1)  # Exactly 1 argument

    def __init__(self, store: DataStore):
        self.store = store

    def execute(self, args: list[str]) -> Any:
        return self.store.get(args[0])
