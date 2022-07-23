# This file is part of a SourceForge project called "unimacro" see
# http://unimacro.SourceForge.net and http://qh.antenna.nl/unimacro
# (c) copyright 2003 see http://qh.antenna.nl/unimacro/aboutunimacro.html
#    or the file COPYRIGHT.txt in the natlink\natlink directory 
#
# _lines.py 
#  written by: Quintijn Hoogenboom (QH software, training & advies)
#  August 2003
#  add column: 23/4/2018
#

"""lines can be selected, with or without line number, copied, moved etc

In the second part of the command, also be triggered by "THAT", an appropriate action can be performed.

Examples: "Line copy", "Line 34", "Line 343 select", "Line 2 Through 5", 
"Line 15 Plus 3 Duplicate",  etc

More elaborate actions are: "Line 3 Move To 6", "Line 3 Through 7 Copy To 10", "Line 5 Move Up 2", "Line 10 Plus 2 Copy Down 10".

If you want to separate the selection and the action you can first say for example: "Line 11 Through 15" and as action "That Copy Up 3". 

If you use the Through part with a lower number, the next higher possible number is calculated, for example "Line 23 Through 5" means "Line 23 Through 25" and
"Line 98 Through 23" means "Line 98 Through 123".


All selection and action stuff is performed in the gotResults part of the grammar.  The following instance variables are therefore maintained: 
self.firstPart = 'that' | 'line' | 'linesnum'
self.action = '' | string (simple action) |
                   list: ['move'|'copy' , 'to'|'up'|'down']
self.numlines = number of lines to select - 1
self.line = linenumber to select
self.movecopyto = line number or number of lines to do the move copy action to
self.previouslines = Previous is used in the command for line selection (0|1)
self.nextLines = Next is used in the command for line selection (0|1)
lines canIn order to collect the numbers in the grammar correctly,
The numbers are collected by the <integer> rule, and subrules, see in natlinkutilsbj.

self.lastDirection gives the last selection direction, persistent

For more information on this number part, see grammar _testnumbersspokenforms.py
"""
import time
import os
import sys
import types
import re
import natlink
from natlinkcore import inivars
import re
# for checking base number:
reNulls = re.compile('0+$')

from natlinkcore import natlinkutils as natut
from dtactions.unimacro import unimacroutils
import unimacro.natlinkutilsbj as natbj
from dtactions.unimacro.unimacroactions import doAction as action
from dtactions.unimacro.unimacroactions import doAction as action
from dtactions.unimacro import unimacroactions as actions
class LinesError(Exception): pass


counts = list(range(1,20)) + list(range(20,50,5)) + list(range(50,100,10)) + list(range(100, 1001, 100))
#print 'counts: %s'% counts

ancestor = natbj.DocstringGrammar
class ThisGrammar(ancestor):
    language = unimacroutils.getLanguage()        
    iniIgnoreGrammarLists = ['count', 'taskcount', 'taskapplication'] # are set in this module
                                                # taskcount and taskapplication only in very special
                                                # case, see Arnoud...
    if language == "nld":
        name = "regels"
        numGram = natbj.numberGrammarTill999['nld']
    else:
        name = "lines"
        numGram = natbj.numberGrammarTill999['enx']
    gramSpec = """
<before> = Here;
<linesthat> exported = (THAT | <lines> | <paras>) <action>;
<linesnum> exported = <linenum> | <linenum> <action>;
<lines> = line | this line | <before> line | 
           {count} lines| <before> {count} lines |
           these {count} lines|
           (previous|next) (line | {count} lines);
<paras> = para | this para | <before> para | <before> this para |
           {count} paras | <before> {count} paras |
           these {count} paras|
           (previous|next) (para | {count} paras);
<linenum> = line (<integer> | <integer>(through<integer> | plus {count}) | back);
<action> = <column> | {simpleaction} | <movecopyaction>;
<column> = column <integer>;
<movecopyaction> = (move | copy) (((down|up) {count})|(to <integer>));
"""+numGram+"""
<base> exported = 'line base' (<integer>|off);
    """

    def initialize(self):
        if not self.language:
            return
        
        self.load(self.gramSpec)
        self.setNumbersList('count', counts)
        
        # only for coupling with tasks search (Arnoud)
        if self.enableSearchCommands:
            self.setNumbersList('taskcount', self.tasksGrammar.taskCounts)
            self.setList('taskapplication', self.tasksGrammar.ini.get('application'))
        
        self.switchOnOrOff()
        self.mode = 'inactive'
        self.lastDirection = 'down'

    def gotBegin(self,moduleInfo):
        if self.checkForChanges:
            self.checkInifile()
        if self.prevModInfo == moduleInfo:
            return
        # changing sets, as moduleInfo changed
