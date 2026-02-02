from app.commands.base import Command, UnblockEvent
from app.data.db import DataBase
from app.data.list_helper import ListOps


class LPushCommand(Command):
    name = "LPUSH"
    arity = (2, float("inf"))

    def __init__(self, database: DataBase):
        self.list_ops = ListOps(database)

    def execute(self, args: list[str]) -> tuple[int, UnblockEvent]:
        key = args[0]
        values = args[1:]
        length = self.list_ops.lpush(key, values)
        return length, UnblockEvent(key=key)
