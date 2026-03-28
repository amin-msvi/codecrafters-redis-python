from app.commands.base import Command, CommandResult
from app.data.db import DataBase
from app.data.zset_helper import ZSetOps


class ZRemCommand(Command):
    name = "ZREM"
    arity = (2, 2)

    def __init__(self, database: DataBase) -> None:
        self._zset_ops = ZSetOps(database)

    def execute(self, args: list[str]) -> CommandResult:
        key, member = args
        removed_members_count = self._zset_ops.remove(key, member)
        return CommandResult(response=removed_members_count)
