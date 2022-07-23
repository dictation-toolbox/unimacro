__version__ = "$Rev: 606 $ on $Date: 2019-04-23 14:30:57 +0200 (di, 23 apr 2019) $ by $Author: quintijn $"
# This file is part of a SourceForge project called "unimacro" see
# http://unimacro.SourceForge.net and http://qh.antenna.nl/unimacro
# (c) copyright 2003 see http://qh.antenna.nl/unimacro/aboutunimacro.html
#    or the file COPYRIGHT.txt in the natlink\natlink directory 
#
# _keystrokes.py 
#  written by: Quintijn Hoogenboom (QH softwaretraining & advies)
#  August 2002, revised September 2003, revised June 2011
"""grammar in which you can continuously dictate keystrokes

There are repeatable keys, like up, down, tab, and non-repeatable keys
like 'alpha, bravo, Home, Context Menu'.

Modes are introduced in this grammar so that in some programs special
keystrokes can be defined, that can be used in combination with all the
others continuously.

"""
import time
import os
import sys
from natlinkcore import inivars
import types
import copy
import natlink
import nsformat
from dtactions.unimacro.unimacroactions import doAction as action
from dtactions.unimacro.unimacroactions import doAction as action

from natlinkcore import natlinkutils as natut
from dtactions.unimacro import unimacroutils
from dtactions.unimacro import unimacroutils
import unimacro.natlinkutilsbj as natbj

language = unimacroutils.getLanguage()        

ancestor = natbj.IniGrammar
class ThisGrammar(ancestor):

    iniIgnoreGrammarLists = ['count', 'effcount', 'character', 'punctuation']
    name = 'keystrokes'
    stdkeysrule = """<stdkeys> = <contextmenu> | <repkey> | <repkey><count> | <norepkey> |
                     <modifiers><repkey> | <modifiers><repkey><count> | <modifiers><norepkey>;"""
    allkeysrule = """<allkeys> = <lastkey> |
        ((<click>|<stdkeys>)+ | (<click>|<stdkeys>)+<lastkey>);"""
    
    lastkeyrule = "<lastkey> = dictate <dgndictation>;"  # only with allkeys!
    importedrule = "<dgndictation> imported;"
    beforerule = "<before> = here|keystroke;"    # to be translated, only for keystrokes extended...
    clickrule = "<click> = {click} | <modifiers> {click};"
    lastpartofgramspec = """<codesof> exported = ('Codes of') <stdkeys>+;
<count> = {count};
<repkey> = {repkey};
<norepkey> = {character}|{norepkey}|<effkey>|{punctuation};
<effkey> = (Eff|Function) {effcount};
<contextmenu> = ('context menu');
<modifiers>  = (Cap|'All-Caps'|Shift|Control|Alt)+ ;
<switchkeys> exported = "keystrokes (simple|extended)";
""" 

    def __init__(self):
        self.language = unimacroutils.getLanguage()
        # here the grammar is not loaded yet, but the ini file is present
        self.startInifile()
        #print 'requireTimes: %s, simpleOrExtended: %s'% (self.requireTimes, self.doKeystrokesExtended)
        self.constructGramSpec(inInit=1)
        ancestor.__init__(self)

    def constructGramSpec(self, inInit=0):
        """return the gramSpec, from gramSpecStart, with several options and tranlation steps
        """
        # first make stdkeysrule with times compulsory or voluntary:
        #if self.requireTimes:
        #    timespart = "(times)"
        #else:
        #    timespart = "[times]"
        #stdkeysrule = self.stdkeysrule % timespart
        
        if self.doKeystrokesExtended:
            startrule = "<startrule> exported = <before>+ <allkeys> | <allkeys>;"
            startSpec = ["# keystrokes extended",
                         startrule, self.stdkeysrule,
                         self.allkeysrule, self.lastkeyrule,
                         self.clickrule, self.importedrule,
                         self.beforerule]
        else:
            startrule = "<startrule> exported = <stdkeys>+;"
            startSpec = ["# keystrokes simple",
                         startrule, self.stdkeysrule]
        #print 'startSpec: %s\n\n'% startSpec
        startSpec.append(self.lastpartofgramspec)
        self.gramSpec = copy.copy(startSpec)
        if not inInit:
            # this should be done only at switchkey command:
            self.unload()
            self.load(self.gramSpec)
        


    def initialize(self):
        #print 'self.gramspec: %s'% self.gramSpec
        self.load(self.gramSpec)
        # call for extra spoken form with difficult numbers
        # needs self.stripSpokenForm in gotResults... function!!!
        #self.addSpokenFormNumbers(self.taskCounts)
        self.countList = list(range(1, self.maxCount+1))
        self.effCountList = list(range(1, self.maxEffCount+1))  
        self.setNumbersList('count', self.countList)
        self.setNumbersList('effcount', self.effCountList)

        self.setCharactersList('character')
        self.setPunctuationList('punctuation')
        self.resetAllVars()
        self.resetVars()
        self.isIgnored = 0
        self.title = 'Unimacro grammar %s (%s) language: %s'% (self.name, __name__, language)
        #self.activateAll()
        self.fillGrammarLists()
        self.dictateOutputState = -1 # start state for dictate <dgndictation> rule (nsformat)
            
    def gotBegin(self, moduleInfo):
        if self.checkForChanges:
            if self.checkInifile():
                self.resetAllVars()
        if self.prevModule == moduleInfo:
            return

        progInfo = unimacroutils.getProgInfo(moduleInfo)       

        self.isIgnored = 0

        if self.ignore and unimacroutils.matchWindow(self.ignore, progInfo=progInfo):
            self.isIgnored = 1
            return


        mode = self.windowPolicy(progInfo=progInfo)
        if mode == self.prevMode:
            return 
