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
        
        if not list_:
            return []
        
        if start >= len(list_):
            return []
        
        if stop >= len(list_):
            stop = len(list_)
        
        if start > stop:
            return []
        
        return list_[start:stop+1]
