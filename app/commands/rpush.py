from app.commands.base import Command, CommandFlags, CommandResult, UnblockEvent
from app.data.db import DataBase
from app.data.list_helper import ListOps


class RPushCommand(Command):
    name = "RPUSH"
    arity = (2, float("inf"))
    flags = CommandFlags(write=True)

    def __init__(self, database: DataBase):
        self.list_ops = ListOps(database)

    def execute(self, args: list[str]) -> CommandResult:
        key = args[0]
        values = args[1:]
        length = self.list_ops.rpush(key, values)
        return CommandResult(response=length, event=UnblockEvent(key=key))
