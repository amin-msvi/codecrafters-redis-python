from app.commands.base import Command, CommandResult
from app.server.server_info import ACLState


class ACLCommand(Command):
    name = "ACL"
    arity = (1, float("inf"))

    def __init__(self, acl_state: ACLState):
        self._acl_state = acl_state
    
    def execute(self, args: list[str]) -> CommandResult:
        subcommand = args[0]
        if subcommand.upper() == "WHOAMI":
            result = self._whoami(args[1:])
            return CommandResult(response=result)
    
    def _whoami(self, args: list[str]) -> str:
        return self._acl_state.whoami
        