##        if not moduleInfo[0]: # no valid module info, do nothing
##            print 'no module info, skipping'
##            return
        # if window changes reset base:
        self.maxBase = 0
        self.base = 0

        progInfo = unimacroutils.getProgInfo(modInfo=moduleInfo)
        if unimacroutils.matchWindow(self.ignore, progInfo=progInfo):
##            print 'progInfo in ignore, skipping: %s'% self.ignore
            return
        if self.windowPolicy(moduleInfo, progInfo):
            if self.mode != 'active':
                self.activateAll()
                self.mode = 'active'
            else:
                pass
##                print '%s, remains active'% self.getName()
        else:
            if self.mode != 'inactive':
##                print '%s: non matching window deactivate: %s'% \
##                      (self.getName(), moduleInfo[1])
                self.deactivateAll()
                self.mode = 'inactive'
            else:
                pass
##                print '%s, remains inactive'% self.getName()
        self.prevModInfo = moduleInfo
        self.progInfo = progInfo

    def gotResultsInit(self,words,fullResults):
        self.currentLine = None
        
        if self.lineNumbersModuloHundred:
            self.app = actions.get_instance_from_progInfo(self.progInfo)
            prog = self.progInfo.prog
            if self.app:
                self.currentLine = self.app.getCurrentLineNumber()
                #if self.currentLine:
                #    print 'current line number for prog: %s: %s'% (prog, self.currentLine)
                #else:
                #    print 'currentLine not found in app: %s'% prog
        self.previousLines = self.nextLines = 0
        self.firstPart = ''        
        self.line = 0
        self.through = 0
        self.newbase = 0 # for collecting a new base number
        self.numlines = 1 # for selecting line number plus count
        self.movecopyto = 0 # line number or number of lines to move or copy to
        self.action = None # for simple actions the action string or list
                           # for movecopy actions set to ['move','to'], ['copy', 'up'] etc
        self.paras = False  # normally lines
        self.column = 0
        self.resetWordVariables()
        
        
        
    def resetWordVariables(self):
        """for the processing of the word copy paste commands
        """
        # self.count is set in the wordspec rule and
        # self.wordAction is set in the rules wordspecifyaction and afterwordoptional.
        # self.direction is default 'right', but can be adapted to 'left' in wordspec rule.
        # in doWordAction, the action is only performed if variable have been set.
        # special case: self.count = 0, only click, in afterwordoptional.
        self.wordAction = None
        self.searchAction = None
        self.count = None
        self.direction = 'right'
        
    ## words:
    # word-action handling:
    def rule_words(self, words):
        """# rules to manage words (copy/paste etc)
           # optional part after a cut/copy action, to move mouse
           # to a new location and do a paste there:
           <wordspecifyaction> | <before> <wordspecifyaction> |
           <wordspecifyaction> <afterwordoptional> | <before> <wordspecifyaction> <afterwordoptional>
        """
        print("never comes here! %s"% words)

    
    def subrule_wordspec(self, words):
        """word | {n2-20} words | word (left|right) | {n2-20} words (left|right)
        """
        lenwords = len(words)
        print("wordspec, got: %s (%s)"% (words, lenwords))
        for i, w in enumerate(words):
            if self.hasCommon(w, 'word'):
                self.count = 1
                if i < lenwords - 1:
                    if self.hasCommon(words[i+1], 'left'):
                        direction = 'left'
            elif self.hasCommon(w, 'words'):
                if not self.count:
                    print('error in grammar lines, wordspec, count should have a value by now: %s\nprocessing word: %s (words: %s)'% \
                          (self.count, w, words))
                if i < lenwords - 1:
                    if self.hasCommon(words[i+1], 'left'):
                        self.direction = 'left'
            elif self.hasCommon(w, ['left', 'right']):
                continue # should have been processed already
            else:
                self.count = self.getNumberFromSpoken(w)
                if not self.count:
                    print('error in grammar lines, wordspec, count been caught here: %s\nprocessing word: %s (words: %s)'% \
                          (self.count, w, words))
                continue
            # process the count:
            if self.wordAction:
                self.doWordAction() # and flush
            if self.searchAction:
                self.doSearchAction()  # and flush

    def subrule_wordspecifyaction(self, words):
        """<wordspec> <wordaction> |
               <wordaction> <wordspec>
        """
        print("should never come in subrule_wordspecifyaction %s"% words)
        
        
    def subrule_wordaction(self, words):
        """{wordaction}| (search ({taskcount}|{taskapplication}))"""
        
        # wordactions, simple actions from inifile
        # search, coupling with tasks grammar for search command after a word
        # was selected, for Arnoud van den Eerenbeemt, QH august 2011
        
        self.wordAction = self.getFromInifile(words, 'wordaction')
        if self.wordAction:
            if self.count:
                self.doWordAction() # only if data
        else:
            if self.hasCommon(words, 'search'):
                self.searchAction = ['search', words[-1]]
                if self.count:
                    self.doSearchAction()

    def subrule_afterwordoptional(self, words):
        """{afterwordaction} | {afterwordaction} <wordspec> | <wordspec> {afterwordaction}
        """
        print("afterwordoptional, got: %s"% words)
        self.wordAction = self.getFromInifile(words, 'afterwordaction')
        if not self.doMouseMoveStopClick():
            self.count = None
            self.wordAction = 0
            print('aborted doMouseMoveStop action, stop this rule')
            return
        # because <wordspec> is optional, test here if it is yet to come (nextRule)
        if self.count:
            # had wordspec rule:
            self.doWordAction()
        elif self.count is None and self.nextRule != 'wordspec':
            print('no word specification in afterwordoptional')
            self.count = 0 # go with a single click if no wordspec has been given
            self.doWordAction()
            
        
    def doMouseMoveStopClick(self):
        """wait for mouse starting to move, stopping and then click
        """
        action("ALERT")
        if not action("WAITMOUSEMOVE"):
            action("ALERT 2")
            return
        if not action("WAITMOUSESTOP"):
            return
        action("ButtonClick")
        action("ALERT")
        return 1

    def doWordAction(self):
        """process count, direction and action
        
        if done, reset variables,
        if variables missing, do nothing
        """
        if self.count is None or self.wordAction is None:
            print('not ready for word action: %s, %s, %s'% (self.count, self.direction, self.wordAction))
            return
        if self.count == 0:
            #print 'doWordAction, single click: %s, %s, %s'% (self.count, self.direction, self.wordAction)
            pass
        else:
            #print 'doWordAction (select words): %s, %s, %s'% (self.count, self.direction, self.wordAction)
            wordSelect = "SELECTWORD %s, %s"% (self.count, self.direction)
            action(wordSelect)
        if self.wordAction:
            action(self.wordAction)
        self.resetWordVariables()

    def doSearchAction(self):
        """process count, direction and action, in this case a search into another window
        
        (coupling with tasks grammar)
        
        if done, reset variables,
        if variables missing, do nothing
        """
        if self.count is None or self.searchAction is None:
            print('not ready for word action: %s, %s, %s'% (self.count, self.direction, self.wordAction))
            return
        if self.count == 0:
            #print 'doWordAction, single click: %s, %s, %s'% (self.count, self.direction, self.wordAction)
            pass
        else:
            #print 'doWordAction (select words): %s, %s, %s'% (self.count, self.direction, self.wordAction)
            wordSelect = "SELECTWORD %s, %s"% (self.count, self.direction)
            action(wordSelect)
        if self.searchAction:
            print('now the search action in the tasks grammar: %s'% self.searchAction)
            self.tasksGrammar.rule_searchinothertask(self.searchAction)
        self.resetWordVariables()


    def gotResults_linenum(self,words,fullResults):
        """starting a linenum rule
        
        when the command is line back, this is intercepted immediately
        otherwise the waiting for a number is started
        """
        if self.hasCommon(words, 'back'):
            self.firstPart = 'lineback'           
            return
        self.firstPart = 'linesnum'
        self.lastDirection = 'down'
        self.collectNumber()
        if self.hasCommon(words, ['line']):
            self.waitForNumber('line')
        elif self.hasCommon(words, ['through']):
            self.waitForNumber('through')
        elif self.hasCommon(words, ['plus']):
            gotCounts = self.getNumbersFromSpoken(words, counts)
            if gotCounts:
                self.numlines = gotCounts[-1] + 1
            

    def gotResults_that(self,words,fullResults):
        self.firstPart = 'that'

    def gotResults_lines(self,words,fullResults):
        self.lastDirection = 'down'
        self.firstPart = 'lines'
        if self.hasCommon(words, ['previous']):
            self.previousLines = 1
            self.lastDirection = 'up'
        if self.hasCommon(words, ['next']):
           self.nextLines = 1
        if self.hasCommon(words, ['line']):
            self.numlines = 1
        if self.hasCommon(words, ['lines']):
            getCounts = self.getNumbersFromSpoken(words, counts)
            if getCounts:
                if len(getCounts) > 1:
                    print('warning, more counts found: %s (take the first)'% getCounts)
                self.numlines = getCounts[0]
            else:
                print('should collect a count, nothing found, take 1')

    def gotResults_paras(self,words,fullResults):
        self.lastDirection = 'down'
        self.firstPart = 'paras'
        if self.hasCommon(words, ['previous']):
            self.previousLines = 1
            self.lastDirection = 'up'
        if self.hasCommon(words, ['next']):
           self.nextLines = 1
        if self.hasCommon(words, ['para']):
            self.numparas = 1
        if self.hasCommon(words, ['paras']):
            getCounts = self.getNumbersFromSpoken(words, counts)
            if getCounts:
                if len(getCounts) > 1:
                    print('warning, more counts found: %s (take the first)'% getCounts)
                self.numlines = getCounts[0]
            else:
                print('should collect a count, nothing found, take 1')


    def gotResults_action(self,words,fullResults):
        self.action = self.getFromInifile(words, 'simpleaction')

    def gotResults_column(self,words,fullResults):
        """wait for integer, action in gotResults
        """
        self.collectNumber()
        self.waitForNumber('column')


    def gotResults_movecopyaction(self,words,fullResults):
        self.collectNumber()
        self.action = [None, None]
        if self.hasCommon(words, ['move']):
            self.action[0] = 'move'
        elif self.hasCommon(words, ['copy']):
            self.action[0] = 'copy'

        if self.hasCommon(words, ['down']):
            self.action[1] = 'down'
            self.movecopyto = self.getNumberFromSpoken(words[-1], counts)
        elif self.hasCommon(words, ['up']):
            self.action[1] = 'up'
            self.movecopyto = self.getNumberFromSpoken(words[-1], counts)
        elif self.hasCommon(words, ['to']):
            self.action[1] = 'to'
            self.waitForNumber('movecopyto')
        print('movecopyto: %s (%s)'% (self.movecopyto, type(self.movecopyto)))


    def gotResults_before(self,words,fullResults):
        if self.hasCommon(words, 'here'):
            natlinkutils.buttonClick('left', 1)

    def gotResults_base(self,words,fullResults):
        if self.hasCommon(words, ['off']):
            self.base = 0
            self.DisplayMessage('resetting line base to 0')
        else:
            self.waitForNumber('newbase')
        
    def gotResults(self,words,fullResults):
        comment = 'command: %s'% ' '.join(words)
        self.prog = self.progInfo.prog
        self.collectNumber()
        #print 'lines command: %s (direction: %s)'% (comment, self.lastDirection)
        #print 'type line: %s'% type(self.line)
        #print 'base: %(base)s, line: %(line)s, through: %(through)s, ' \
        #      'movecopyto: %(movecopyto)s, action: %(action)s'% self.__dict__
        if self.movecopyto and self.action[1] == 'to':
            intLine = int(self.movecopyto)
            if intLine >= 100 or self.movecopyto.startswith('0'):
                self.movecopyto = intLine # always absolute
            elif self.currentLine:
                intLine = getLineRelativeTo(intLine, self.currentLine)
                self.movecopyto = intLine
            else:
                self.movecopyto = intLine
        if self.line:
            intLine = int(self.line)
            #print 'intLine: %s, currentLine: %s'% (intLine, self.currentLine)
            if len(self.line) > 2:
                self.line = intLine # always absolute
            elif self.currentLine:
                intLine = getLineRelativeTo(intLine, self.currentLine)
                print('getLineRelativeTo, old: %s new: %s (currentline: %s)'% (self.line, intLine, self.currentLine))
                self.line = intLine
            else:
                self.line = intLine
            
        if self.through:
            intThrough = int(self.through)
            if intThrough > self.line:
                self.through = intThrough # always absolute
            else:
                if len(self.through) == 2:
                    modulo = 100
                else:
                    modulo = 10
                print('modulo for through: %s'% modulo)
                intThrough = getLineRelativeTo(intThrough, self.line, modulo=modulo,
                                               minLine=self.line)
                self.through = intThrough

            ## should not happen often:
            if self.line > self.through:
                # calculate the next higher number respective to self.line
                ndigits = len(repr(self.through))
                steps = 10**ndigits
                leftPart = self.line//steps
                newThrough = leftPart*steps + self.through
                while newThrough < self.line:
                    leftPart += 1
                    newThrough = leftPart*steps + self.through
                self.through = newThrough
                
            self.numlines = self.through - self.line + 1
        #print 'line: "%(line)s", to: "%(through)s", movecopyto: "%(movecopyto)s"' \
        #     ', numlines "%(numlines)s", action: "%(action)s"'%  self.__dict__

        # doing the selection part:
        T = []
        self.goingUp = 0
        if self.previousLines:
            self.goingUp = 1
        if self.nextLines:
            T.append('{extdown}')
        if self.firstPart == 'that':
            pass
        elif self.firstPart == 'lineback':
            T.append('<<lineback>>')
        elif self.firstPart == 'lines':
            if self.goingUp:
                T.append('<<selectpreviousline>>')
                if self.numlines > 1:
                    T.append('<<selectup %s>>' % (self.numlines-1,))
            else:
                T.append('<<selectline>>')
                if self.numlines > 1:
                    T.append('<<selectdown %s>>' % (self.numlines-1,))
        elif self.firstPart == 'paras':
            print('paragraphs!')
            if self.goingUp:
                print('vorige alinea')
                T.append('<<selectpreviouspara>>')
                if self.numlines > 1:
                    T.append('<<selectparaup %s>>' % (self.numlines-1,))
            else:
                print('deze of volgende alinea')
                T.append('<<selectpara>>')
                if self.numlines > 1:
                    T.append('<<selectparadown %s>>' % (self.numlines-1,))
            
        elif self.firstPart == 'linesnum':
            T.append('<<gotoline %s>>'% self.line)
            if self.numlines > 1:
                T.append('<<selectline>>')
                T.append('<<selectdown %s>>' % (self.numlines-1,))
            elif self.action != None:
                # only when you call for a single line without action, NO
                # selection is done
                T.append('<<selectline>>')

        t1 = time.time ()
        action(''.join(T), comment=comment)
        t2 = time.time ()
