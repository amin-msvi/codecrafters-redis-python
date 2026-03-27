from app.commands.base import Command, UnsubscribeResult
from app.server.pubsub import PubSubState


class UnsubscribeCommand(Command):
    name = "UNSUBSCRIBE"
    arity = (1, float('inf'))
    
    def __init__(self, pubsub_state: PubSubState):
        self._pubsub_state = pubsub_state
    
    def execute(self, args: list[str]) -> UnsubscribeResult:
        channel = args[0]
        return UnsubscribeResult(channel=channel)
        
    