from app.commands.base import Command, UnblockEvent
from app.data.key_space import KeySpace
from app.data.list_helper import ListOps


class RPushCommand(Command):
    name = "RPUSH"
    arity = (2, float("inf"))

    def __init__(self, keyspace: KeySpace):
        self.list_ops = ListOps(keyspace)

    def execute(self, args: list[str]) -> tuple[int, UnblockEvent]:
        key = args[0]
        values = args[1:]
        length = self.list_ops.rpush(key, values)
        return length, UnblockEvent(key=key)
