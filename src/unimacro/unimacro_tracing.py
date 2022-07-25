#Copyright Ben Staniford (ben@staniford.net)
#I do not know status of this presently (Quintijn)
import natlink
from natlink.natlinkutils import *

import re

#globally sets trace level, (0=Off, 1=Info, 2=Warnings, 3=tracing, 4=everything/method entry/exit)
global_tracing = 4

#set's tracing on for all the modules (individual grammars contain their own trace variables)
module_tracing = 1

#These are constants that are used within the unimacro source 
INFO=1
WARNING=2
TRACING=3
METHOD_ENTRY_EXIT=4

#Will make trace entry in the trace file
# Params:
# caller = the module/class calling the trace file
# trcinfo = a string containing the trace message
# level = 1/2/3 (1=Info, 2=Warnings, 3=tracing, 4=method calls)
def trace(caller, trcinfo, level, mode="macro"):
    try:
        import time
        global global_tracing
        if global_tracing>=level:
            if (caller=="unload"):
                pass
            elif (caller.tracing==0):
                return
            elif (mode=="utils"):
                if module_tracing==0:
                    return
            starttime=time.strftime("%H:%M:%S-- ", time.localtime())
            trcfile = open('c:/temp/unimacro.trc', 'a')
            if (mode=="utils"):
                trcfile.write(str(starttime) + "UTILS MOD CALLED BY: " + str(caller) + "::::")
            else:
                trcfile.write(str(starttime) + str(caller) + "::::")
                trcfile.write(trcinfo+"\n")
            trcfile.close()
    except AttributeError:
        starttime=time.strftime("%H:%M:%S-- ", time.localtime())
        trcfile = open('c:/temp/unimacro.trc', 'a')
        trcfile.write(str(starttime) + str(caller) + "::::")
        trcfile.write(trcinfo+"\n")
        trcfile.close()
