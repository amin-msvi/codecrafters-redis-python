import socket
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable


@dataclass
class WaitingClient:
    socket: socket.socket
    keys: list[str]
    timeout_at: datetime | None
    callback: Callable[[str], tuple[str, Any] | None | list[Any]]


class BlockingState:
    def __init__(self):
        self._waiters: dict[str, list[WaitingClient]] = {}

    def add(self, client: WaitingClient) -> None:
        for key in client.keys:
            self._waiters.setdefault(key, []).append(client)

    def pop(self, key: str) -> WaitingClient | None:
        """Pop the first waiter for a given key."""
        waiters = self._waiters.get(key)
        if not waiters:
            return None

        waiter = waiters.pop(0)
        if not waiters:
            del self._waiters[key]

        # Remove from all other keys this client was waiting on
        for k in waiter.keys:
            if k != key and k in self._waiters:
                try:
                    self._waiters[k].remove(waiter)
                except ValueError:
                    pass
                if not self._waiters[k]:
                    del self._waiters[k]

        return waiter

    def remove(self, client: WaitingClient) -> None:
        """Remove a client from all waiting lists (e.g., on timeout)."""
        for key in client.keys:
            if key in self._waiters:
                try:
                    self._waiters[key].remove(client)
                except ValueError:
                    pass
                if not self._waiters[key]:
                    del self._waiters[key]

    def get_expired(self, now: datetime) -> list[WaitingClient]:
        """Get all clients whose timeout has passed."""
        expired = []
        seen: set[int] = set()

        for waiters in self._waiters.values():
            for waiter in waiters:
                if (
                    id(waiter) not in seen
                    and waiter.timeout_at
                    and waiter.timeout_at < now
                ):
                    expired.append(waiter)
                    seen.add(id(waiter))

        return expired
