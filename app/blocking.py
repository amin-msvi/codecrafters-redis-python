from dataclasses import dataclass
from datetime import datetime
import socket


@dataclass
class WaitingClient:
    socket: socket.socket
    keys: list[str]
    timeout_at: datetime | None


class BlockingState:
    def __init__(self):
        # sample: {'list_key1': [client1, client2], 'list_key2': [client2, client3]}
        self._waiting_by_key: dict[str, list[WaitingClient]] = {}
        # sample: [client1, client2, client3]
        self._all_waiting: list[WaitingClient] = []

    def add_waiting(self, client: WaitingClient) -> None:
        self._all_waiting.append(client)
        for key in client.keys:
            self._waiting_by_key.setdefault(key, []).append(client)

    def get_waiters_for_key(self, key: str) -> list[WaitingClient]:
        return self._waiting_by_key.get(key, [])

    def remove_waiter(self, client: WaitingClient) -> None:
        self._all_waiting.remove(client)

        for key in client.keys:
            if key in self._waiting_by_key:
                self._waiting_by_key[key].remove(client)
                if not self._waiting_by_key[key]:
                    del self._waiting_by_key[key]

    def get_timed_out(self) -> list[WaitingClient]:
        timed_out_clients = []
        now = datetime.now()
        for client in self._all_waiting:
            if client.timeout_at and client.timeout_at < now:
                timed_out_clients.append(client)
        return timed_out_clients
