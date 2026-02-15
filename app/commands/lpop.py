from app.commands.base import Command, CommandFlags, CommandResult
from app.data.db import DataBase
from app.data.list_helper import ListOps


class LPopCommand(Command):
    name = "LPOP"
    arity = (1, 2)
    flags = CommandFlags(write=True)

    def __init__(self, database: DataBase):
        self.list_ops = ListOps(database)

    def execute(self, args: list[str]) -> CommandResult:
        key = args[0]
        count = 1
        if len(args) > 1:
            count = int(args[1])

        return CommandResult(response=self.list_ops.lpop(key, count))
