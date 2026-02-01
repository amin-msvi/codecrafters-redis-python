from typing import Any
from app.commands.base import Command
from app.data.key_space import KeySpace
from app.data.list_helper import ListOps


class LPopCommand(Command):
    name = "LPOP"
    arity = (1, 2)

    def __init__(self, keyspace: KeySpace):
        self.list_ops = ListOps(keyspace)

    def execute(self, args: list[str]) -> Any:
        key = args[0]
        count = 1
        if len(args) > 1:
            count = int(args[1])

        return self.list_ops.lpop(key, count)
