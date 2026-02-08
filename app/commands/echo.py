from app.commands.base import Command


class EchoCommand(Command):
    name = "ECHO"
    arity = (1, 1)

    def execute(self, args: list[str]) -> str:
        return args[0]
