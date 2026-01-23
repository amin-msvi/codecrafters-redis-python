from app.resp_parser import RESPError
from app.data_store import DataStore
from app.utils import get_expiry

Handler = str | RESPError

data_store = DataStore()


class SimpleString:
    def __init__(self, s: str):
        self.s = s


def ping_handler(args: list) -> SimpleString | RESPError:
    """
    PING [message]

    Returns:
        - "PONG" if no args
        - The message if provided
    """

    if len(args) == 0:
        return SimpleString(s="PONG")
    elif len(args) == 1:
        return args[0]
    else:
        return RESPError("wrong number of arguments for 'ping' command")


def echo_handler(args: list):
    """
    ECHO message

    Returns the message.
    """
    if len(args) != 1:
        return RESPError("wrong number of arguments for 'echo' command")
    return args[0]


def get_handler(args: list):
    """
    GET a value for a key

    Returns: value
    """
    if len(args) != 1:
        return RESPError("Wrong number of argument for 'get' command")
    return data_store.get(args[0])


def set_handler(args: list):
    """
    SET a key-value pair in DataStore.
    Example: ['mykey', 10, 'eX', 10]

    Returns 'OK' (simple string) if successful
    """
    if len(args) < 2:
        return RESPError("wrong number of argument for 'set' command")
    data_store.set(key=args[0], value=args[1], expiry_ms=get_expiry(args))
    return SimpleString(s="OK")


COMMAND_HANDLER = {
    "PING": ping_handler,
    "ECHO": echo_handler,
    "SET": set_handler,
    "GET": get_handler,
}


def handle_command(command: tuple | None) -> Handler:
    """
    Takes: ["ECHO", "hey"]
    Returns "hey" (or RESPError for errors)
    """

    if not command:
        return RESPError("empty command")

    cmd_name = command[0].upper()
    args = command[1:]
    handler = COMMAND_HANDLER.get(cmd_name)
    if handler is None:
        return RESPError(f"unknown command '{command[0]}'")
    return handler(args)
