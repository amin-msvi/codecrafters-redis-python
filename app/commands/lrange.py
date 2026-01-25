from app.commands.base import Command
from app.data.lists import Lists


class LRangeCommand(Command):
    name = "LRANGE"
    arity = (3, 3)
    
    def __init__(self, lists: Lists):
        self.lists = lists
    
    def execute(self, args: list[str]) -> list:
        list_name = args[0]
        start = int(args[1])
        stop = int(args[2])
        
        list_ = self.lists[list_name]

        # Converting negative indexes to positive
        if start < 0:
            start = max(0, start + len(list_))
        if stop < 0:
            stop = max(0, stop + len(list_))

        return list_[start:stop+1]
