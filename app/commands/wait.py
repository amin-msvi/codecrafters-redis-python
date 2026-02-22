from app.commands.base import BlockingResponse, Command, CommandResult, RDBSync
from app.server.server_info import ServerInfo


class WaitCommand(Command):
    name = "WAIT"
    arity = (2, 2)

    def __init__(self, server_info: ServerInfo):
        self._server_info = server_info
    
    def execute(self, args: list[str]) -> CommandResult | BlockingResponse | RDBSync:
        num_replicas = int(args[0])
        timeout = int(args[1])
        return CommandResult(response=self._server_info.replication.connected_slaves)
        
