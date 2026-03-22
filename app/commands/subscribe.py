from app.commands.base import Command, SubscribeResult
from app.server.pubsub import PubSubState


class SubscribeCommand(Command):
    name = "SUBSCRIBE"
    arity = (1, 1)
    
    def __init__(self, pubsub_state: PubSubState):
        self._pubsub_state = pubsub_state
    
    def execute(self, args: list[str]) -> SubscribeResult:
        channel_name = args[0]
        return SubscribeResult(channel=channel_name)
