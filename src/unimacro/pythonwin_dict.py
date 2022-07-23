# Python Macro Language for Dragon NaturallySpeaking
#   (c) Copyright 1999 by Joel Gould
#   Portions (c) Copyright 1999 by Dragon Systems, Inc.
#
# Pythonwin, trying things with dication grammar, only seems to work when
# exclusively activated.
#
# Use testDialogForDicationGrammar.py (run from pythonwin), to start the window
# which accepts dictation from this grammar
#
# dictated text is inserted in front of text that is already there
#
# written by: Quintijn Hoogenboom (QH software, training & advies), june 2006
#
#
"""
try with title "Title" (from testDialogForDicationGrammar.py) or
               "Script" having a new (non saved python script)
"""
import natlink
from natlinkcore import natlinkutils
import win32ui
import nsformat

dictObj = None
debugMode = 1
##wantedTitle = "PythonWin - [Script1]" 
wantedTitle = "Title" # belonging to testDialogForDicationGrammar

class VoiceDictation:
    dictObj = None
    ctrl = None
    # Initialization.  Create a DictObj instance and activate it for the
    # dialog box window.  All callbacks from the DictObj instance will go
    # directly to the dialog box.

    def initialize(self, hndle=None):
        if self.dictObj != None:
            D("dictObj already initialized")
            return
        self.__class__.dictObj = natlink.DictObj()
        Cwnd = win32ui.GetForegroundWindow()
        for i in range(15000, 16000):
            try:
                ctrl = Cwnd.GetDlgItem(i)  # edit box
            except:
                pass
            else:
                D("got ctrl: %s: %s"% (i, ctrl))
                self.__class__.ctrl = ctrl
                break
        else:
            D("could not find a ctrl")
            self.__class__.ctrl = None
        self.dictObj.setBeginCallback(self.onTextBegin)
        self.dictObj.setChangeCallback(self.onTextChange)
        self.dictObj.activate(hndle)
##        self.dictObj.activate(dlg.GetSafeHwnd())


    def onTextBegin(self,moduleInfo):
        D('win dict, text begin')
        self.updateState()

    # We get this callback when something in the dictation object changes
    # like text is added or something is selected by voice.  We then update
    # the edit control to match the dictation object.

    def onTextChange(self,delStart,delEnd,newText,selStart,selEnd):
        D('win dict, text change:%s, %s, %s, %s, %s'% ( delStart, delEnd, newText, selStart, selEnd))
        self.dictObj.setLock(1)
        if self.ctrl:
            self.ctrl.SetSel(delStart,delEnd)
            self.ctrl.ReplaceSel(newText)
            self.ctrl.SetSel(selStart,selEnd)
        else:
            natlinkutils.playString(newText)
        self.dictObj.setLock(0)

    def updateState(self):
        if self.ctrl:
            D("ctrl")
            text = self.ctrl.GetWindowText()
            selStart,selEnd = self.ctrl.GetSel()
        else:
            D("fake text")
            text = "aa bb cc dd"
            selStart, selEnd = len(text), len(text)

        visStart,visEnd = self.getVisibleRegion()
        if (visStart, visEnd) == (None, None):
            visStart, visEnd = selStart, selEnd
        self.dictObj.setLock(1)
        self.dictObj.setText(text,0,0x7FFFFFFF)
        self.dictObj.setTextSel(selStart,selEnd)
        self.dictObj.setVisibleText(visStart,visEnd)
        self.dictObj.setLock(0)
        D("dictObj set with text: %s"% text)

    def getWindowText(self):
        if self.ctrl:
            return self.ctrl.GetWindowText()
        else:
            return "aa bb cc"

    def getSel(self):
        if self.ctrl:
            return self.ctrl.GetSel()
        else:
            return 4, 5

        
    def getVisibleRegion(self):
        """Utility subroutine which calculates the visible region of the edit

         control and returns the start and end of the current visible region.
        """
        if self.ctrl:
            top,bottom,left,right = self.ctrl.GetClientRect()
            firstLine = self.ctrl.GetFirstVisibleLine()
            visStart = self.ctrl.LineIndex(firstLine)

            lineCount = self.ctrl.GetLineCount()
            lastLine = lineCount
            for line in range(firstLine+1,lineCount):
                charInLine = self.ctrl.LineIndex(line)
                left,top = self.ctrl.GetCharPos(charInLine)
                if top >= bottom:
                    break
                lastLine = line

            visEnd = self.ctrl.LineIndex(lastLine+1)
            if visEnd == -1:
                visEnd = len(self.ctrl.GetWindowText())
            return visStart,visEnd
        else:
            return None, None
    
    # Call this function to cleanup.  We have to reset the callback
    # functions or the object will not be freed.
        
    def terminate(self):
        if self.dictObj:
            self.dictObj.deactivate()
            self.dictObj.setBeginCallback(None)
            self.dictObj.setChangeCallback(None)
            self.__class__.dictObj = None
            self.__class__.ctrl = None