##        print 'line select action: %s'% (t2-t1)
        T = []
        
        # doing the action part:
        if self.column:
            keystroke("{right %s}"% self.column)
            return
        if not self.action:
            return
        if isinstance(self.action, str):
            action(self.action, comment=comment)
        elif type(self.action) == list:
            if self.action[0] == 'move':
                T.append('<<cut>>')
            elif self.action[0] == 'copy':
                T.append('<<copy>>')
                if not self.prog in ['excel']:
                    if self.lastDirection == 'up':
                        T.append('{extleft}')
                    elif self.lastDirection == 'down':
                        T.append('{extright}')
            else:
                raise LinesError('invalid movecopy action (first word): %s'% self.action)

            print('gotResult: movecopyto: %s (%s)'% (self.movecopyto, type(self.movecopyto)))
            print('gotResult: numlines: %s'% self.numlines)

            if self.action[1] == 'up':
                if self.prog in ['excel']:
                    T.append("<<movetotopofselection>>")
                if self.prog in ['pycharm64', 'pycharm32']:
                    print('pycharm, %s'% repr(T))
                    if self.action[0] == 'copy':
                        T.append("{ctrl+d}")   # duplicate
                    T.append("{shift+ctrl+up %s}"% self.numlines)
                else:
                    # all other applications
                    T.append('{up %s}' % self.movecopyto)

            elif self.action[1] == 'down':
                if self.prog in ['excel']:
                    T.append("<<movetobottomofselection>>")
                    self.movecopyto += 1
                if self.prog in ['pycharm64', 'pycharm32']:
                    print('pycharm, %s'% repr(T))
                    if T and T[0] == "<<copy>>":
                        T = ["{ctrl+d}"]  ## duplicate
                    else:
                        T = []
                    T.append("{shift+ctrl+down %s}"% self.numlines)
                else:
                    # all other applications:
                    T.append('{down %s}' % self.movecopyto)
            elif self.action[1] == 'to':
                if self.action[0] == 'move' and not self.prog in ['excel']:
                    # if new line below the current line, the cut lines have to be accounted for (not in excel though)
                    currentLine = self.line or self.currentLine
                    if currentLine:
                        if self.movecopyto > currentLine + self.numlines:
                            self.movecopyto -= self.numlines
                    else:
                        print('_lines: movecopyaction: current line not known, move can be wrong if target is below current line')

                T.append('<<gotoline %s>>' % self.movecopyto)
            else:
                raise LinesError('invalid movecopy action (second word): %s'% self.action)
            T.append('<<movecopypaste>>')
            if self.numlines and not self.prog in ['excel']:
                T.append('{extup %s}{exthome}'% self.numlines)
