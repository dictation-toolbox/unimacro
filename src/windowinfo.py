"""Extracts the threadinfo of the current thread. Can see if a menu
or popup is active

hasMenuOpen() gives true if menu (File, Edit, ...) is open or a right click
context menu is open.
hasPopupOpen() give true if a right click (context) menu is open.

getWindowFlags gives (as a tuple) the flags that are set in the guithreadinfo.flags variable.


Used for grammar kaiser_dictation.py in conjunction with unimacro grammars
(qh.antenna.nl/unimacro). Quintijn Hoogenboom, december 2009
"""

from ctypes import *
import types
user32 = windll.user32
kernel32 = windll.kernel32
import time
class RECT(Structure):
 _fields_ = [
     ("left", c_ulong),
     ("top", c_ulong),
     ("right", c_ulong),
     ("bottom", c_ulong)
 ]

class GUITHREADINFO(Structure):
 _fields_ = [
     ("cbSize", c_ulong),
     ("flags", c_ulong),
     ("hwndActive", c_ulong),
     ("hwndFocus", c_ulong),
     ("hwndCapture", c_ulong),
     ("hwndMenuOwner", c_ulong),
     ("hwndMoveSize", c_ulong),
     ("hwndCaret", c_ulong),
     ("rcCaret", RECT)
 ]

def moveCursorInCurrentWindow(x, y):
 # Find the focussed window.
    guiThreadInfo = GUITHREADINFO(cbSize=sizeof(GUITHREADINFO))
    user32.GetGUIThreadInfo(0, byref(guiThreadInfo))
    focussedWindow = guiThreadInfo.hwndFocus

    # Find the screen position of the window.
    windowRect = RECT()
    user32.GetWindowRect(focussedWindow, byref(windowRect))

    # Finally, move the cursor relative to the window.
    user32.SetCursorPos(windowRect.left + x, windowRect.top + y)

def hasMenuOpen():
    guiThreadInfo = GUITHREADINFO(cbSize=sizeof(GUITHREADINFO))
    user32.GetGUIThreadInfo(0, byref(guiThreadInfo))
    flags = guiThreadInfo.flags
    menuOpen = 4
    return (flags & menuOpen) == menuOpen

def hasPopupOpen():
    guiThreadInfo = GUITHREADINFO(cbSize=sizeof(GUITHREADINFO))
    user32.GetGUIThreadInfo(0, byref(guiThreadInfo))
    flags = guiThreadInfo.flags
    popupOpen = 16
    return (flags & popupOpen == popupOpen)
    
def getWindowFlags():
    guiThreadInfo = GUITHREADINFO(cbSize=sizeof(GUITHREADINFO))
    user32.GetGUIThreadInfo(0, byref(guiThreadInfo))
    return flagsToTuple(guiThreadInfo.flags)
    
def flagsToTuple(flags):
    """convert a flags int into a set of flags
    """
    if flags == None:
        return ()
    elif flags == 0:
        return ()
    Flags = []
    if type(flags) in (int, int):
        if type(flags) == int: n = 32
        elif type(flags) == int: n = 64
        else:
            raise ValueError('type should be "int" or "long" here, not: %s'% type(flags))
        if flags:
            for i in range(n):
                if flags & (1<<i):
                    Flags.append(i)
            else:
                pass # flags == 0
    elif type(flags) in (tuple, list):
        Flags = flags
    else:
        print('type flags: %s'% type(flags))
        Flags = flags
    return tuple(Flags)

#GUI_CARETBLINKING = 1
#GUI_INMOVESIZE = 2
#GUI_INMENUMODE = 4
#GUI_SYSTEMMENUMODE = 8
#GUI_POPUPMENUMODE = 16
    

if __name__ == '__main__':
    # Quick test.
    #moveCursorInCurrentWindow(200, 200)
    # should return False:
    time.sleep(1)
    print('hasMenuOpen: %s'% hasMenuOpen())
    print('hasPopupOpen: %s'% hasPopupOpen())
    print('flags: %s'% repr(getWindowFlags()))