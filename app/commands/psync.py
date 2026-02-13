from app.commands.base import Command
from app.server_info import ServerInfo
from app.types import SimpleString


class PSyncCommand(Command):
    name = "PSYNC"
    arity = (2, 2)
    
    def __init__(self, server_info: ServerInfo):
        self._server_info = server_info
    
    def execute(self, args: list[str]) -> SimpleString:
        master_replid = self._server_info.replication.master_replid
        master_repl_offset = self._server_info.replication.master_repl_offset
        response = f"FULLRESYNC {master_replid} {master_repl_offset}"
        return SimpleString(response)