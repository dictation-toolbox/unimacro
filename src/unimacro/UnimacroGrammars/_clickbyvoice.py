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
#pylint:disable=C0209, W1203

"""
This commands grammar allows clicking by voice

It is a global grammar, that is activated as soon as one of the chromium browsers is
in the foreground 

"""
from logging import getLogger
from io import StringIO

import natlink
from unimacro import natlinkutilsbj as natbj

from dtactions import unimacroutils
from dtactions.unimacroactions import doAction as action
from dtactions.unimacroactions import doKeystroke  as keystroke
import unimacro

from io import StringIO
logger = unimacro.logger()
# use extension Click by Voice
visiblePause = 0.4



language = unimacroutils.getLanguage()




ancestor = natbj.IniGrammar
class ThisGrammar(ancestor):

    @classmethod
    def module() -> str:
        return __module__
       

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
<shownumbers> exported = ((show) [more] (numbers) [{additionalonoroff}]+) | ((numbers) {additionalonoroff}+) ;
<hidenumbers> exported = (hide) (numbers);
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
        self.ActiveHndle = None
        self.load(self.gramSpec)


       
    def gotBegin(self,moduleInfo):
        if not language:
            return
        if self.checkForChanges:
            self.prevHandle = None

        winHandle = moduleInfo[2]
        if not winHandle:
            self.warning(f'no window handle in {self.name}')
            return
        if self.prevHandle == winHandle:
            return
        self.prevHandle = winHandle
        progInfo = unimacroutils.getProgInfo(moduleInfo)
        self.debug('progInfo: %s',repr(progInfo))
        prog = progInfo.prog
        chromiumBrowsers = {'chromium', 'chrome', 'msedge', 'safari', 'brave'}
        if prog in chromiumBrowsers:
            if progInfo.toporchild == 'child':
                self.debug(f'in child window, of a clickbyvoice program {prog}')
            if self.checkForChanges:
                self.info(f'_clickbyvoice ({self.name}, prog: {prog}, checking the inifile')
                self.checkInifile()
            self.switchOnOrOff(window=winHandle)
            if not self.ActiveHndle == winHandle:
                self.info(f'activate _clickbyvoice, {prog}, hndle: {winHandle}')
                self.activateAll(window=winHandle)
                self.ActiveHndle = winHandle
        else:
            if self.isActive():
                self.info("deactivate _clickbyvoice")
                self.deactivateAll()
                self.ActiveHndle = False
                

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
        self.debug(f"__file__ {__file__} "  )
        self.debug( 'showhidenumbers, words: %s', words)
        showNumbers = ":+"  # fresh start, just in case
        if self.hasCommon(words, 'more'):
            showNumbers += "+"
            
        additionalOptions = False
        while 1:
            additional = self.getFromInifile(words[-1], 'additionalonoroff', noWarning=1)
            if additional is None:
                break
            if additional == '-':
                self.info(f'{self.name}: hide the numbers')
                self.gotResults_hidenumbers(words, fullResults)
                return
            words.pop() # remove last word of list.
            #allow duplicates (new behavior in 2024-12-08)
            #doesn't seem to harm anything and allows for appending a +
            showNumbers += additional 
            additionalOptions = True
                
        if additionalOptions:
            self.info(f'{self.name}: showNumbers command: {showNumbers}, set as new default for the current session.')
            # set new chosen string:
            # self.setInInifile("general", "show numbers", showNumbers)

        self.showNumbers = showNumbers
        self.getInputcontrol()
        self.doOption(showNumbers)
        self.debug('clickbyvoice, before finishInputControl')
        self.finishInputControl()
        self.debug('clickbyvoice, after finishInputControl')


    def gotResults_hidenumbers(self, words, fullResults):
        """hide the numbers

        """
        self.getInputcontrol()
        self.doOption(self.hideNumbers)
        self.finishInputControl()

    def gotResults_tabactions(self,words,fullResults):
        """do an actions to the current tab (doc)"""
        self.debug(f'tabactions words: {words}')
        command = self.getFromInifile(words, 'tabcommands')
            
        if command:
            action(command)

    def gotResults_numberedtabs(self,words,fullResults):
        """go to a numbered tab (doc) and do an optional action"""
        self.info(f'numberedtabs: {words}')
        command = self.getFromInifile(words, 'tabcommands')

        counts = self.getNumbersFromSpoken(words)
        if not counts:
            self.info(f'_clickbyvoice, numberedtabs, no valid tab number found: {words}')
            return
            
        if command:
            action(command)

    def gotResults_navigatetabs(self,words,fullResults):
        """go to next or previous tab(s) (documents) and refresh possibly"""
        self.info(f'navigate tabs: {words}')
        direction = None
        command = self.getFromInifile(words, 'tabcommands',noWarning=1)
        
        if self.hasCommon(words, ['next', 'verder', 'volgende', 'vooruit', 'forward']):
            direction = 'tab'
        elif self.hasCommon(words, ['previous', 'terug', 'vorige', 'back']):
            direction = 'shift+tab'
        else:
            self.info(f'no direction found in command: {words}')
        
        counts = self.getNumbersFromSpoken(words)
        if counts:
            count = counts[0]
        else:
            count = 1
