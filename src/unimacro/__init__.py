"""Unimacro __init__


Note there will be a global variable created in the unimacro module 'ulogger' which is Logging.Logger object named 'natlink.unimacro'
You can always access it by name.  It is created in _control.py.

"""
import os
import sys

#these functions are in this module so that they can be loaded without loading a lot of unimacro code.
#they could be in a seperate .py file in unimacro to achieve the same (ie not in the control grammar).

def control_logger_name() -> str : 
        return "natlink.unimacro.control"

def logname() -> str:
    """ Returns the name of the unimacro logger."""
    return "natlink.unimacro"
__version__ = '4.1.4.2'   
 
