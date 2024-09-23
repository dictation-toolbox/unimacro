"""Unimacro __init__


Note there will be a global variable created in the unimacro module 'ulogger' which is Logging.Logger object named 'natlink.unimacro'
You can always access it by name.  It is created in _control.py.

"""
import os
import sys

import importlib.metadata
__version__ = importlib.metadata.version(__package__)  #version set in pyproject.toml now.

def folders_logger_name() -> str:
    return "natlink.unimacro.folders"

def control_logger_name() -> str : 
    return "natlink.unimacro.control"

def logname() -> str:
    """ Returns the name of the unimacro logger."""
    return "natlink.unimacro"

