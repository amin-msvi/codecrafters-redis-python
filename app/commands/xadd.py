from app.commands.base import Command
from app.data.db import DataBase
from app.data.stream_helper import StreamOps
from app.types import RESPError
from app.utils.command_utils import parse_args


class XaddCommand(Command):
    name = "XADD"
    arity = (4, float("inf"))

    def __init__(self, database: DataBase):
        self.stream_ops = StreamOps(database)

    def execute(self, args: list[str]) -> RESPError | str:
        key = args[0]
        id = args[1]
        fields = self._get_pairs(args[2:])
        result = self.stream_ops.add(key, id, fields)
        if isinstance(result, RESPError):
            return result
        return str(result)

    def _get_pairs(self, pairs: list) -> dict:
        return parse_args(pairs)
