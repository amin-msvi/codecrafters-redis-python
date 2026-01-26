from typing import Any
from app.commands.base import Command
from app.data.lists import Lists


class LPopCommand(Command):
    name = "LPOP"
    arity = (1, 1)
    
    def __init__(self, lists: Lists):
        self.lists = lists
    
    def execute(self, args: list[str]) -> Any:
        list_name = args[0]
        if list_name in self.lists:
            return self.lists[list_name].pop(0)
        return None
