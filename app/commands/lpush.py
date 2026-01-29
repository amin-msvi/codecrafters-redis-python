from app.blocking import BlockingState
from app.commands.base import Command
from app.data.lists import Lists
from app.resp_encoder import encode_resp


class LPushCommand(Command):
    name = "LPUSH"
    arity = (2, float("inf"))

    def __init__(self, lists: Lists, blocking_state: BlockingState):
        self.lists = lists
        self._blocking_state = blocking_state

    def execute(self, args: list[str]) -> int:
        list_name = args[0]
        list_values = args[1:]
        self.lists.lset(list_name, list_values)
        new_length = len(self.lists[list_name])

        # Check if anyone is waiting for this list
        waiters = self._blocking_state.get_waiters_for_key(list_name)
        if waiters:
            waiter = waiters[0]
            value = self.lists[list_name].pop(0)
            response = encode_resp([list_name, value])
            waiter.socket.sendall(response)
            self._blocking_state.remove_waiter(waiter)

        return new_length
