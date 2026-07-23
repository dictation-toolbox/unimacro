"""Unimacro __init__


Note there will be a global variable created in the unimacro module 'ulogger' which is Logging.Logger object named 'natlink.unimacro'
You can always access it by name.  It is created in _control.py.

"""

from logging import Logger
from logging import getLogger as __get_logger__
import importlib.metadata
__version__ = importlib.metadata.version(__package__)  #version set in pyproject.toml now.


def logname() -> str:
    """ Returns the name of the unimacro logger."""
    return "natlink.unimacro"

def logger() -> Logger:
    return __get_logger__(logname())