##            action('<<upafterpaste>>', comment=comment)
            T.append('<<afterlines>>')
        if T:
            t1 = time.time ()
            action(''.join(T), comment=comment)
            t2 = time.time ()
##            print 'line action action: %s'% (t2-t1)

    def fillDefaultInifile(self, ini=None):
        """initialize as a starting example the ini file

        """
        ini = ini or self.ini
        ancestor.fillDefaultInifile(self, ini)
        if self.language == 'nld':
            self.ini.set('simpleaction', 'selecteren', '')
            self.ini.set('simpleaction', 'verwijderen', '{del}')
            self.ini.set('simpleaction', 'knippen', '{ctrl+x}')
            self.ini.set('simpleaction', 'kopiejeren', '{ctrl+c}')
            self.ini.set('simpleaction', 'dupliceren', '{ctrl+c}{right}{ctrl+v}')
            self.ini.set('simpleaction', 'wissen', '{del}')
            self.ini.set('simpleaction', 'einde', '<<endafterselection>>')
            self.ini.set('simpleaction', 'over plakken', '{ctrl+v}')
            self.ini.set('simpleaction', 'plakken', '<<realhome>>{ctrl+v}')
            self.ini.set('simpleaction', 'over plakken', '{ctrl+v}')
            self.ini.set('simpleaction', 'over plakken', '{ctrl+v}')
            self.ini.set('general', 'deactivate', 'sol')
            self.ini.set('general', 'ignore', 'empty')
            
        elif self.language == 'enx':
            self.ini.set('simpleaction', 'select', '')
            self.ini.set('simpleaction', 'delete', '{del}')
            self.ini.set('simpleaction', 'cut', '{ctrl+x}')
            self.ini.set('simpleaction', 'copy', '{ctrl+c}')
            self.ini.set('simpleaction', 'duplicate', '{ctrl+c}{right}{ctrl+v}')
            self.ini.set('simpleaction', 'end', '<<endafterselection>>')
            self.ini.set('simpleaction', 'paste', '<<realhome>>{ctrl+v}')
            self.ini.set('simpleaction', 'paste over', '{ctrl+v}')
            self.ini.set('general', 'deactivate', 'sol')
            self.ini.set('general', 'ignore', 'empty')
        else:
            self.ini.set('simpleaction', 'select', '')
            self.ini.set('general', 'ignore', 'empty')

    def fillInstanceVariables(self, ini=None):
        """fills instance variables with data from inifile

        overload for grammar lines: get activate/deactivate windows

        """
        try:
            #print 'fillInstantVariables for %s'% self
            ini = ini or self.ini
            self.lineNumbersModuloHundred = self.ini.getBool('general', 'line numbers modulo hundred')
            if self.lineNumbersModuloHundred:
                print('_lines: do "line numbers modulo hundred" if the application allows this')

            self.activateRules = ini.getDict('general', 'activate')
            if not self.activateRules:
                self.activateRules = {'all': None}
            if '*' in self.activateRules:
                del self.activateRules['*']
                self.activateRules['all'] = None
            for prog in self.activateRules:
                if self.activateRules[prog] == '*':
                    self.activateRules[prog]  = None
    ##        print 'self.activateRules: %s'% self.activateRules

            self.deactivateRules = ini.getDict('general', 'deactivate')
            if not self.deactivateRules:
                self.deactivateRules = {'none': None}
            if '*' in self.deactivateRules:
                del self.deactivateRules['*']
                self.deactivateRules['all'] = None
            for prog in self.deactivateRules:
                if self.deactivateRules[prog] == '*':
                    self.deactivateRules[prog]  = None
    ##        print 'self.deactivateRules: %s'% self.deactivateRules
            
            self.ignore = ini.getDict('general', 'ignore')
            if not self.ignore:
                try:
                    mgwn = {'nld': 'muisraster'}[self.language]
                except KeyError:
                    mgwn = 'mouse grid'
                self.ignore = {'empty': None, 'natspeak': mgwn}
            for prog in self.ignore:
                if self.ignore[prog] == '*':
                    self.ignore[prog]  = None
    ##        print 'self.ignore: %s'% self.ignore

            # Arnoud, same option needs to be set in _tasks
            self.tasksGrammarName = self.ini.get('general', 'enable search commands')
            self.tasksGrammar = self.enableSearchCommands = None
            # after a wordspec you can call "search number or task", numbers and tasks
            # corresponding with the _tasks grammar
            if self.tasksGrammarName:
                self.tasksGrammar = natbj.GetGrammarObject(self.tasksGrammarName)
                if self.tasksGrammar:
                    self.enableSearchCommands = 1
                    print('_lines, enable search commands, coupling grammar %s with %s'% (self.name, self.tasksGrammarName))
                else:
                    print('_lines, enable search commands failed, invalid name: %s'% self.tasksGrammarName)
                    self.enableSearchCommands = 0
            
        except inivars.IniError:
            print('IniError while initialising ini variables in _lines')

            
    def windowPolicy(self, modInfo, progInfo=None): 
        progInfo = progInfo or unimacroutils.getProgInfo(modInfo)
