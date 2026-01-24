"""
Commands package.

Importing this module ensures all command classes are loaded,
which is necessary for auto-discovery to work
"""

# Import all command modules to register them
from app.commands.ping import PingCommand  # noqa: F401
from app.commands.echo import EchoCommand  # noqa: F401
from app.commands.get import GetCommand  # noqa: F401
from app.commands.set import SetCommand  # noqa: F401

# Export the registry for easy access
from app.commands.registry import CommandRegistry

__all__ = ["CommandRegistry"]
