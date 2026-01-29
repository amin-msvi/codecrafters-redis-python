from app.blocking import BlockingState
from app.commands.base import Command
from app.data.lists import Lists


class RPushCommand(Command):
    name = "RPUSH"
    arity = (2, float("inf"))

    def __init__(self, lists: Lists, blocking_state: BlockingState):
        self.lists: Lists = lists
        self._blocking_state = blocking_state

    def execute(self, args: list[str]) -> int:
        list_name = args[0]
        list_values = args[1:]
        self.lists[list_name] = list_values
        new_length = len(self.lists[list_name])
        waiters = self._blocking_state.get_waiters_for_key(list_name)
        if waiters:
            from app.resp_encoder import encode_resp

            waiter = waiters[0]
            value = self.lists[list_name].pop(0)
            waiter.socket.sendall(encode_resp([list_name, value]))
            self._blocking_state.remove_waiter(waiter)
        return new_length
