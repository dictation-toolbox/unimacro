"""actions from application komodo

see www.activestate.com. Does not work yet for s&s or line numbers modulo 100
now special (QH) metaactions for very special tasks on selections of a file only
"""
import win32gui
import ctypes
import win32api
import messagefunctions as mf
from .actionbases import AllActions
from actions import doAction as action
from actions import doKeystroke as keystroke
import natlinkclipboard
import time


# class KomodoActions(MessageActions):
class KomodoActions(AllActions):
    def __init__(self, progInfo):
        AllActions.__init__(self, progInfo)
        self.classname = "Komodo"
        
    # def getInnerHandle(self, handle):
    #     # cannot get the correct "inner handle"
    #     return
    #     nextHndle = handle 
    #     user32 = ctypes.windll.user32
    #     #
    #     controls = mf.findControls(handle, wantedClass="Scintilla")
    #     print('Scintilla controls: %s'% controls)
    #     for c in controls:
    #         ln = self.getCurrentLineNumber(c)
    #         numberLines = self.getNumberOfLines(c)
    #         visible1 = self.isVisible(c)
    #         info = win32gui.GetWindowPlacement(c) 
    #         print('c: %s, linenumber: %s, nl: %s, info: %s'% (c, ln, numberLines, repr(info)))
    #         parent = c
    #         while 1:
    #             parent = win32gui.GetParent(parent)
    #             clName = win32gui.GetClassName(parent)
    #             visible = self.isVisible(parent)
    #             info = win32gui.GetWindowPlacement(parent) 
    #             print('parent: %s, class: %s, visible: %s, info: %s'% (parent, clName, visible, repr(info)))
    #             if parent == handle:
    #                 print('at top')
    #                 break
    def getCurrentLineNumber(self, handle=None):
        debug = 0
        t1 = time.time()
        if self.topchild == "child":
            return 0
        cb = natlinkclipboard.Clipboard(save_clear=True, debug=debug)  # clear "debug" to get rid of timing line
        shortcutkey = "{alt+shift+n}{ctrl+c}"
        keystroke(shortcutkey)
        
        # # now collect the clipboard, at most waiting 10 intervals of 0.1 second.
        result = cb.get_text(waiting_interval=0.01, waiting_iterations=10)    # should be the current line number
        # print(f'result from clipboard: {result}')
        t2 = time.time()
        lapse = t2 - t1
        if debug:
            print(f'time in getCurrentLineNumber: {lapse:.3f}')
        try:
            return int(result)
        except (ValueError, TypeError):
            return 0

    def metaaction_gotolinetemp(self, linenum, handle=None):
        print("starting metaaction gotoline")
        debug = 0
        t1 = time.time()
        if self.topchild == "child":
            return 0
        cb = natlinkclipboard.Clipboard(save_clear=True, debug=debug)  # clear "debug" to get rid of timing line
        cb.set_text(str(linenum))  ## this one needs testing in natlinkclipboard TODOQH
        time.sleep(0.5)
        shortcutkey = "{alt+shift+n}{ctrl+g}"
        keystroke(shortcutkey)
        
        # # now collect the clipboard, at most waiting 10 intervals of 0.1 second.
        result = cb.get_text(waiting_interval=0.01, waiting_iterations=10)    # should be the current line number
        print(f'result gotoline: {result}')
        # print(f'result from clipboard: {result}')
        t2 = time.time()
        lapse = t2 - t1
        if debug:
            print(f'time in gotoline: {lapse:.3f}')

        
    def metaaction_makeunicodestrings(self, dummy=None):
        """for doctest testing, put u in front of every string
        """
        print('metaaction_makeunicodestrings, for Komodo')
        natut.playString("{ctrl+c}")
        t = natqh.getClipboard()
        print('in: %s'% t)
        t = replaceStringToUnicode(t)
        natqh.setClipboard(t)
        natut.playString("{ctrl+v}{down}")

def _test():
    """do doctests, for changing function
    """
    import doctest
    doctest.testmod()
    
