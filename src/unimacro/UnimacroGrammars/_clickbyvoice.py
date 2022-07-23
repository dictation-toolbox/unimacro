# This file is part of a SourceForge project called "unimacro" see
# http://unimacro.SourceForge.net and http://qh.antenna.nl/unimacro
# (c) copyright 2003 see http://qh.antenna.nl/unimacro/aboutunimacro.html
#    or the file COPYRIGHT.txt in the natlink\natlink directory 
#
# from April 2020 in GitHub Dictation-toolbox Unimacro
#
# Mouseless Browsing extension from Rudolf Noe (mode = "mlb") is discarded
#
# only clickbyvoice, which is present in all browsers that are chromium compatible
# chrome, safari, brave, edge (Microsoft Edge) etc.
#
# 
#
# written by: Quintijn Hoogenboom (QH software, training & advies)
#
# the lists {n1-9}, {n1-20} are constructed in internal grammar functions
#
# the lists {pagecommands} and {tabcommands} in the inifile (edit chrome hah)
#
"""
This commands grammar allows clicking by voice

It is a global grammar, that is activated as soon as one of the chromium browsers is
in the foreground 

"""


import natlink
from dtactions.unimacro import unimacroutils
from natlinkcore import natlinkutils as natut
from dtactions.unimacro import unimacroutils
import unimacro.natlinkutilsbj as natbj
from dtactions.unimacro.unimacroactions import doAction as action
from dtactions.unimacro.unimacroactions import doAction as action

# use extension Click by Voice
visiblePause = 0.4

language = unimacroutils.getLanguage()

ancestor = natbj.IniGrammar
class ThisGrammar(ancestor):

    try:
        numberGram = natbj.numberGrammarTill999[language]
    except KeyError:
        print('take number grammar from "enx"')
        numberGram = natbj.numberGrammarTill999['enx']
        
    if language == "nld":
        name = 'Click by voice'
    else:
        name = 'Click by voice'

    gramSpec = """
<shownumbers> exported = ((show) (numbers) [{additionalonoroff}]+) | ((numbers) {additionalonoroff}+) ;
<hidenumbers> exported = (hide) (numbers) [after {n1-20}];
<picknumber> exported = (pick) <integer> [{navigateoptions}];

# is already in _tasks grammar:
# <navigatetabs> exported = ((next|previous) tab) [{n1-20} | {tabcommands}]|
#                            (tab (back|forward) [{n1-20} | {tabcommands}]);
# <numberedtabs> exported = tab {n1-n20} [{tabcommands}];
# <tabactions> exported = tab {tabcommands};


<navigatepages> exported = ((next|previous|{pagecommands}) page)|
                            (page (back|forward) [{n1-20}]) |
                            page {pagecommands} |
                            (next|previous) page {pagecommands};
#and the numbers grammar (0,...,999 or chain of digits):                             
"""+numberGram
        
    def initialize(self):
        self.prevHandle = -1
        self.load(self.gramSpec)

    def gotBegin(self,moduleInfo):
        if not language: return
        if self.checkForChanges:
            self.prevHandle = None

        winHandle = moduleInfo[2]
        if not winHandle:
            print('no window handle in %s'% self.name)
            return
        if self.prevHandle == winHandle:
            return
        self.prevHandle = winHandle
        progInfo = unimacroutils.getProgInfo(moduleInfo)
        # print('progInfo: %s'% repr(progInfo))
        prog = progInfo.prog
        chromiumBrowsers = {'chromium', 'chrome', 'msedge', 'safari', 'brave'}
        if prog in chromiumBrowsers:
            if progInfo.topchild == 'child':
                print('in child window, the clickbyvoice window?')
            if self.checkForChanges:
                print('_clickbyvoice (%s), prog: %s, checking the inifile'% (self.name, prog))
                self.checkInifile()
            self.switchOnOrOff(window=winHandle)
            if not self.isActive == winHandle:
                print("activate _clickbyvoice, %s, %s"% (prog, winHandle))
                self.activateAll(window=winHandle)
                self.isActive = winHandle
        else:
            if self.isActive:
                print("deactivate _clickbyvoice")
                self.deactivateAll()
                self.isActive = False
                

    def gotResultsInit(self,words,fullResults):
        """at start of actions"""
        self.number = ''
        self.navOption = ''   # eg left or right (s or o)hallo
        self.hadPick = False

    def gotResults_picknumber(self, words, fullResults):
        """start the collecting of the wanted number
        """
        if self.hasCommon(words[0], 'pick'):
            self.waitForNumber('number')
            self.hadPick = True
        else:
            self.navOption = self.getFromInifile(words[-1], 'navigateoptions')
            
    def gotResults_shownumbers(self, words, fullResults):
        """show the numbers, with additional options

        """
        # print 'showhidenumbers, words: %s'% words
        showNumbers = ":+"  # fresh start, just in case
        additionalOptions = False
        while 1:
            additional = self.getFromInifile(words[-1], 'additionalonoroff', noWarning=1)
            if additional is None: break
            if additional == '-':
                print('%s: hide the numbers'% self.name)
                self.gotResults_hidenumbers(words, fullResults)
                return
            words.pop() # remove last word of list.
            if additional in showNumbers:
                pass
            else:
                showNumbers += additional 
                additionalOptions = True
                
        if additionalOptions:
            print('%s: showNumbers command: %s, set as new default for the current session.'% (self.name, showNumbers))
            # set new chosen string:
            # self.setInInifile("general", "show numbers", showNumbers)

        self.showNumbers = showNumbers
        self.getInputcontrol()
        self.doOption(showNumbers)
        self.finishInputControl()
        

    def gotResults_hidenumbers(self, words, fullResults):
        """hide the numbers

        """
        wordFound, position = self.hasCommon(words, "after", withIndex=True)
        if wordFound:
            print("setting timer later")
        
        self.getInputcontrol()
        self.doOption(self.hideNumbers)
        self.finishInputControl()

    def gotResults_tabactions(self,words,fullResults):
        """do an actions to the current tab (doc)"""
        # print(f'tabactions words: {words}')
        command = self.getFromInifile(words, 'tabcommands')
            
        if command:
            action(command)

    def gotResults_numberedtabs(self,words,fullResults):
        """go to a numbered tab (doc) and do an optional action"""
        print(f'numberedtabs: {words}')
        command = self.getFromInifile(words, 'tabcommands')

        counts = self.getNumbersFromSpoken(words)
        if not counts:
            print(f'_clickbyvoice, numberedtabs, no valid tab number found: {words}')
            return
            
        if command:
            action(command)

    def gotResults_navigatetabs(self,words,fullResults):
        """go to next or previous tab(s) (documents) and refresh possibly"""
        print(f'navigate tabs: {words}')
        dir = None
        command = self.getFromInifile(words, 'tabcommands',noWarning=1)
        
        if self.hasCommon(words, ['next', 'verder', 'volgende', 'vooruit', 'forward']):
            dir = 'tab'
        elif self.hasCommon(words, ['previous', 'terug', 'vorige', 'back']):
            dir = 'shift+tab'
        else:
            print(f'no direction found in command: {words}')
        
        counts = self.getNumbersFromSpoken(words)
        if counts:
            count = counts[0]
        else:
            count = 1
