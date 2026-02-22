from app.commands.ping import PingCommand
from app.commands.echo import EchoCommand
from app.commands.get import GetCommand
from app.commands.set import SetCommand
from app.commands.rpush import RPushCommand
from app.commands.lrange import LRangeCommand
from app.commands.lpush import LPushCommand
from app.commands.llen import LLenCommand
from app.commands.lpop import LPopCommand
from app.commands.blpop import BLPopCommand
from app.commands.type import TypeCommand
from app.commands.xadd import XaddCommand
from app.commands.xrange import XRangeCommand
from app.commands.xread import XReadCommand
from app.commands.incr import IncrCommand
from app.commands.info import InfoCommand
from app.commands.replconf import ReplConfCommand
from app.commands.psync import PSyncCommand
from app.commands.wait import WaitCommand

from app.commands.registry import CommandRegistry

__all__ = ["CommandRegistry"]
