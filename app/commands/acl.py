from app.commands.base import Command, CommandResult
from app.server.server_info import User
from app.types import RESPError, SimpleString


class ACLCommand(Command):
    name = "ACL"
    arity = (1, float("inf"))

    def __init__(self, user_info: User):
        self._user_info = user_info
    
    def execute(self, args: list[str]) -> CommandResult:
        subcommand = args[0]
        if subcommand.upper() == "WHOAMI":
            result = self._whoami(args[1:])
            return CommandResult(response=result)
        elif subcommand.upper() == "GETUSER":
            result = self._getuser(args[1:])
            return CommandResult(result)
        elif subcommand.upper() == "SETUSER":
            result = self._setuser(args[1:])
            return CommandResult(result)
        else:
            return CommandResult(RESPError("-ERR Subcommand for ACL not found."))
    
    def _whoami(self, args: list[str]) -> str:
        return self._user_info.username
    
    def _getuser(self, args: list[str]) -> list:
        return self._user_info.info.get_states()
    
    def _setuser(self, args: list[str]) -> SimpleString:
        password = args[1]
        return self._user_info.info.set_user(password)