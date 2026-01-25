from app.commands.base import Command
from app.data.lists import Lists


class RPushCommand(Command):
    name = "RPUSH"
    arity = (2, float("inf"))

    def __init__(self, lists: Lists):
        self.lists: Lists = lists

    def execute(self, args: list[str]) -> int:
        list_name = args[0]
        list_values = args[1:]
        self.lists[list_name] = list_values
        return len(self.lists[list_name])
