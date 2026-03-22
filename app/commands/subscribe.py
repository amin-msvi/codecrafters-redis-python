from app.commands.base import BlockingResponse, Command, CommandResult, RDBSync, WaitBlocker


class SubscribeCommand(Command):
    name = "SUBSCRIBE"
    arity = (1, 1)
    
    def __init__(self):
        pass
    
    def execute(self, args: list[str]) -> CommandResult | BlockingResponse | RDBSync | WaitBlocker:
        channel_name = args[0]
        return CommandResult(response=["subscribe", channel_name, 1])