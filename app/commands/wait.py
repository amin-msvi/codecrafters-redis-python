from app.commands.base import BlockingResponse, Command, CommandResult, RDBSync
from app.server.server_info import ServerInfo


class WaitCommand(Command):
    name = "WAIT"
    arity = (2, 2)

    def __init__(self, server_info: ServerInfo):
        self._server_info = server_info
    
    def execute(self, args: list[str]) -> CommandResult | BlockingResponse | RDBSync:
        n_replica = int(args[0])
        wait_for = int(args[1])
        return CommandResult(response=0)
        
