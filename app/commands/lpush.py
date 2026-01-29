from app.commands.base import Command, UnblockEvent
from app.data.lists import Lists


class LPushCommand(Command):
    name = "LPUSH"
    arity = (2, float("inf"))

    def __init__(self, lists: Lists):
        self.lists = lists

    def execute(self, args: list[str]) -> tuple[int, UnblockEvent]:
        list_name = args[0]
        list_values = args[1:]
        self.lists.lset(list_name, list_values)
        length = len(self.lists[list_name])
        return length, UnblockEvent(key=list_name)
