from app.commands.base import Command
from app.data.key_space import KeySpace
from app.data.list_helper import ListOps


class LLenCommand(Command):
    name = "LLEN"
    arity = (1, 1)

    def __init__(self, keyspace: KeySpace):
        self.list_ops = ListOps(keyspace)

    def execute(self, args: list[str]) -> int:
        key = args[0]
        return self.list_ops.llen(key)
