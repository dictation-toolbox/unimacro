# (unimacro - natlink macro wrapper/extensions)
# (c) copyright 2003 Quintijn Hoogenboom (quintijn@users.sourceforge.net)
#                    Ben Staniford (ben_staniford@users.sourceforge.net)
#                    Bart Jan van Os (bjvo@users.sourceforge.net)
#
# This file is part of a SourceForge project called "unimacro" see
# http://unimacro.SourceForge.net).
#
# "unimacro" is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License, see:
# http://www.gnu.org/licenses/gpl.txt
#
# "unimacro" is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; See the GNU General Public License details.
#
# "unimacro" makes use of another SourceForge project "natlink",
# which has the following copyright notice:
#
# Python Macro Language for Dragon NaturallySpeaking
#   (c) Copyright 1999 by Joel Gould
#   Portions (c) Copyright 1999 by Dragon Systems, Inc.
#
# _modes.py 
#  written by: Quintijn Hoogenboom (QH softwaretraining & advies)
#  August 2008
#  for LaTeX/Math problem Angela Wigmore
# 
"""trying to catch different modes, password (as example, LaTeX, Math)...


"""

import time
import os
import sys
import types
import re
import natlinkcore.natlink as natlink

import natlinkcore.natlinkutils as natut
import unimacro.natlinkutilsqh as natqh
import unimacro.natlinkutilsbj as natbj


# lists number1to99 and number1to9 etc. are taken from function getNumberList in natlinkutilsbj