##        print 'tabs:     direction: %s, count: |%s|, command: |%s|'% (direction, counlinker balkt, command)

        if direction:        
            while count > 0:
                count -= 1
                keys = '{ctrl+' + direction + '}'
                keystroke(keys)
                unimacroutils.Wait(0.5) #0.3 seem too short for going back tabs in chrome
            
        if command:
            action(command)

    def gotResults_navigatepages(self,words,fullResults):
        """go to next or previous page(s) and refresh possibly"""
##        print 'navigate pages: %s'% words
        ## not active at the moment, possibly reactivate...
        direction = None
        command = self.getFromInifile(words, 'pagecommands',noWarning=1)
        
        if self.hasCommon(words, ['next', 'verder', 'volgende', 'vooruit', 'forward']):
            direction= 'right'
        elif self.hasCommon(words, ['previous', 'terug', 'vorige', 'back']):
            direction= 'left'
        else:
            self.warning(f'no direction found in command: {words}')
        
        counts = self.getNumbersFromSpoken(words)
        if counts:
            count = counts[0]
        else:
            count = 1
##        print 'PAGES:     dir: %s, count: |%s|, command: |%s|'% (dir, counlinker balkt, command)

        if direction:        
            while count > 0:
                count= count -1
                keystroke('{alt+%s}'%(direction))
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
            self.debug('collected no number')
            return
        self.getInputcontrol()
        command = self.number
        commandparts = []
        if self.navOption:
            if not self.navOption.startswith(":"):
                command += ":"
            command += self.navOption
        if command.find(';') >= 0:
            self.debug(f'command: {command}')
            commandparts = command.split(';')
            command = commandparts.pop(0)
            self.debug(f'command: {command}, commandparts: {commandparts}')
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
            if progInfo.toporchild == 'child':
                if i:
                    self.info(f'found input window after {i} steps')
                break
            unimacroutils.Wait()
        else:

             self.warning("_clickbyvoice failed to reach input window")
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
        if self.showNumbers.find(":") != 0:
            if self.showNumbers.find(":") == -1:
                self.showNumbers = ":" + self.showNumbers
            else:
                self.warning(f'{self.name}, "+" sign missing in inifile, "general", "show numbers": "{self.showNumbers}", replace by default: ":+"')
                self.showNumbers = ":+"
        if self.showNumbers.find("+") != 1:
            self.warning('{self.name}, "+" sign missing or in wrong position in inifile, "general", "show numbers": "{self.showNumbers}", replace by default: ":+"')
            self.showNumbers = ":+"
        # not in inifile:
        self.hideNumbers = ":-"


#logger should be used instead of print
#replace print to avoid unintended use.
builtin_print=print
def our_print(*args,**kwargs):
    f=StringIO()
    builtin_print(args,kwargs,file=f)
    value=f.getvalue()  
    logger.debug("print called instead of logging functions: %s", value)
    logger.error(value)

# standard stuff Joel (adapted for possible empty gramSpec, QH, unimacro)
if __name__ == "__main__":
    ## interactive use, for debugging:
    with natlink.natConnect():
        try:
            thisGrammar = ThisGrammar(inifile_stem="_clickbyvoice")
            # thisGrammar.startInifile()
            thisGrammar.initialize()
            logger.debug('clickbyvoice, before finishInputControl')
            thisGrammar.finishInputControl()
            logger.debug('clickbyvoice, after finishInputControl')



        finally:
            thisGrammar.unload()
elif __name__.find('.') == -1:
    # standard startup when Dragon starts:
    thisGrammar = ThisGrammar()
    thisGrammar.initialize()

    
def unload():
    #pylint:disable=W0603
    global thisGrammar
    if thisGrammar:
        thisGrammar.unload()
    thisGrammar = None

