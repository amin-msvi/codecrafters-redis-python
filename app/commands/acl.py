from app.commands.base import Command, CommandResult
from app.server.server_info import User
from app.types import SimpleString


class ACLCommand(Command):
    name = "ACL"
    arity = (1, float("inf"))

    def __init__(self, users_info: User):
        self._users_info = users_info
    
    def execute(self, args: list[str]) -> CommandResult:
        subcommand = args[0]
        if subcommand.upper() == "WHOAMI":
            result = self._whoami(args[1:])
            return CommandResult(response=result)
        if subcommand.upper() == "GETUSER":
            result = self._getuser(args[1:])
            return CommandResult(result)
        if subcommand.upper() == "SETUSER":
            result = self._setuser(args[1:])
            return CommandResult(result)
    
    def _whoami(self, args: list[str]) -> str:
        return self._users_info.username
    
    def _getuser(self, args: list[str]) -> list:
        return self._users_info.info.get_states()
    
    def _setuser(self, args: list[str]) -> SimpleString:
        password = args[1]
        return self._users_info.info.set_user(password)