from app.commands.base import Command, CommandResult
from app.server.server_info import User


class AuthCommand(Command):
    name = "AUTH"
    arity = (2, 2)

    def __init__(self, user_info: User):
        self._user_info = user_info

    def execute(self, args: list[str]) -> CommandResult:
        username = args[0]
        password = args[1]
        auth_result = self._user_info.auth(username, password)
        return CommandResult(response=auth_result)
