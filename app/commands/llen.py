from app.commands.base import Command
from app.data.lists import Lists


class LLenCommand(Command):
    name = "LLEN"
    arity = (1, 1)

    def __init__(self, lists: Lists):
        self.lists = lists

    def execute(self, args: list[str]) -> int:
        list_name = args[0]
        if list_name not in self.lists:
            return 0
        return len(self.lists[list_name])
