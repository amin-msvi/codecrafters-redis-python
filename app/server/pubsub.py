from collections import defaultdict
from dataclasses import dataclass
import socket


@dataclass
class PubSubState:
    def __init__(self):
        self._channels: dict[str, set[socket.socket]] = defaultdict(set)  # channels -> sockets
    
    def subscribe(self, client: socket.socket, channel: str):
        self._channels[channel].add(client)
    
    def subscription_count(self, client: socket.socket) -> int:
        return sum(1 for subscribers in self._channels.values() if client in subscribers)
