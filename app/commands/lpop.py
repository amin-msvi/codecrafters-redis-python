from typing import Any
from app.commands.base import Command
from app.data.lists import Lists


class LPopCommand(Command):
    name = "LPOP"
    arity = (1, 2)

    def __init__(self, lists: Lists):
        self.lists = lists

    def execute(self, args: list[str]) -> Any:
        list_name = args[0]
        n_to_remove = 1
        if len(args) > 1:
            n_to_remove = int(args[1])

        if list_name in self.lists:
            if n_to_remove == 1:
                return self.lists[list_name].pop(0)
            remained = self.lists[list_name][:n_to_remove]
            del self.lists[list_name][:n_to_remove]
            return remained
        return None
