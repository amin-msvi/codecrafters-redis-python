from app.resp_parser import RESPError

Handler = str | RESPError


def ping_handler(args: list):
    """
    PING [message]

    Returns:
        - "PONG" if no args
        - The message if provided
    """

    if len(args) == 0:
        return "PONG"
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


COMMAND_HANDLER = {
    "PING": ping_handler,
    "ECHO": echo_handler,
}


def handle_command(command: list) -> Handler:
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
