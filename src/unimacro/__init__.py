"""Unimacro __init__


Note there will be a global variable created in the unimacro module 'ulogger' which is Logging.Logger object named 'natlink.unimacro'
You can always access it by name.  It is created in _control.py.

"""
import os
import sys

__version__ = '4.1.6'   # requires the dtactions 1.5.5, with new sendkeys (from send_input, vocola)   
#they could be in a seperate .py file in unimacro to achieve the same (ie not in the control grammar).
#these will possilby be removed since we may not need them to enumerate the grammars and ask for log names.

def folders_logger_name() -> str:
      return "natlink.unimacro.folders"

def control_logger_name() -> str : 
        return "natlink.unimacro.control"

def logname() -> str:
    """ Returns the name of the unimacro logger."""
    return "natlink.unimacro"
 
