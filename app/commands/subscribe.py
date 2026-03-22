from app.server.pubsub import PubSubState


class SubscribeCommand(Command):
    name = "SUBSCRIBE"
    arity = (1, 1)
    
    def __init__(self, pubsub_state: PubSubState):
        self._pubsub_state = pubsub_state
    
    def execute(self, args: list[str]) -> CommandResult | BlockingResponse | RDBSync | WaitBlocker:
        channel_name = args[0]
        return CommandResult(response=["subscribe", channel_name, 1])