##        print 'tabs:     dir: %s, count: |%s|, command: |%s|'% (dir, counlinker balkt, command)

        if dir:        
            while count > 0:
                count -= 1
                keys = '{ctrl+' + dir + '}'
                keystroke(keys)
                unimacroutils.Wait(0.5) #0.3 seem too short for going back tabs in chrome
            
        if command:
            action(command)

    def gotResults_navigatepages(self,words,fullResults):
        """go to next or previous page(s) and refresh possibly"""
##        print 'navigate pages: %s'% words
        ## not active at the moment, possibly reactivate...
        dir = None
        command = self.getFromInifile(words, 'pagecommands',noWarning=1)
        
        if self.hasCommon(words, ['next', 'verder', 'volgende', 'vooruit', 'forward']):
            dir = 'right'
        elif self.hasCommon(words, ['previous', 'terug', 'vorige', 'back']):
            dir = 'left'
        else:
            print('no direction found in command: %s'% words)
        
        counts = self.getNumbersFromSpoken(words)
        if counts:
            count = counts[0]
        else:
            count = 1
##        print 'PAGES:     dir: %s, count: |%s|, command: |%s|'% (dir, counlinker balkt, command)

        if dir:        
            while count > 0:
                count= count -1
                keystroke('{alt+%s}'%(dir))
                unimacroutils.Wait(0.5) #0.3 seem too short for going back pages in chrome
            
        if command:
            action(command)


    def gotResults(self,words,fullResults):
    
        # step 5, in got results collect the number:
        # only necessary in this grammar for collecting the choose command
        if not self.hadPick:
            return
        self.collectNumber()
        if not self.number:
            print('collected no number')
            return
        self.getInputcontrol()
        command = self.number
        commandparts = []
        if self.navOption:
            if not self.navOption.startswith(":"):
                command += ":"
            command += self.navOption
        if command.find(';') >= 0:
            print('command: %s'% command)
            commandparts = command.split(';')
            command = commandparts.pop(0)
            print('command: %s, commandparts: %s'% (command, commandparts))
        self.doOption(command)
        for additional in commandparts:
            unimacroutils.Wait(visiblePause)
            keystroke(additional)
        self.finishInputControl()
        
        
        
    def getInputcontrol(self):
        """get the Click by Voice input control"""
        keystroke("{shift+ctrl+space}")
        unimacroutils.Wait()   ## longer: unimacroutils.Wait(visiblePause)
        for i in range(10):
            progInfo = unimacroutils.getProgInfo()
            if progInfo.topchild == 'child':
                if i: print('found input window after %s steps'% i)
                break
            unimacroutils.Wait()
        else:
            print("_clickbyvoice failed to reach input window")
        # print("found input window of clickbyvoice")
        unimacroutils.visibleWait()
        
        
    def doOption(self, option):
        """after the inputcontrol is focussed, do the command"""
        keystroke(option)

    def finishInputControl(self):
        """press enter, after a little bit of waiting
        """
        unimacroutils.visibleWait()
        unimacroutils.visibleWait()
        keystroke("{enter}")
        
    def fillInstanceVariables(self):
        """fills the necessary instance variables

        """
        self.showNumbers = self.ini.get('general', 'show numbers') or ':+'
        if not self.showNumbers.find(":") == 0:
            if self.showNumbers.find(":") == -1:
                self.showNumbers = ":" + self.showNumbers
            else:
                print('%s, "+" sign missing in inifile, "general", "show numbers": "%s", replace by default: "%s"'% (self.name, self.showNumbers, ":+"))
                self.showNumbers = ":+"
        if self.showNumbers.find("+") != 1:
            print('%s, "+" sign missing or in wrong position in inifile, "general", "show numbers": "%s", replace by default: "%s"'% (self.name, self.showNumbers, ":+"))
            self.showNumbers = ":+"
        # not in inifile:
        self.hideNumbers = ":-"



# standard stuff Joel (adapted for possible empty gramSpec, QH, unimacro)
thisGrammar = ThisGrammar()
if thisGrammar.gramSpec:
    thisGrammar.initialize()
else:
    thisGrammar = None
    
def unload():
    #pylint:disable=W0603
    global thisGrammar
    if thisGrammar: thisGrammar.unload()
    thisGrammar = None

