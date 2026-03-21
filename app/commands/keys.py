from app.commands.base import (
    BlockingResponse,
    Command,
    CommandResult,
    RDBSync,
    WaitBlocker,
)
from app.data.db import DataBase


class KeysCommand(Command):
    name = "KEYS"
    arity = (1, float("inf"))

    def __init__(self, database: DataBase):
        self._db = database

    def execute(
        self, args: list[str]
    ) -> CommandResult | BlockingResponse | RDBSync | WaitBlocker:
        keys = self._db.get_keys(args[0])
        return CommandResult(response=keys)
