from dataclasses import dataclass
from app.commands.base import Command
from app.server_info import ServerInfo
from app.types import RDB, SimpleString

@dataclass
class RDBSync:
    response: SimpleString
    rdb: RDB


class PSyncCommand(Command):
    name = "PSYNC"
    arity = (2, 2)
    
    def __init__(self, server_info: ServerInfo):
        self._server_info = server_info
    
    def execute(self, args: list[str]) -> RDBSync | None:
        if args[0] == "?" and args[1] == "-1":
            master_replid = self._server_info.replication.master_replid
            master_repl_offset = self._server_info.replication.master_repl_offset
            response = f"FULLRESYNC {master_replid} {master_repl_offset}"

            return RDBSync(response=SimpleString(response), rdb=RDB(string=None))