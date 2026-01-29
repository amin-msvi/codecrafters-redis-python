from app.commands.base import BlockingResponse, Command
from app.data.lists import Lists


class BLPopCommand(Command):
    name = "BLPOP"
    arity = (2, float("inf"))

    def __init__(self, lists: Lists):
        self.lists = lists

    def execute(self, args: list[str]) -> list | BlockingResponse:
        keys = args[:-1]
        timeout = float(args[-1])

        for key in keys:
            if key in self.lists and len(self.lists[key]) > 0:
                value = self.lists[key].pop(0)
                return [key, value]

        # No data available - signal to block
        return BlockingResponse(keys=keys, timeout=timeout)
