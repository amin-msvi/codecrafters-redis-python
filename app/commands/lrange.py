from app.commands.base import Command
from app.data.key_space import KeySpace
from app.data.list_helper import ListOps


class LRangeCommand(Command):
    name = "LRANGE"
    arity = (3, 3)

    def __init__(self, keyspace: KeySpace):
        self.list_ops = ListOps(keyspace)

    def execute(self, args: list[str]) -> list:
        key = args[0]
        start = int(args[1])
        stop = int(args[2])
        return self.list_ops.lrange(key, start, stop)
