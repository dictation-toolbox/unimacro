"""actions from application code (Visual Studio)

getting the current line number!
"""
import time
from .actionbases import AllActions
from actions import doAction as action
from actions import doKeystroke as keystroke
import natlinkclipboard

class  CodeActions(AllActions):
    def __init__(self, progInfo):
        AllActions.__init__(self, progInfo)
        
    def getCurrentLineNumber(self, handle=None):
        t1 = time.time()
        if self.topchild == "child":
            return 0
        cb = natlinkclipboard.Clipboard(save_clear=True, debug=1)  # clear "debug" to get rid of timing line
        # via the command palette:
        # action("{shift+ctrl+p}; copy current line to clipboard; {enter};")
          
        # better via a shortcut key, goto file, preferences, keyboard shortcuts
        # type copy current line number to clipboard
        # press ctrl+alt+c    (choose different keystroke and change in next line!!)
        shortcutkey = "{ctrl+alt+c}"
        keystroke(shortcutkey)
        
        # now collect the clipboard, at most waiting 10 intervals of 0.1 second.
        result = cb.get_text(waiting_interval=0.025, waiting_iterations=10)    # should be the current line number
        # print(f'result from clipboard: {result}')
        t2 = time.time()
        lapse = t2 - t1
        print(f'time in getCurrentLineNumber: {lapse:.3f}')
        try:
            return int(result)
        except (ValueError, TypeError):
            return 0
        
    
if __name__ == '__main__':
    pass        
        