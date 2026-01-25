from app.commands.base import Command


class RPushCommand(Command):
    name = "RPUSH"
    arity = (2, float('inf'))

    def __init__(self):
        self.lists: dict[str, list] = {}
    
    def execute(self, args: list[str]) -> int:
        list_name = args[0]
        list_values = args[1:]
        
        if list_name not in self.lists:
            self.lists[list_name] = []
        
        for value in list_values:
            self.lists[list_name].append(value)
        return len(self.lists[list_name])