##        print 'keystrokes, new mode: ', mode
        if self.prevMode == 'inactive':
            self.activateAll()
            
        self.prevMode = mode
        ini = self.ini
        #print 'do keystrokes for mode: %s'% repr(mode)
        if mode == 'inactive':
            print('%s: deactivate: %s'% (self.GetName(), mode))
            self.deactivateAll()
            self.cancelMode()
            self.resetAllVars()
            return
        elif mode == 'active':
            repkeySections = ['repkey']
            norepkeySections = ['norepkey']
            # print 'activate "default mode" keystrokes'
##            print '%s, mode: %s, repkeySections: %s, norepkeySections: %s'% \
##                  (self.GetName(), mode, self.repkeySections, self.norepkeySections)
        else:
            # print 'activate keystrokes with mode: %s'% repr(mode)
            # self.modeSet is set of modestrings being active:
            wantExclusive = self.modeSet & self.exclusiveModes  # both a set
            if wantExclusive:
                print('make keystokes mode exclusive: %s'% wantExclusive)
                self.setExclusive(1)
            #if 
            repkeySections = self.ini.getSectionsWithPrefix('repkey', mode)
            repkeySections.append('repkey')
            norepkeySections = self.ini.getSectionsWithPrefix('norepkey', mode)
            norepkeySections.append('norepkey')
            #print '%s, mode: %s, repkeySections: %s, norepkeySections: %s'% \
            #      (self.GetName(), mode, repkeySections, norepkeySections)

        if repkeySections != self.repkeySections:
            L = ini.get(repkeySections)
            self.setList('repkey', L)
            self.repkeySections = repkeySections[:]
            self.repkeyList = L[:]
        if norepkeySections != self.norepkeySections:
            L = ini.get(norepkeySections)
            self.setList('norepkey', L)
            self.norepkeySections = norepkeySections[:]
            self.norepkeyList = L[:]
 
    def gotResultsInit(self, words,fullResults):
        self.resetVars()
        self.buf = []
        self.codes = 0
        self.hadClick = 0
        self.fullResults = fullResults
        #print "keystrokes: %s"% words
        if fullResults and fullResults[0][1] != 'lastkey':
            self.dictateOutputState = -1  # reset, otherwise resume previous result.

    def gotResults_before(self, words, fullResults):
        """optional for here or keystroke multiple words even allowed"""
        if not self.hasCommon(words, 'here'):
            print('got words in "before" rule, but not "here": %s'% words)
            return
        # do a click, or (if next rule == contextmenu) a right click.
        button, nClick = 'left', 1
        if self.nextRule == 'contextmenu':
            button = 'right'
        #print '_keystrokes, do a "%s" mouse click'% button
        if not self.doWaitForMouseToStop():
            raise Exception("_keystrokes, mouse did not stop")
        unimacroutils.buttonClick(button, nClick)
        unimacroutils.visibleWait()
        self.hadClick = button             

    def subrule_contextmenu(self, words):
        """'context menu'"""
        if self.hadClick == 'right':
            self.hadClick = 0
            return
        self.flush()
        self.key = '{shift+f10}'
        self.flush()
        
    #def importedrule_dgnletters(self, words):
    #    print 'dgnletters: %s'% words
    #    for w in words:
    #        self.flush()
    #        posSlash = w.find('\\')
    #        if posSlash > 0:
    #            self.key = w[:posSlash]
    #        elif w[:4] in ['\\spa']:
    #            self.key = ' '
    #        elif self.hasCommon(w[1:], 'backslash'):
    #            self.key = '\\'
    #        elif self.hasCommon(w[1:],'cap'):
    #            self.cap = 1dit is een test
    #        else: # 
    #            
    def gotResults_dgndictation(self, words, fullResults):
        print('words of dgndictation: %s'% words)
        formattedOutput, self.dictateOutputState = nsformat.formatWords(words, state=self.dictateOutputState)
        self.key = formattedOutput
        self.flush()
        #
        #try:
        #    natlink.recognitionMimic(words)
        #except natlink.MimicFailed: level Hello space Has
        #    print "_keystrokes, dictate rule: cannot mimic words: %s"% words
            
                     
    def gotResults_count(self, words, fullResults):
        #print 'found count: %s'% words
        self.count = self.getNumberFromSpoken(words[0])

    # repkey gevraagd:
    def gotResults_repkey(self, words, fullResults):
        "{repkey}"
        self.flush()
        for w in words:
            self.flush()
            if self.repkeySections:
                res = self.ini.get(self.repkeySections, w)
            else:
                print('_keystrokes, no repkeySections for this mode: %s'% repr(self.prevMode))
                return
            if res:
                self.key = res
            else:
                print('rep, found character or something else: %s'% w)
                posSlash = w.find('\\')
                if posSlash > 0:
                    self.key = w[:posSlash]
                else:
                    self.key = w

    def gotResults_effkey(self, words, fullResults):
        "( Eff|Function ) {effcount}"
        self.flush()
        count = self.getNumberFromSpoken(words[-1]) 
        self.key = '{f%s}'% count
        self.flush()

    def gotResults_norepkey(self, words, fullResults):
        "{punctuation} | {character} | {norepkey} | <effkey>"
        self.flush()
        if self.key:
            # no waiting for counts, can be done directly:
            self.flushAll()
        for w in words:
            #print 'norepkey: %s'% w
            #  Special case for context menu if the word "Here" had been said
            if self.hasCommon(w,["context menu"]) and self.hadClick:
                continue
            char = self.getCharacterFromSpoken(w)
            if char:
                self.key = char
                #print 'icalphabet: %s'% self.key
            else:
                char = self.getPunctuationFromSpoken(w)
                if char:
                    self.key = char
                else:
                    if self.repkeySections:
                        res = self.ini.get(self.norepkeySections, w)
                    else:
                        print('_keystrokes, no norepkeySections for this mode: %s'% self.prevMode)
                        return
                    res = self.ini.get(self.norepkeySections, w)
                    if not res:
                        raise ValueError("_keystrokes, norepkey: no code found for %s (%s)"% w, (self.fullResults))
                    self.key = res
                #print 'norepkey: %s'% self.key
            self.flush()
    # 
    # kijk hier welke modifier keys (ctrl, shift, alt) gevraagd worden:
    def gotResults_modifiers(self, words, fullResults):
        """(Cap | "All-Caps" | Shift | Control | Alt)+ """
        self.flush()
        self.mod = ''
        # doorloop shift, control en alt:
        #print 'mod:', `words`
        if self.hasCommon(words, 'all-caps'):
            self.cap = max(self.cap, 2)
        elif self.hasCommon(words, 'cap'):
            self.cap = self.cap or 1
        elif self.hasCommon(words,  ['shift']):
            self.mod = 'shift+'
        # control:
        if self.hasCommon(words, ['control']):
            self.mod  = self.mod + 'ctrl+'
        # alt:
        if self.hasCommon(words, ['alt']):
            self.mod = self.mod + 'alt+'

    def gotResults_click(self, words, fullResults):
        """do click, with mouse, rule
        
        modifiers can be set
        """
        # print 'click rule: %s (modifiers: %s), prevrule: %s'% (words, self.mod, self.prevRule)
        self.flush()
        if self.key:
            self.flushAll()
        if self.prevRule is None or self.prevRule in ['startrule', 'modifiers']:
            if not self.doWaitForMouseToStop():
                print('_keystrokes, click, cancel command')
                return
        else:
            if not self.doMouseMoveStopClick():
                print("you should move the mouse a bit at least!")
                return
        possibleButtons = unimacroutils.joelsButtons
        possibleClicks = ['1', '2', '3']
        clickrules = self.getFromInifile(words[0], 'click')
        #print 'clickrules: %s'% clickrules
        if not clickrules:
            print('_keystrokes: no valid clickrule')
            return
        parts = [s.strip() for s in clickrules.split(',')]
        button = parts[0]
        if not button in possibleButtons:
            print('button should be one of %s'% possibleButtons)
            return
        if len(parts) > 1:
            
            if parts[1] not in possibleClicks:
                print('number of clicks (%s) should be one of %s'% (parts[1], possibleClicks))
                return
            nClick = int(parts[1])
        else:
            nClick = 1
    
        if len(parts) > 2:
            print('currently only (button, clicks) allowed in clickrule, not: %s'% clickrules)
            return
    
        if self.nextRule == 'contextmenu' and nClick == 1:
            button = 'right'
        unimacroutils.buttonClick(button, nClick, modifiers=self.mod)
        unimacroutils.visibleWait()
        self.hadClick = button



    def doMouseMoveStopClick(self):
        """wait for mouse starting to move, stopping and then click
        """
        action("ALERT")
        if not action("WAITMOUSEMOVE"):
            action("ALERT 2")
            return
        if not action("WAITMOUSESTOP"):
            action("ALERT 2")
            return
        action("ALERT")
        return 1

    def gotResults_switchkeys(self, words):
        """[do] keystrokes (simple|extended)"""
        #line from fillInstanceVariables:
        #self.doKeystrokesExtended = self.ini.getBool('general', 'extended keystrokes', False)
        if self.hasCommon(words, 'simple'):
            self.doKeystrokesExtended = False
        else:
            self.doKeystrokesExtended = True
        self.ini.set('general', 'extended keystrokes', self.doKeystrokesExtended)
        self.ini.writeIfChanged()
        self.constructGramSpec() # should also reload the grammar
        #print 'after switchkeys, requireTimes: %s, simpleOrExtended: %s'% (self.requireTimes, self.doKeystrokesExtended)

    def gotResults_codesof(self, words,fullResults):
        self.codes = 1
        
    def gotResults_startrule(self, words,fullResults):
        pass # no special rule here!
    
    def gotResults_lastkey(self, words,fullResults):
        self.flush()
        self.flushAll()  
        unimacroutils.visibleWait()

    def gotResults(self, words,fullResults):
        self.flush()
        self.flushAll()
        if self.cap < 3:
            self.cap = 0
            
           
    def flush(self):
        if not self.key:
            return
        self.hadClick = 0

        if self.cap:
            self.key = unimacroutils.doCaps(self.key)

        if self.mod:
            self.key = unimacroutils.doModifier(self.key, self.mod)
        if self.count != 1:
            self.key = unimacroutils.doCount(self.key, self.count)
       
        if type(self.key) == list:
            print('_keystrokes, flush: warning, self.key is list: %s'% self.key)
            self.buf.extend(self.key)
        else:
            self.buf.append(self.key)
        self.resetVars()

    def flushAll(self):
        if self.buf:
            try:
                buf = ''.join(self.buf)
            except TypeError:
                print("---TypeError in flushAll of _keystrokes: %s"% repr(self.buf))
                raise
            
            #print 'flushAll: %s'% buf  
            if self.codes:
                action("SCLIP %s"% buf)
            elif buf.find("<<") >= 0:
                action(buf)
            else:
                keystroke(buf)
            self.buf = []

    def resetVars(self):
        self.mod = ""
        self.count = 1
        self.key = ''
        if self.cap == 1:
            self.cap =0

    
    def resetAllVars(self):
        self.repkeySections = None
        self.norepkeySections = None
        self.repkeyList = self.norepkeyList = []
        self.prevModule = None
        self.prevMode = 'inactive'
        
        self.cap = 0
        self.buf = []
        self.resetVars()
       
    def gotResults_command(self, words,fullResults):
        self.cap = 0
        
        if self.hasCommon(words, ['Caps']):
            self.cap = 3
            
    def windowPolicy(self, modInfo=None, progInfo=None): 
        progInfo = progInfo or unimacroutils.getProgInfo(modInfo)
        #print 'window policy------progInfo: %s'% repr(progInfo)
        #print 'deactivaterules: %s'% self.deactivateRules
        #print 'activaterules: %s'% self.activateRules
        modeSet = []
        for mode in self.modes:
            if unimacroutils.matchWindow(self.modes[mode], progInfo=progInfo):
                modeSet.append(mode)
        self.modeSet = set(modeSet)
        if modeSet: return tuple(modeSet)

        if unimacroutils.matchWindow(self.activateRules, progInfo=progInfo):
            if unimacroutils.matchWindow(self.deactivateRules, progInfo=progInfo):
                return 'inactive'
            return 'active'
        else:
            return 'inactive'

       
    def showInifile(self, body=None, grammarLists=None, ini=None,
                    showGramspec=1, prefix=None, commandExplanation=None,
                    postfix=None, lineLen=60, sort=1):
        body = []
        if self.modes:
            if type(self.prevMode) in (list, tuple):
                modesString = ', '.join(self.prevMode)
            else:
                modesString = str(self.prevMode)
            body.append('current mode/active/inactive: %s'% modesString)
            if not self.prevMode:
                body.append("no current mode (yet): %s"% self.prevMode)
            elif self.prevMode == 'active':
                pass
            elif self.prevMode == 'inactive':
                # probably never comes here, because grammar is inactive at this moment
                body.append('inactive in %s'% self.deactivateRules)
            else:
                # give extra moohdes information:
                body.append('possible modes:')
                for mode in self.modes:
                    if self.modes[mode] == {mode: None}:
                        body.append('\t%s: (all windows)'% mode)
                    else:
                        body.append('\t%s: %s'% (mode, self.modes[mode]))
        else:
            body.append('active/inactive: %s'% self.prevMode)

        if self.doKeystrokesExtended:
            body.append('do keystrokes extended (with Here and mouse clicking)')
        else:
            body.append('do keystrokes simple (no mouse clicking)')
        #if self.requireTimes:
        #    body.append('require "times" when doing repeat keys')
        ancestor.showInifile(self, body=body)

    def fillDefaultInifile(self, ini):
        """initialize as a starting example the ini file obsolete

        """
        pass
        
    def fillInstanceVariables(self):
        """fills instance variables with data from inifile

        overload for grammar keystrokes

        """
        try:
            ini = self.ini
            self.maxCount = ini.getInt('general', 'max count') or 20
            self.maxEffCount = ini.getInt('general', 'max eff count') or 12
            self.doKeystrokesExtended = ini.getBool('general', 'extended keystrokes', False)
            #self.requireTimes = ini.getBool('general', 'require times', False)
            #if self.requireTimes:
            #    print 'require "times" (or translation/synonym) in keystrokes grammar when using repeatable keystrokes'

    ##        print 'fillInstantVariables for %s'% self
            self.activateRules = ini.getDict('general', 'active', {'all': None})
            self.cleanAsterixes(self.activateRules)

            self.deactivateRules = self.ini.getDict('general', 'ignore', {'none': None})
            self.cleanAsterixes(self.deactivateRules)

            modes = ini.get('modes')
            implicitModes = ini.getSectionPostfixesWithPrefix('repkey') + \
                        ini.getSectionPostfixesWithPrefix('norepkey')
            for m in implicitModes:
                if m and m not in modes:
                    #print 'implicit mode added: %s'% m
                    modes.append(m)
            if not modes:
                #print 'no modes defined for grammar: %s'% self.GetName()
                self.modes = None
            else:
                self.modes = {}
                for m in modes:
                    self.modes[m] = ini.getDict('modes', m, {m: None})
                    
            self.exclusiveModes = set(self.ini.getList('general', 'exclusive modes', []))
            for m in self.exclusiveModes:
                if m not in self.modes:
                    print('warning, exclusive mode "%s" not in defined modes: %s'% (repr(m), list(self.modes.keys())))
            
                    
        except inivars.IniError:
            print('IniError while initialising ini variables in _keystrokes')
            print('message: %s'% sys.exc_info()[1])
            return
        
    def cleanAsterixes(self, Dict):
        """change * to None in keys and values, inplace!
        """
        if '*' in Dict:
            del Dict['*']
            Dict['all'] = None
        for prog in Dict:
            if Dict[prog] == '*':
                Dict[prog]  = None
##        print 'self.activateRules: %s'% self.activateRules
 
    def cancelMode(self):
        # ending exclusive mode if in it, also ending the mode it is in
        self.setExclusive(0)
        self.resetAllVars()
 
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
 
def changeCallback(type,args):
    # not active without special version of natlinkmain:
    if ((type == 'mic') and (args=='on')):
        return   # check WAS in natlinkmain...
    if thisGrammar:
        thisGrammar.cancelMode()

