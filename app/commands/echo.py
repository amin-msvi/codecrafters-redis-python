from app.commands.base import Command, CommandResult


class EchoCommand(Command):
    name = "ECHO"
    arity = (1, 1)

    def execute(self, args: list[str]) -> CommandResult:
        return CommandResult(response=args[0])
