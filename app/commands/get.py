from typing import Any
from app.commands.base import Command
from app.data_store import DataStore


class GetCommand(Command):
    """
    GET key

    Returns the value of key, or None if key doesn't exist.
    """

    name = "GET"
    arity = (1, 1)  # Exactly 1 argument

    def __init__(self, store: DataStore):
        self.store = store

    def execute(self, args: list[str]) -> Any:
        return self.store.get(args[0])