##        print 'window policy------progInfo: ', `progInfo`
        if unimacroutils.matchWindow(self.activateRules, progInfo=progInfo):
##            print 'matching activate: %s'% self.activateRules
            if not unimacroutils.matchWindow(self.deactivateRules, progInfo=progInfo):
                return 1
##        else:
##            print 'no positive match, deactivate:  %s'% self.activateRules
##        print 'window policy no match: %s'% modInfo[1]

def getLineRelativeTo(relativelinenum, currentLine, modulo=100, minLine=1, maxLine=None, visStart=None, visEnd=None):
    """return linenumber closest to currentLine, relative is modulo (normally 100)
    
    from lisp code of Mark, python (QH, modulolinenumbersmdl.py in miscqh) Oct 2013

    cannot below minLine (default 1)
    cannot above maxLine (if given)
    todo: if visStart and visEnd are given, do closest within the visible range...
    """
    n = relativelinenum
    if n < 0 or n >= modulo:
        raise ValueError("getLineRelativeTo, linenum must be between 0 and %s, not: %s"% (modulo, n))
    a = currentLine - currentLine%modulo + n
    if a < currentLine:
        b = a + modulo
    else:
        b = a - modulo
    if a < minLine: return b
    if b < minLine: return a
    if maxLine:
        if a > maxLine: return b
        if b > maxLine: return a

    if abs(a-currentLine) < abs(b-currentLine):
        return a
    else:
        return b


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

