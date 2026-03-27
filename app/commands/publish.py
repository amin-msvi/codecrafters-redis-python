from app.commands.base import Command, PublishResult
from app.server.pubsub import PubSubState


class PublishCommand(Command):
    name = "PUBLISH"
    arity = (2, 2)

    def __init__(self, pubsub_state: PubSubState):
        self._pubsub_state = pubsub_state

    def execute(self, args: list[str]) -> PublishResult:
        channel_name = args[0]
        message = args[1]
        return PublishResult(channel=channel_name, message=message)