class CommandGrammar(natlinkutils.GrammarBase):

    gramSpec = """
        <OK> exported = OK | okay;
        <scratch> exported = scratch [that];
        <clear> exported = clear | start again;
    """

    def initialize(self):
        print('initializing/loading CommandGrammar belonging to Python dictatebox')
        self.load(self.gramSpec)
        self.state = None
        self.prevHandle = -1
        self.txt = None # becomes the text dialog
        # keep same as pythonwin_dict grammar:
        self.exclusive = 0 # test with 1 or 0!
        self.dictObj = VoiceDictation()

        
    def gotBegin(self,moduleInfo):
        winHandle = moduleInfo[2]
        if self.prevHandle == winHandle:
            return
        # terminate dictObj:
        self.dictObj.terminate()
        self.prevHandle = winHandle
        if natlinkutils.matchWindow(moduleInfo, 'pythonwin', wantedTitle):
            if not self.isActive():
                self.dictObj.initialize(hndle=winHandle)
                print('activate (exclusive: %s) Pythonwin command grammar with dictate box, handle: %s'% \
                      (self.exclusive, winHandle))
                self.activateAll(winHandle, exclusive=self.exclusive)
        elif self.isActive():
            print('deactivate Pythonwin command grammar with dictate box')
            self.dictObj.terminate()
            self.deactivateAll()
            self.txt = None

    def onTextBegin(self, param):
        print("ontextbegin: %s"% param)

    def gotResultsInit(self,words,fullResults):
        if not self.txt:
            Cwnd = win32ui.GetForegroundWindow()
            self.txt=Cwnd.GetDlgItem(15008)  # edit box

    def gotResults_OK(self, words, fullResults):
        print('heard command:  %s '% words)
        natlinkutils.playString("{tab}{enter}")

    def gotResults_scratch(self, words, fullResults):
        print('heard command:  %s '% words)
        i,j = self.txt.GetSel()
        if i < j:
            natlinkutils.playString("{backspace}")

    def gotResults_clear(self, words, fullResults):
        print('heard command:  %s '% words)
        self.txt.Clear()

##class DictGrammar(natlinkutils.DictGramBase):
##    def __init__(self):
##        natlinkutils.DictGramBase.__init__(self)
##
##    def initialize(self):
##        print 'initializing/loading DictGrammar!!'
##        self.load()
##        self.state = None
##        self.isActive = 0
##        self.prevHandle = -1
##        self.txt = None # becomes the text dialog
##        self.exclusive = 1  # test with 1 or 0!
##        self.totalText = ''
##        self.dictObj = VoiceDictation()
##
##        
##    def gotBegin(self,moduleInfo):
##        winHandle = moduleInfo[2]
##        if self.prevHandle == winHandle:
##            if self.dictObj:
##                self.onTextBegin()
##                
##            return
##        self.dictObj.terminate()
##        self.prevHandle = winHandle
##        if natlinkutils.matchWindow(moduleInfo, 'pythonwin', wantedTitle):
##            if not self.isActive:
##                if not self.dictObj:
##                    self.dictObj.initialize(ctrl=None, hndle=winHandle)
##
##                print 'activate (exclusive: %s) Pythonwin dictation grammar, handle: %s'% \
##                      (self.exclusive, winHandle)
##                self.activate(winHandle, exclusive=self.exclusive)
##                self.isActive = 1
##        elif self.isActive:
##            print 'deactivate Pythonwin dictation grammar'
##            if self.dictObj:
##                self.dictObj.terminate()
##            self.deactivate()
##            self.txt = None
##            self.isActive = 0
##
##
##    def gotResults(self, words):
##        self.numberOfLinesBelow = 3  # for s&s or printing
##        print 'heard dictation:  %s '% words
##        self.dictObj.setBeginCallback()
####        dir txt: ['Clear', 'Copy', 'CreateWindow', 'Cut', 'FmtLines',
####                  'GetFirstVisibleLine', 'GetLine', 'GetLineCount',
####                  'GetSel', 'LimitText', 'LineFromChar', 'LineIndex',
####                  'LineScroll', 'Paste', 'ReplaceSel', 'SetReadOnly', 'SetSel']
##        
####        for funcName in ['GetFirstVisibleLine', 'GetLine', 'GetLineCount',
####                     'LineIndex', 'LineFromChar']:
####            func = getattr(txt, funcName)
####            result = func()
####            print '%s: %s'% (funcName, result)
##        self.dictObj.onTextBegin()
##        
##        actualLine = txt.GetLine()
##        actualLineNumber = txt.LineFromChar()
##        ## with no selection on, the current line is txt.GetLine(), others are txt.GetLine(index)
##        ## the current line number = txt.LineFromChar()
##        ## in this example the visible region is shown, until maximum 3 lines below the current line
##        print 'current line: %s'% txt.GetLine()
##        print 'line index: %s'% txt.LineIndex()
##        print 'line fromchar: %s'% txt.LineFromChar()
##        print 'GetSel: %s, %s'% txt.GetSel()
##        maxLineNum = min(txt.GetLineCount(), actualLineNumber+self.numberOfLinesBelow)
##        for line in range(txt.GetFirstVisibleLine(), maxLineNum):
##            text = txt.GetLine(line)
##            print 'line %s: %s'% (line, text)
##            
##        actual,self.state = nsformat.formatWords(words,self.state)
##        txt.ReplaceSel(actual)
##        self.totalText += actual
        
def D(t):
    """debug text if debugMode is on"""
    if debugMode:
        print(t)
        


# standard stuff Joel (adapted for possible empty gramSpec, QH, unimacro)
dictGrammar = None
##dictGrammar = DictGrammar()
##dictGrammar.initialize()
cmdGrammar = CommandGrammar()
cmdGrammar.initialize()
print('cmdGrammar initialized')
##print 'dictGrammar initialized'

def unload():
    global dictGrammar, thisGrammar
    if dictGrammar:
        dictGrammar.unload()
    if cmdGrammar:
        cmdGrammar.unload()
