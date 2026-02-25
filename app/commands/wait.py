from datetime import datetime, timedelta
from app.commands.base import Command, CommandResult, WaitBlocker
from app.server.server_info import ServerInfo


class WaitCommand(Command):
    name = "WAIT"
    arity = (2, 2)

    def __init__(self, server_info: ServerInfo):
        self._server_info = server_info

    def execute(self, args: list[str]) -> CommandResult | WaitBlocker:
        num_replicas = int(args[0])
        timeout = int(args[1])
        target_offset = self._server_info.replication.master_repl_offset
        expiry = datetime.now() + timedelta(milliseconds=timeout)
        return WaitBlocker(
            min_replicas=num_replicas,
            target_offset=target_offset,
            timeout=expiry if timeout != 0 else None,
        )
