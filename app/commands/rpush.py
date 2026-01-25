from app.commands.base import Command


class RPushCommand(Command):
    name = "RPUSH"
    arity = (2, 2)

    def __init__(self):
        self.lists: dict[str, list] = {}
    
    def execute(self, args: list[str]) -> int:
        list_name = args[0]
        list_value = args[1]
        
        if list_name not in self.lists:
            self.lists[list_name] = []
        
        self.lists[list_name].append(list_value)
        return len(self.lists[list_name])
