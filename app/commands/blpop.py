from typing import Any
from app.commands.base import BlockingResponse, Command
from app.data.key_space import KeySpace
from app.data.list_helper import ListOps


class BLPopCommand(Command):
    name = "BLPOP"
    arity = (2, float("inf"))

    def __init__(self, keyspace: KeySpace):
        self.list_ops = ListOps(keyspace)

    def execute(self, args: list[str]) -> list | BlockingResponse:
        keys = args[:-1]
        timeout = float(args[-1])

        for key in keys:
            if self.list_ops.has_data(key):
                value = self.list_ops.lpop(key)
                return [key, value]

        def unblock_for_blpop(key: str) -> tuple[str, Any] | None:
            if not self.list_ops.has_data(key):
                return None
            value = self.list_ops.lpop(key)
            return key, value

        # No data available - signal to block
        return BlockingResponse(
            keys=keys,
            timeout=timeout,
            unblock_callback=unblock_for_blpop,
        )
