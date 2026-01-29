from app.commands.base import BlockingResponse, Command
from app.data.lists import Lists


class BLPopCommand(Command):
    name = "BLPOP"
    arity = (1, 2)

    def __init__(self, lists: Lists):
        self.lists = lists

    def execute(self, args: list[str]) -> list | BlockingResponse:
        list_name = args[0]
        timeout = int(args[1])
        if list_name in self.lists:
            return [list_name, self.lists[list_name].pop(0)]
        else:
            return BlockingResponse(keys=[list_name], timeout=timeout)
