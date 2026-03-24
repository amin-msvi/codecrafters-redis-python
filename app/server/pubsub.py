from collections import defaultdict
import socket

from app.resp_encoder import encode_resp
from app.types import RESPError


class PubSubState:
    def __init__(self):
        self._channels: dict[str, set[socket.socket]] = defaultdict(
            set
        )  # channels -> sockets
        self._allowed_commands = [
            "SUBSCRIBE",
            "UNSUBSCRIBE",
            "PSUBSCRIBE",
            "PING",
            "QUIT",
        ]

    def subscribe(self, client: socket.socket, channel: str):
        self._channels[channel].add(client)
    
    def publish(self, channel: str, message: str) -> None:
        subscribers = self._get_subscribers_of(channel)
        if subscribers is None:
            return

        for subscriber in subscribers:
            subscriber.sendall(encode_resp(["message", channel, message]))

    def unsubscribe(self, client: socket.socket, channel: str) -> None:
        self._channels[channel].remove(client)

    def subscription_count(self, client: socket.socket) -> int:
        """Returns the number of channels the client subscribed to (client_1 -> channel1, channel2 --> 2)"""
        return sum(
            1 for subscribers in self._channels.values() if client in subscribers
        )
    
    def publish_count(self, channel: str):
        """Returns the number of client (subscribers) that channel has: channel1: client1 --> 1"""
        return len(self._channels[channel])

    def intercept(
        self, client: socket.socket, parsed_data: list[str], cmd_name: str
    ) -> list[str] | RESPError | None:
        if not self.is_subscriber(client):
            return
        if cmd_name not in self._allowed_commands:
            return RESPError(
                f"Can't execute '{cmd_name}': only (P|S)SUBSCRIBE / (P|S)UNSUBSCRIBE / PING / QUIT / RESET are allowed in this context"
            )
        
        if cmd_name == "PING":
            return ["pong", ""]

    def is_subscriber(self, client: socket.socket) -> bool:
        return self.subscription_count(client) > 0
    
    def _get_subscribers_of(self, channel: str) -> set[socket.socket] | None:
        return self._channels.get(channel)