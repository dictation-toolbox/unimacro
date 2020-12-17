"""actions from application komodo

see www.activestate.com. Does not work yet for s&s or line numbers modulo 100
now special (QH) metaactions for very special tasks on selections of a file only
"""
import win32gui
import ctypes
import win32api
import messagefunctions as mf
from .actionbases import AllActions
import natlinkutils as natut
import natlinkutilsqh as natqh
import re

reSingleQuote = re.compile(r"(\'[^\']*\')")

# class KomodoActions(MessageActions):
class KomodoActions(AllActions):
    def __init__(self, progInfo):
        AllActions.__init__(self, progInfo)
        self.classname = "Komodo"
        
    def getInnerHandle(self, handle):
        # cannot get the correct "inner handle"
        return
        nextHndle = handle 
        user32 = ctypes.windll.user32
        #
        controls = mf.findControls(handle, wantedClass="Scintilla")
        print('Scintilla controls: %s'% controls)
        for c in controls:
            ln = self.getCurrentLineNumber(c)
            numberLines = self.getNumberOfLines(c)
            visible1 = self.isVisible(c)
            info = win32gui.GetWindowPlacement(c) 
            print('c: %s, linenumber: %s, nl: %s, info: %s'% (c, ln, numberLines, repr(info)))
            parent = c
            while 1:
                parent = win32gui.GetParent(parent)
                clName = win32gui.GetClassName(parent)
                visible = self.isVisible(parent)
                info = win32gui.GetWindowPlacement(parent) 
                print('parent: %s, class: %s, visible: %s, info: %s'% (parent, clName, visible, repr(info)))
                if parent == handle:
                    print('at top')
                    break
        
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

# several tries for getting introspection of the Komodo controls failed sofar (QH, October 2013) 
import ctypes
import win32con
def get_windows(startWith=None):
    '''Returns windows in z-order (top first)'''
    user32 = ctypes.windll.user32
    lst = []
    top = user32.GetTopWindow(startWith)
    if not top:
        return lst
    lst.append(top)
    next = top
    print('top: %s'% next)
    while True:
        
        next = user32.GetTopWindow(next)
        print('next: %s'% next)
        if not next:
            break
    #    lst.append(next)
    #return lst        
    
    
reSingleQuote = re.compile(r"(\'[^\']*\')")
reDoubleQuote = re.compile(r'(\"[^\"]*\")')
def replaceStringToUnicode(t):
    """prefix all occurrences of a string with an u prefix

    only in lines that do not start with >>> (doctest lines)
    catches first single or double quote, but no triple quotes

>>> replaceStringToUnicode(" hello ")
' hello '
>>> replaceStringToUnicode(" 'single quoted' ")
" u'single quoted' "
>>> replaceStringToUnicode('"double quoted"')
'u"double quoted"'
>>> replaceStringToUnicode(" ['single \\" quoted', \\"double ' quote\\"] ")
' [u\'single " quoted\', "double \' quote"] '    
    """
    Lines = t.split('\n')

    for i, line in enumerate(Lines):
        if line.find(">>>") >= 0:
            continue
        nsingle = line.find("'")
        ndouble = line.find('"')
        if nsingle >= 0:
            if ndouble == -1 or nsingle < ndouble:
                line = reSingleQuote.sub(r'u\1', line)
                Lines[i] = line
        elif ndouble >= 0:
            if nsingle == -1 or ndouble < nsingle:
                line = reDoubleQuote.sub(r'u\1', line)
                Lines[i] = line
        #else: equal and -1 so no quotes found...
            
    return '\n'.join(Lines)

def _test():
    """do doctests, for changing function
    """
    import doctest
    doctest.testmod()
    


if __name__ == '__main__':

    # focus =66284
    # 
    # print 'focus; %s'% focus
    # progInfo = ('komodo', 'babbababa', 'top', focus)
    # ka = KomodoActions( progInfo )
    # get_windows()
    #tw = mf.findTopWindows(wantedText="komodo")
    #for t in tw:
    #    print 't:%s'% t
    #    lst = get_windows(t)
    #    for l in lst:
    #        visible = win32gui.SendMessage(l, win32con.WS_VISIBLE)
    #        print 'l: %s, visible: %s'% (l, visible)
    ##    #pr
    ##    topchild = user32.GetTopWindow(t)
    ##    nextchild = user32.GetTopWindow(topchild)
    ##    print 'tophandle: %s, topchild: %s, nextchild: %s'% (t, topchild, nextchild)
    ##    
    #    pprint.pprint( mf.dumpWindow(t) )
    #    print '----------------------------------------------------------'        
    #
    _test()