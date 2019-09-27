__version__ = "$Revision: 351 $, $Date: 2011-01-10 17:20:10 +0100 (ma, 10 jan 2011) $, $Author: quintijn $"
############################################################################
#
# global Python grammar file: _setpriority.py
import win32con,win32api,win32process
#
# This file is loaded automatically when the Python subsystem starts because
# its filename begins with an underscore (the signal for a global module).
#
# Its only goal is to change the process priority of Natspeak to :
desiredPClass = win32process.HIGH_PRIORITY_CLASS # (define new priority here)
# upon start of the system, and display the change in the message window.
#
# If you don't want to see the change notification in case of succes,
# set the following constant to zero
displayResults = 0
#
# This scripts appears to work for DNS4 and 5, under NT 4 and NT 2000.
# It is assumed that the macro system is run under the process control of NatSpeak,
# and the user has enough rights to change the priority of the process.
#
# Author: B.J. van Os


def GetPriorityClassName(pClass):
     if pClass==win32process.HIGH_PRIORITY_CLASS:
         return 'HIGH'
     elif pClass==win32process.NORMAL_PRIORITY_CLASS:
         return 'NORMAL'
     elif pClass==win32process.IDLE_PRIORITY_CLASS:
         return 'IDLE'
     elif pClass==win32process.REALTIME_PRIORITY_CLASS:
         return 'REAL'
     elif pClass==win32process.ABOVE_NORMAL_PRIORITY_CLASS:
         return 'ABOVE NORMAL'
     elif pClass==win32process.BELOW_NORMAL_PRIORITY_CLASS:
         return 'BELOW NORMAL'


id = win32api.GetCurrentProcessId()
h  = win32api.OpenProcess(win32con.PROCESS_ALL_ACCESS,0,id)
oldPClass = win32process.GetPriorityClass(h)

if displayResults: print 'Current Process Priority = ',GetPriorityClassName(oldPClass)

if oldPClass == desiredPClass:
     if displayResults: print 'WARNING: Current Process already has desired priority!'
else:
     win32process.SetPriorityClass(h,desiredPClass)
     newPClass=win32process.GetPriorityClass(h)
     if oldPClass==newPClass:
         print 'WARNING: Change of process priority failed!'
     else:
         if displayResults: print 'New Process Priority     = ',GetPriorityClassName(newPClass)
