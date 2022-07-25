
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
# _calculator.py 
#  written by: Quintijn Hoogenboom (QH softwaretraining & advies)
#  April 2016
# 
"""smart and reliable number dictation, used for calculator

Inside the calc program the commands can be made exclusive.

But you can also use this grammar in other windows, because python itself can
do the calculations for you.
Also see the page "number grammar" on the Unimacro site and
the grammars _number simple and _number extended.
"""
import copy
from dtactions.unimacro.unimacroactions import doAction as action

from natlinkcore import natlinkutils as natut
from dtactions.unimacro import unimacroutils
from dtactions.unimacro import unimacroutils
import unimacro.natlinkutilsbj as natbj

ancestor = natbj.IniGrammar
class ThisGrammar(ancestor):

    language = unimacroutils.getLanguage()
    normalRules = ['calcnormal', 'cancel']
    calcRules = ['calccalc', 'cancel'] # exclusive
    continueRules = ['calccontinue', 'cancel'] # exclusive

    #see grammar _numbers.py (or _numbers_simple.py or _numbers_extended.py)
    #for instructions on the (quite complicated) number rules
    number_rules = natbj.numberGrammarTill999[language] # hundreds, including a long string of digits

    name = "calculator"

    gramSpec = """
<calcnormal> exported = calculate (<number>|<operator>)+ [equals];
<calccalc> exported = [calculate] (<number>|<operator>)+ [equals];
<calccontinue> exported = equals | (<number>|<operator>)+;
<number> = <integer> | <float>;
<operator> = {operator};
<cancel> exported = Cancel [Calculator] | Calculator Cancel;
"""+number_rules+"""
    """
  
    def initialize(self):
        if not self.language:
            print("no valid language in grammar "+__name__+" grammar not initialized")
            return
        self.load(self.gramSpec)
        # if switching on fillInstanceVariables also fill numbers lists like {n1-9} or {number1to99}
        self.switchOnOrOff()
        self.inCalculation = False
        self.activeSet = None
        self.minus = ''
        self.number = ''
        self.prevModInfo = None
        self.prog = None
        self.exclusive = 0
        self.lastResult = None
        self.startwithLastResult = False
        
    def gotBegin(self, moduleInfo):
        if self.checkForChanges:
            self.checkInifile()
        if self.prevModInfo != moduleInfo:
            progInfo = unimacroutils.getProgInfo(modInfo=moduleInfo)
            self.prevModInfo = moduleInfo
            self.cancelMode()
            self.prog = progInfo.prog
            if self.prog == 'calc':
                self.activeSet = None
            else:
                if self.exclusive:
                    self.activeSet = None  # reinitialize non exclusive

        if self.inCalculation:
            if self.prog != 'calc':
                if not self.activeSet == self.continueRules:
                    self.activeSet = copy.copy(self.continueRules)
                    self.exclusive = 1
                    self.activateSet(self.activeSet, exclusive=self.exclusive)
                    print("calculation, exclusiveRules activated")
        else:
            if self.prog == 'calc':
                if not self.activeSet == self.calcRules:
                    self.activeSet = copy.copy(self.calcRules)
                    self.exclusive = 1
                    self.activateSet(self.activeSet, exclusive=self.exclusive)
                    print("calc, exclusive rules activated")
            else:
                if not self.activeSet == self.normalRules:
                    if self.activeSet:
                        print("calculation, activate normalRules again")
                    self.activeSet = copy.copy(self.normalRules)
                    self.exclusive = 0
                    self.activateSet(self.activeSet, exclusive=self.exclusive)

    def gotResultsInit(self, words, fullResults):
        # Step 2:
        # you can initialise variables here, eg self.minus = None, self.number = ''. Not necessary, but
        # in some grammars more appropriate than in the next function.
        if self.inCalculation:
            pass
            # print 'continue calculation %s'% words
        else:
            ## reset, to be sure:
            self.calculation = []
            self.hadNumber = self.hadOperator = False

        if self.exclusive:
            print('calculation exclusive, wait for number')
            self.waitForNumber('number')
        # starting with no lastresult:
        self.startwithLastResult = False

    def fillInstanceVariables(self):
        """fills the necessary instance variables
        records the unary or possibly unary operators
        
        """
        self.unaryLeftOperators = self.ini.getList('general', 'unary left operators')
        self.unaryRightOperators = self.ini.getList('general', 'unary right operators')
        self.dualOperators = self.ini.getList('general', 'dual operators')  ## may be incomplete, but for double functions, like minus


    def reset(self):
        pass

    def gotResults_calcnormal(self, words, fullResults):
        # step 3: specify the number you are waiting for
        # check if the word Minus is present, and then wait for the number named "number"
        # note in this example self.number is non existent until collectNumber has been visited.
        # self.minus will only be set if the rule number is visited.
        # print 'calcnormal or calccalc'
        if self.hasCommon(words, 'calculate'):
            if self.prog == 'calc':
                print('calculate, clear previous calculation')
                keystroke("{esc}")
            self.waitForNumber('number')
            self.minus = False
            self.inCalculation = True

        elif self.hasCommon(words, 'equals'):
            self.collectNumberAddToCalculation()
            self.calculation.append("=")
            self.doCalculation()
            return

    gotResults_calccalc = gotResults_calcnormal
  
  
    def gotResults_calccontinue(self, words, fullResults):
        # step 3: specify the number you are waiting for
        # check if the word Minus is present, and then wait for the number named "number"
        # note in this example self.number is non existent until collectNumber has been visited.
        # self.minus will only be set if the rule number is visited.
        if not self.inCalculation:
            raise Exception("_calculator, shoud be in a calculation right now")
        
        if self.hasCommon(words, 'equals'):
            self.collectNumberAddToCalculation()
            self.calculation.append("=")
            self.doCalculation()
            self.inCalculation = False
       
    def gotResults_number(self, words, fullResults):
        # this rule only catches with the word "minus"
        print('calculator: rule number, %s'% words)
        # self.waitForNumber('number')
        self.minus = not self.minus

    def gotResults_operator(self, words, fullResults):
        # step 3: specify the number you are waiting for
        # check if the word Minus is present, and then wait for the number named "number"
        # note in this example self.number is non existent until collectNumber has been visited.
        # self.minus will only be set if the rule number is visited.
        
        for w in words:
            self.collectNumberAddToCalculation()
            print('rule operator, hadOperator: %s, hadNumber %s'% (self.hadOperator, self.hadNumber))
            operator = self.getFromInifile(w, 'operator')
            operatorStripped = operator.strip()
    
            unaryLeft = w in self.unaryLeftOperators
            unaryRight = w in self.unaryRightOperators
            possiblyDual = w in self.dualOperators
            
            if self.hadNumber:
                if unaryRight:
                    pass
                elif possiblyDual or not unaryLeft:
                    self.hadNumber = False  # just set now
                else:
                    print('no unaryLeft operator expected: %s'% w)
                    continue
            else:
                if unaryLeft and not possiblyDual:
                    pass
                elif w == words[0]:
                    self.startwithLastResult = True

            if self.hadOperator:
                operator = operator.strip()

            self.calculation.append(operator)
            if not unaryRight:
                self.hadOperator = True

    def gotResults_cancel(self, words, fullResults):
        self.cancelMode()


    def gotResults(self,words,fullResults):
        # step 4, in gotResults collect the number (as a string):
        self.collectNumberAddToCalculation() # setting self.number, see self.waitForNumber above
        if self.calculation:
            if self.prog == 'calc':
                print('calculation sofar (calc): %s'% ''.join(self.calculation))
                self.doCalculation()
            else:
                print('continue calculation or finish with "equals" (or "cancel")')
                print('calculation sofar: %s'% ''.join(self.calculation))
                
 


    def collectNumberAddToCalculation(self):
        """collect the number, and add to self.calculation
        
        also wait again for new number...
        """
        self.collectNumber()
        self.hadNumber = False
        if self.number:
            # if not self.hadOperator:
            #     print 'no operator found, for new number: %s'% self.number
            self.hadNumber = True
            self.hadOperator = False
            if self.minus:
                self.number = '-' + self.number
            self.calculation.append(self.number)
            self.number = ''
            self.waitForNumber('number')
                      
    def doCalculation(self):
        if not self.calculation:
            print('doCalculation, no calculation ready')
            return
        if not self.inCalculation and self.prog != 'calc':
            print('not in a calculation')
            return

        if self.startwithLastResult:
            self.calculation.insert(0, str(self.lastResult))
        
        calculationpython = ''.join([c for c in self.calculation if c != "="])
        # place for python specific tricks:
        if calculationpython.find(',') >= 0:
            calculationpython = calculationpython.replace(',', '.')
        result = eval(calculationpython)
        self.lastResult = result

        if self.prog in ['calc']:
            if self.startwithLastResult:
                del self.calculation[0]  # take memory from calculator, not from this list...
                print('in calc, continuation of calculation, expect lastResult: %s'% self.lastResult)
            for c in self.calculation:
                keystroke(c.strip())

        elif self.prog in ['natspeak']:  # DragonPad
            print('%s = %s'% (calculationpython, result))
        elif self.prog in ['excel']:
            calculationExcel = [c.strip() for c in self.calculation if c != "="]
            calculationExcel = '=' + ''.join(calculationExcel) + "{tab}"
            keystroke(calculationExcel)
        else:
            print("calc: %s = %s"% (calculationpython, result))
            keystroke('%s'% result )
            
        self.inCalculation = False
        self.calculation = []

    def cancelMode(self):
        #print "end of oops exclusive mode", also called when microphone is toggled.
##        print 'resetting oops grammar'
        if self.inCalculation:
            print('%s, cancel exclusive mode'% self.name)
            self.activeSet = None
            self.deactivateAll()
            self.inCalculation = False
            self.lastResult = None
        self.calculation = []


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
    
    