##ancestor = natbj.TestGrammarBase
ancestor = natbj.IniGrammar
class ThisGrammar(ancestor):

    # rule modes is always on (if the grammar is on that is)
    # of the other 3 exported rules only one can be on...

    normalRules = ["modes"]
    passwordRules = ["modes", "password_mode"]
    latexRules = ["modes", "latex_mode"]
    mathRules = ["modes", "math_mode"]
    modes = ['normal', 'password', 'latex', 'math']
    exclusiveModes = ['password', 'latex']  # never make 'normal' exclusive!
    
    language = natqh.getLanguage()
    # take from natlinkutilsbj:
    ICAlphabet = natbj.getICAlphabet(language=language)
    iniIgnoreGrammarLists = ['letter']

    gramSpec = """
# initially only this rule is on: 
<modes> exported = (normal|latex|math|password) mode (on|off);

# the exclusive mode rules:
<password_mode> exported = <firstpw> [<nextpw>+];
<latex_mode> exported = <firstml> [<nextml>+];
<math_mode> exported = <firstml> [<nextml>+];

# the non exported rules:
# password:
<firstpw> = <letter> | <ucletter> | number <number>;
<nextpw> = <letter> | <ucletter> | number <number>;

# latex/math:
<firstml> = <letter> | <ucletter> | <greekletter> | <operator> | <beginend> | <numberrule>;
<nextml> = <letter> | <ucletter> | <greekletter> | <operator> | <beginend> | <numberrule>;

# subrules:
<letter> = {letter};
<ucletter> = (Cap) {letter};
<greekletter> = Greek {greekletter};
<operator> = {operator};
<beginend> = (begin|end) {beginenddirective};
<numberrule> = number <number>;

# insert the numbers grammar, first test with _number!: 
<number> = <integer> [(comma|point|dot) <integer>];   
"""+natbj.numberGrammar[language]


    def gotBegin(self, moduleInfo):
        if self.checkForChanges:
            self.setMode("normal")
  
    def initialize(self):
        self.load(self.gramSpec)
        # if switching on fillInstanceVariables also fill number1to9 and number1to99!
        self.switchOnOrOff()
        self.setList('letter', self.ICAlphabet)

        self.currentMode = 'normal'
        self.numKeystrokes = 0
        self.setMode('normal', silent=1)

    def gotResultsInit(self,words,fullResults):
        # initialise the variables you want to collect the numbers in:
        self.resetData()

    def resetData(self):
        """reset things"""
        # the tricks for the number rule:
        self.waitForNumber('number')
        self.minus = ''

        
    def gotResults_modes(self,words,fullResults):
        """switch on of off modes"""

        # note hasCommon to check for translated words as well (French, Dutch or synonyms)
        # Some more sophisticated things should be done here, for example
        ##when you try to switch off a mode which is not on, what should you do?  
        ##
        ##Also when switching on another mode, maybe the previous mode should be switched off in a more nice way.
        if self.hasCommon(words, 'off'):
            self.setMode('normal')
            return
        if not self.hasCommon(words, 'on'):
            self.DisplayMessage("<modes, invalid command: %s>"% ' '.join(words))
            return

        for mode in self.modes:
            if self.hasCommon(words, mode):
                print('want mode %s (%s)'% (mode, words))
                self.setMode(mode)
                return

    def gotResults_letter(self,words,fullResults):
        self.flushNumber()
        for w in words:
            if w in self.ICAlphabet:
                w = w.split('\\')[0][0]
            else:
                continue
            self.keystroke(w)

    def gotResults_ucletter(self,words,fullResults):
        self.flushNumber()
        for w in words:
            if w in self.ICAlphabet:
                w = w.split('\\')[0][0]
            else:
                continue
            
            self.keystroke(w.upper())

    def gotResults_greekletter(self,words,fullResults):
        self.flushNumber()
        for w in words:
            result = self.getFromInifile(w, 'greekletter')
            if ';' in result:
                results = [t.strip() for t in result.split(";")]
                if self.currentMode == 'normal':
                    result = results[0]
                elif self.currentMode == 'latex' and len(results) > 1:
                    result = results[1]
                elif self.currentMode == 'math' and len(results) > 2:
                    result = results[2]
                else:
                    result = results[-1]
            result = self.doFunc('greekletter%s'% self.currentMode.capitalize(), result)
                    
            print("w: %s, greekletter:   %s" % (w, result))
            self.keystroke(result)
            
    def gotResults_operator(self,words,fullResults):
        """get the operator part, go through mode dependent function

        the function self.operatorModename (Latex, Math, Password) is
        executed if it is defined, input the words (one by one)
        output also a string which is printed.

        """        
        self.flushNumber()
        for w in words:
            result = self.getFromInifile(w, 'operator')
            result = self.doFunc('operator%s'% self.currentMode.capitalize(), result)
            print("w: %s, results:    %s" % (w, result))
            self.keystroke(result)
            
    def gotResults_beginenddirective(self,words,fullResults):
        self.flushNumber()
        for w in words:
            self.keystroke(w)

    def gotResults_numberrule(self,words,fullResults):
        """only flush the number here"""
        self.flushNumber()

    def flushNumber(self):
        """gives the output of a number if it was catching one

        setup the catch for the next number (waitForNumber call)
        """
        self.collectNumber() # gets result in self.number...
        if self.number:
            if self.minus:
                self.number = '-' + self.number
            self.keystroke(self.number)
            self.number = ''
        self.waitForNumber('number')
            

    def gotResults(self,words,fullResults):
        # step 5, in got results collect the number:
        self.flushNumber()
        return
        if self.through:
            res = 'collected number: %s, through: %s'%(self.number, self.through)
            self.keystroke(res+'\n')
        elif self.number:
            if self.minus:
                self.number = '-' + self.number
            self.outputNumber(self.number)
        elif self.pair:
            self.keystroke("{f6}{f6}")
            num = self.pair*2 - 1
            self.keystroke("{tab %s}"% num)
            self.keystroke("<<OpenPair>>")
            
                      
    def outputNumber(self, number):
        self.keystroke(number)
        prog = natqh.getProgName()
        if prog in ['iexplore']:
            self.keystroke('{tab}{extdown}{extleft}')
        elif prog in ['natspeak']:
            self.keystroke('{enter}')
        elif prog in ['excel']:
            self.keystroke('{tab}')

    def setMode(self, mode, silent=None):
        """setting the correct mode and display a message

        the variable currentMode is set,
        the relevant rules are activated
        if silent fals, also DisplayMessage in recognition window...
        """
        print('--- currentmode: %s'% self.currentMode)
        if mode == 'normal':
            if self.currentMode != 'normal':
                self.doFunc('end%sMode'% self.currentMode.capitalize())
        elif self.currentMode not in ['normal', mode]:
            self.doFunc('end%sMode'% self.currentMode.capitalize())

        self.currentMode = mode
        self.doFunc('begin%sMode'% mode.capitalize())
        
        rules = getattr(self, '%sRules'% mode, '')
        if rules:
            exclusive = mode in self.exclusiveModes
            self.activateSet(rules, exclusive=exclusive)
            message = "<modes: %s mode>"% mode
        else:
            message = "<modes: no rules for mode %s>"% mode
        if silent:
            print(message)
        else:
            self.DisplayMessage(message)

    # functions for different modes:
    def beginLatexMode(self):
        """action at beginning of this mode"""
        self.numKeystrokes = 0
        self.keystroke("$ ")
    def beginMathMode(self):
        """action at beginning of this mode"""
        self.numKeystrokes = 0
        self.keystroke("<math>\n")
    def beginPasswordMode(self):
        """action at beginning of this mode"""
        self.numKeystrokes = 0
    def beginNormalMode(self):
        """action at beginning of this mode"""
        self.numKeystrokes = 0

    def endLatexMode(self):
        """action at end of this mode"""
        self.keystroke(" $")
    def endMathMode(self):
        """action at end of this mode"""
        self.keystroke("\n</math>")
    def endPasswordMode(self):
        """action at end of this mode"""
        self.numKeystrokes = 0
    def endNormalMode(self):
        """action at end of this mode"""
        self.numKeystrokes = 0

    def operatorLatex(self, text):
        return " %s "% text
    def operatorMath(self, text):
        return "\n    <mi>%s</mi>"% text

    # utility functions for this grammar:
    def doFunc(self, funcName, *args):
        """apply a function, if present
        prints to Message window when not present
        
        """
        func = getattr(self, funcName, '')
        if func:
            print('mode: %s, func: %s'% (self.currentMode, funcName))
            if args:
                return func(*args)
            else:
                func()
        else:
            if args:
                print('mode: %s, func: %s not present'% (self.currentMode, funcName))
                return args[0]
            else:
                print('modes, function not present: %s'% funcName)
            

    def keystroke(self, keys):
        """do a playString and record the number of self.keystrokes so far

        The number of keystrokes are collected in self.numKeystrokes,
        This variable can be reset at end of a mode, end of phrase etc.
         
        """
        if keys:
            natut.playString(keys)
            self.numKeystrokes += len(keys)

    def cancelMode(self):
        """for example if the mic is switched off

        reset to normal mode
        """
        if self.currentMode != 'normal':
            self.setMode('normal')

    # other name:
    resetExclusiveMode = cancelMode


# standard stuff Joel (adapted for possible empty gramSpec, QH, unimacro)
thisGrammar = ThisGrammar()
if thisGrammar.gramSpec:
    thisGrammar.initialize()
else:
    thisGrammar = None

def unload():
    global thisGrammar
    if thisGrammar: thisGrammar.unload()
    thisGrammar = None

def changeCallback(type,args):
    # not active without special version of natlinkmain,
    # call the cancelMode, to switch off exclusive mode when mic toggles:
    if ((type == 'mic') and (args=='on')):
        return   # check WAS in natlinkmain...
    if thisGrammar:
        thisGrammar.cancelMode()
