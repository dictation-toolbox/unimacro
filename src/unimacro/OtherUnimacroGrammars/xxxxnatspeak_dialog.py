#
# Python Macro Language for Dragon NaturallySpeaking
#   (c) Copyright 1999 by Joel Gould
#   Portions (c) Copyright 1999 by Dragon Systems, Inc.
#
# natspeak.py
#
# grammar activated if a recent folders dialog is brought to the foreground,
# interaction with grammar _folders.
#
#pylint:disable=
from dtactions import unimacroutils
from dtactions.sendkeys import sendkeys as keystroke
import unimacro.natlinkutilsbj as natbj



ancestor = natbj.IniGrammar
class ThisGrammar(ancestor):
    """grammar recent folder dialog
    
    only to be switched on if dialog is there, if dialog is gone, the grammar rules set is deactivated
    """    
    language = unimacroutils.getLanguage()
    name = "natspeak dialog"
    
    setRecentFolderDialog = ["chooserfd", "okcancelrfd"]
    
    gramSpec = """
<chooserfd> exported = choose {number};
<okcancelrfd> exported = OK | Cancel;
    """
    def initialize(self):
        if not self.language:
            print("no valid language in grammar "+__name__+" grammar not initialized")
            return
        self.load(self.gramSpec)
        print(f'loaded: {self.gramSpec}') 
        self.prevHndle = None

    def gotBegin(self,moduleInfo):
        """switch rfd (recent folders dialog) on
        
        if title matches what is provided in _folders grammar.
        """
        hndle = moduleInfo[2]
        if hndle == self.prevHndle:
            return
        self.prevHndle = hndle
        if unimacroutils.matchModule('natspeak'):
            # try to reach data from _folders grammar: 
            self.foldersGram = self.GetGrammarObject('folders')
            #print 'self.foldersGram: %s'% self.foldersGram
            if self.foldersGram is None:
                return
            dTitle = self.foldersGram.dialogWindowTitle
            dRange = self.foldersGram.dialogNumberRange
            if dTitle and unimacroutils.matchModule('natspeak', wantedTitle=dTitle, titleExact=1, caseExact=1):
                self.activateSet(self.setRecentFolderDialog)
                self.setNumbersList('number', dRange)
                return
        # other situations:
        self.deactivateAll()
        
    def gotResults_chooserfd(self, words, fullResults):
        """result from the recent folders dialog
        
        extract the number, then close the dialog and
        then call the relevant function from the folders grammar
        """
        wNumList = self.getNumbersFromSpoken(words) # returns a string or None
        if len(wNumList) != 1:
            print(f'natspeak dialog: error in command, no number found: {wNumList}')
            return
        chooseNum = wNumList[0]
        self.exitDialog()
        self.foldersGram.gotoRecentFolder(chooseNum-1)  # remember choose is 1 based, the list is 0 based 

    def gotResults_okcancelrfd(self, words, fullResults):
        print(f'dialog ok cancel: {words}, just close the dialog')
        self.exitDialog()

    def exitDialog(self):
        """finish the open dialog, normally by pressing enter"""
        dTitle = self.foldersGram.dialogWindowTitle
        if dTitle and unimacroutils.matchModule('natspeak', wantedTitle=dTitle, titleExact=1, caseExact=1):
            unimacroutils.rememberWindow()
            keystroke("{enter}") # exit dialog.
        unimacroutils.waitForNewWindow()
        
        
# standard stuff:
thisGrammar = ThisGrammar()
thisGrammar.initialize()

def unload():
    #pylint:disable=W0603
    global thisGrammar
    if thisGrammar:
        thisGrammar.unload()
    thisGrammar = None
