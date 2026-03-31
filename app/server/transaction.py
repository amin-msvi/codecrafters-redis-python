from dataclasses import dataclass, field
import socket

from app.commands.registry import CommandRegistry
from app.commands.base import CommandResult
from app.types import EncodeableValue, RESPError, RESPValue, SimpleString


@dataclass
class ExecResult:
    result: EncodeableValue
    events: list[str] = field(default_factory=list)


class TransactionState:
    def __init__(self, registry: CommandRegistry):
        self._transactions: dict[socket.socket, list[RESPValue]] = {}
        self._registry = registry

    def start(self, client: socket.socket):
        self._transactions[client] = []

    def queue(self, client: socket.socket, parsed_data: list[str]):
        self._transactions[client].append(parsed_data)

    def discard(self, client):
        del self._transactions[client]

    def is_in_transaction(self, client: socket.socket) -> bool:
        return client in self._transactions

    def intercept(
        self, client, parsed_data, cmd_name
    ) -> ExecResult | SimpleString | RESPError | None:
        if cmd_name == "MULTI":
            self.start(client)
            return SimpleString("OK")

        if cmd_name == "EXEC":
            return self._execute(client)

        if cmd_name == "DISCARD":
            if self.is_in_transaction(client):
                self.discard(client)
                return SimpleString("OK")
            else:
                return RESPError("-ERR DISCARD without MULTI")

        if self.is_in_transaction(client):
            self.queue(client, parsed_data)
            return SimpleString("QUEUED")

        return

    def _execute(self, client) -> ExecResult:
        commands_input = self._transactions.get(client)
        results = []
        events = []

        if commands_input is None:
            return ExecResult(result=RESPError("-ERR EXEC without MULTI"))
        if commands_input == []:
            self.discard(client)
            return ExecResult(result=[])

        for command_input in commands_input:
            result = self._registry.execute(command_input)
            if isinstance(result, CommandResult):
                if result.event:
                    events.append(result.event.key)
                results.append(result.response)
            else:
                results.append(result)

        self.discard(client)
        return ExecResult(result=results, events=events)
