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
# _number.py 
#  written by: Quintijn Hoogenboom (QH softwaretraining & advies)
#  August 2003
# 
"""smart and reliable number dictation

the number part of the grammar was initially provided by Joel Gould in
his grammar "winspch.py it is changed a bit, but essentially all sorts of numbers can be
dictated with his grammar.

For real use in other grammars, copy the things from his grammar into another grammar. See
for example "_lines.py" and "firefox browsing.py".
BUT: first try if the logic of _number simple.py is enough. If not, study this grammar.

BTW when dictating numbers in excel (doing my bookkeeping), I use this grammar  (or the "number simple") all the time!

QH september 2013: rewriting of the functions, ruling out optional command words. The optional word "and" has been removed
            (now say "three hundred twenty" instead of "three hundred and twenty")

QH211203: English numbers require more work: thirty three can be recognised as "33" or
as "30", "3".

QH050104: standardised things, and put functions in natlinkutilsbj, so that
other grammars can invoke the number grammar more easily.
"""
from dtactions.unimacro.unimacroactions import doAction as action
from dtactions.unimacro.unimacroactions import doAction as action
from unimacro.actions import getMetaAction

from natlinkcore import natlinkutils
from dtactions.unimacro import unimacroutils
import unimacro.natlinkutilsbj as natbj

import iban  # special module for banknumber (European mainly I think)
import types  

# Note: lists number1to99 and number1to9 and n1-9 and n20-90 etc. are taken from function getNumberList in natlinkutilsbj

ancestor = natbj.IniGrammar
class ThisGrammar(ancestor):

    language = unimacroutils.getLanguage()
    #Step 1, choose one of next three grammar rules:
    # the <integer> rule comes from these grammar rules
    try:
        number_rules = natbj.numberGrammarTill999[language]
    except KeyError:
        print('take number grammar from "enx"')
        number_rules = natbj.numberGrammarTill999['enx']
    
    #number_rules = natbj.numberGrammarTill999999[language] # including thousands
    #number_rules = natbj.numberGrammar[language] #  including millions
    name = "number extended"
    # do not use "To" instead of "Through", because "To" sounds the same as "2"
    gramSpec = ["""
<testnumber1> exported = [<spacing>] (number <number>)+;
<testnumber2> exported = number <integer> Through <integer>;
<pagenumber> exported = page <integer> [Through <integer>];
<filenamelastpage> exported = filename last page;
<pair> exported = Pair <number> And <number>;
<number> = <integer> | Minus <integer> | <float> | Minus <float>;
<spacingnumber> exported = number (<spacing>|<number>)+;
<spacing> = {spacing};
"""]
    gramSpec.append("<banknumber> exported = IBAN {n00-99} {bankheader} <integer>;")
    gramSpec.append(number_rules)
    try:
        integer999 = natbj.numberGrammarTill999[language]
    except KeyError:
        print('take number grammar from "enx"')
        integer999 = natbj.numberGrammarTill999['enx']
    ##  345567;345567
    ## these are special rules for making numbers of specific length.
    ## when they appear to be usefull, I will try to make them available in other languages
    ## and other cases too:
        
    amsterdamZuidRule = """<numberaztotal> exported =  <numberazone> | <numberaztwo> | <numberazone><numberaztwo>;
    <numberazone>  = zesentachtig <numberthreedigits><numberthreedigits>;
    <numberaztwo> = point (<__thousandslimited>  | <numbertwodigits><numbertwodigits>);
<numbertwodigits> = {n0-9}{n0-9} | {n10-99};
<numberthreedigits> = {n0-9}{n0-9}{n0-9} | <__hundredslimited> | {n0-9} <numbertwodigits>;
<__hundredslimited> = hundred | <__2to9before> hundred | hundred <__1to99after> ;
<__thousandslimited> = thousand | <__2to9before> thousand | thousand <__1to99after> |
                        <__2to9before> thousand <__1to9after>;

<numberfourdigits> = <__thousandslimited>  | <numbertwodigits> <numbertwodigits> ;
<numbersixdigits> = {n0-9}+ | {n0-9} <numbertwodigits>  {n0-9} <numbertwodigits> ;
<__thousands> = duizend | (<__1to99>|<__hundreds>) duizend | duizend (<__1to99>|<__hundreds>) |
                   (<__1to99>|<__hundreds>) duizend  (<__1to99>|<__hundreds>);
<__2to9before> = {n2-9};
<__1to99after> = {n1-99};
<__1to9after> = {n1-9};

"""

##8600 8650 86 2008
    def gotResults___hundredslimited(self,words,fullResults):
        """will return only three digits as _sofar
        goes together with <__2to9before> and <__1to99after>
        
        """
        didBeforeRules = ['__2to9before']
        doInAfterRules = ['__1to99after', '__1to9after']
    
        print('__hundredslimited, prevRule: %s, nextRule: %s, words: %s'% (self.prevRule, self.nextRule, words))
        lenw = len(words)
        for i in range(lenw):
            if i == 0 and self.prevRule in didBeforeRules:
                pass
            else:
                self._hundreds = 100
            if self.nextRule in doInAfterRules and  i == lenw - 1:
                # leave the "adding" action to nextRule
                pass
            else:
                self._sofar += str(self._hundreds)
                self._hundreds = 0

    def gotResults___thousandslimited(self,words,fullResults):
        """will return only four digits as _sofar
        
        goes together with <__2to9before> and <__1to99after> and possibly <__1to9after>
        
        """
        didBeforeRules = ['__2to9before']
        doInAfterRules = ['__1to99after', '__1to9after']
    
        # print '__hundredslimited, prevRule: %s, nextRule: %s, words: %s'% (self.prevRule, self.nextRule, words)
        lenw = len(words)
        for i in range(lenw):
            if i == 0 and self.prevRule in didBeforeRules:
                pass
            else:
                self._thousands = 1000
            if self.nextRule in doInAfterRules and  i == lenw - 1:
                # leave the "adding" action to nextRule
                pass
            else:
                self._sofar += str(self._thousands)
                self._thousands = 0

    def gotResults___1to99after(self, words, fullResults):
        """should be after __hundredslimited or __thousandslimited
        
        must be defined in doInAfterRules ofter the corresponding rule
        """
        didBeforeRules = ['__hundredslimited', '__thousandslimited']

        print('__1to99after, prevRule: %s, nextRule: %s, words: %s'% (self.prevRule, self.nextRule, words))
        if len(words) > 1:
            raise ValueError("rule __1to99after, expect only one word, got %s: %s"% (len(words), words))
        numWords = self.getNumbersFromSpoken(words)
        num = numWords[0]
        if self.prevRule == '__hundredslimited':
            self._hundreds += num
            self._sofar += str(self._hundreds)
            self._hundreds = 0
        elif self.prevRule == '__thousandslimited':
            self._thousands += num
            self._sofar += str(self._thousands)
            self._thousands = 0
        else:
            print('__1to99after, no valid rule, got: %s, expected one of: %s'% (self.prevRule, didBeforeRules))
            self._sofar += str(num)
            print('_sofar: %s'% self._sofar)

    def gotResults___1to9after(self, words, fullResults):
        """should be after __hundredslimited or __thousandslimited
        
        must be defined in doInAfterRules ofter the corresponding rule
        
        Identical with gotResults___1to99after
        """
        didBeforeRules = ['__hundredslimited', '__thousandslimited']

        print('__1to99after, prevRule: %s, nextRule: %s, words: %s'% (self.prevRule, self.nextRule, words))
        if len(words) > 1:
            raise ValueError("rule __1to99after, expect only one word, got %s: %s"% (len(words), words))
        numWords = self.getNumbersFromSpoken(words)
        num = numWords[0]
        if self.prevRule == '__hundredslimited':
            self._hundreds += num
            self._sofar += str(self._hundreds)
            self._hundreds = 0
        elif self.prevRule == '__thousandslimited':
            self._thousands += num
            self._sofar += str(self._thousands)
            self._thousands = 0
        else:
            print('__1to99after, no valid rule, got: %s, expected one of: %s'% (self.prevRule, didBeforeRules))
            self._sofar += str(num)
            print('_sofar: %s'% self._sofar)


    def gotResults___2to9before(self, words, fullResults):
        """together with __hundredslimited or __thousandslimited
        
        expect one word only, and treat with respect to the next rule
        should be defined in didBeforeRules of the corresponding rule
        """
        # print '__2to9before, prevRule: %s, nextRule: %s, words: %s'% (self.prevRule, self.nextRule, words)
        
        if len(words) > 1:
            raise ValueError("rule __2to9before, expect only one word, got %s: %s"% (len(words), words))
        numWords = self.getNumbersFromSpoken(words, asStr=1)
        numStr = numWords[0]
        num = int(numStr)
        if self.nextRule == '__hundredslimited':
            self._hundreds = num * 100
        if self.nextRule == '__thousandslimited':
            self._thousands = num * 1000
        else:
            print('__2to9before, nextRule is NOT __hundredslimited of __thousandslimited')
            self._sofar += numStr
            print('_sofar: %s'% self._sofar)
    

##8640  8600

#failed to get this working:
#<listtupleargument> exported = (Tuple|List|Argument) (Number <number> | (Variable|String) <dgndictation> | None)+;
    def __init__(self):
        """start the inifile and add to grammar if needed a special rule
        """
        self.startInifile()
        #print 'enableSearchCommands: %s'% self.enableSearchCommands
        if self.specialAmsterdamZuid:
            self.gramSpec.append(self.amsterdamZuidRule)
        ancestor.__init__(self)                


    def gotBegin(self,moduleInfo):
        if self.checkForChanges:
            self.checkInifile()
        self.progInfo = unimacroutils.getProgInfo(moduleInfo)
  
    def initialize(self):
        if not self.language:
            print("no valid language in grammar "+__name__+" grammar not initialized")
            return
        self.load(self.gramSpec)
        # if switching on fillInstanceVariables also fill numbers lists like {n1-9} or {number1to99}
        self.switchOnOrOff() 

    def gotResultsInit(self, words, fullResults):
        # Step 2:
        # initialise the variables you want to collect the numbers in:
        # defining them here makes testing in gotResults easier
        self.number = ''  # for most rules
        self.page = ''    # for page rule
        self.through = '' # only for testnumber2 and pagenumber
        self.pair = ''    # only for the pair rule...
        self.minus = False
        self.ibanHeader = None # for banknumber
        self.ibanCheck =  None # for banknumber
        self.totalNumber = '' # for multiple parts (Amsterdam Zuid, spacingnumber)

        #self.listtupleargument = ''
        #self.Items = [] # for listtupleargumenthallo
        # this line can be used to get the correct fullResults to be used in testIniGrammar.py for
        # for debugging the rules!
        # print 'fullResults of number extended: %s'% fullResults
        
        
    def fillInstanceVariables(self):
        """fills the necessary instance variables

        in this grammar a special rule for Loes Wijers, Amsterdam Zuid.        
        """
        # search commands (for Arnoud):
        self.specialAmsterdamZuid = self.ini.getBool('general', 'special amsterdam zuid') 
        self.filenamePagenumbersPrefix = self.ini.get('general', 'filename page numbers prefix')
        self.filenamePagenumbersPostfix = self.ini.get('general', 'filename page numbers postfix')
        self.lastPage, self.lastThroug = None, None   # filename page numbers
       
    def gotResults_testnumber1(self, words, fullResults):
        # step 3: setting the number to wait for
        # because more numbers can be collected, the previous ones be collected first
        # if you expect only one number, this function can be skipped (but it is safe to call):
        self.collectNumber()
        result = self.hasCommon(words, 'number')
        if self.hasCommon(words, 'number'):
            if self.number:
                # flush previous number
                self.number =self.doMinus('number', 'minus') # convert to int
                self.outputNumber(self.number)
            self.waitForNumber('number')
        else:
            raise ValueError('invalid user input in grammar %s: %s'%(__name__, words))

    def gotResults_testnumber2(self, words, fullResults):
        # step 4 also: if more numbers are expected,
        # you have to collect the previous number before asking for the new
        self.collectNumber()
        # self.minus is not relevant here, as this rule is about integers only...
        # can ask for 'number' or for 'through':
        if self.hasCommon(words, 'number'):
            self.waitForNumber('number')
        elif self.hasCommon(words, 'through'):
            self.waitForNumber('through')
        else:
            raise NumberError('invalid user input in grammar %s: %s'%(__name__, words))

    def gotResults_spacingnumber(self, words, fullResults):
        self.collectNumber()
        self.totalNumber += self.number
        self.waitForNumber('number')

    def gotResults_spacing(self, words, fullResults):
        self.collectNumber()
        self.totalNumber += self.number
        self.waitForNumber('number')
        for w in words:
            spacingchar = self.getFromInifile(w, 'spacing')
            self.totalNumber += spacingchar
        
    def gotResults_pagenumber(self, words, fullResults):
        # step 4 also: if more numbers are expected,
        # you have to collect the previous number before asking for the new
        self.collectNumber()
        # self.minus is not relevant here, as this rule is about integers only...
        # can ask for 'number' or for 'through':
        if self.hasCommon(words, 'page'):
            self.waitForNumber('page')
        elif self.hasCommon(words, 'through'):
            self.waitForNumber('through')
        else:
            raise NumberError('invalid words in pagenumber rule in grammar %s: %s'%(__name__, words))

    def gotResults_filenamelastpage(self, words, fullResults):
        # additional command, compose filename with the last called page number(s).
        # need variables in inifile section [general]: filename pagenumber prefix and filename pagenumber postfix
        # if these are not set, of if no page numbers are "remembered", do nothing
        if self.lastPage:
            if self.lastThroug:
                lp, lt = int(self.lastPage), int(self.lastThroug)
                if lt > lp:
                    pagePart = '%s-%s'% (lp, lt)
                else:
                    pagePart = self.lastPage
            else:
                pagePart = self.lastPage
        else:
            print('numbers extended: no page numbers command issued yet, skip command')
            return
        if not self.filenamePagenumbersPrefix:
            print('%s: command "%s", please specify "filename page numbers prefix" in section [general] of inifile'% (' '.join(words), self.name))
        if not self.filenamePagenumbersPostfix:
            print('%s: command "%s", please specify "filename page numbers postfix" in section [general] of inifile'% (' '.join(words), self.name))
        if self.filenamePagenumbersPrefix and self.filenamePagenumbersPostfix:
            fName = self.filenamePagenumbersPrefix + pagePart + self.filenamePagenumbersPostfix
            action("SCLIP %s"% fName)

    def gotResults_pair(self, words, fullResults):
        # here a bit different logic for the place to collect the previous number.
        #
        self.pair = 'pair'
        if self.hasCommon(words, 'and'):
            self.collectNumber()
            self.number = self.doMinus('number', 'minus')
            self.waitForNumber('pair')
        else:
            self.waitForNumber('number')

    def gotResults_banknumber(self,words,fullResults):
        """get first 8 characters from bank name (list), rest from numbers grammar
        """
        self.ibanHeader = self.getFromInifile(words[-1], 'bankheader')
        self.ibanCheck =  "%.2d"% self.getNumberFromSpoken(words[-2])
        self.waitForNumber('number')

    def gotResults_number(self, words, fullResults):
        # step: when in this rule, the word Minus (or synonym or translation) has been spoken..
        self.minus = True

    def gotResults_numberazone(self, words, fullResults):
        """first part of the number"""
        if not self.totalNumber:
            self.totalNumber = '86'
            # print 'totalNumber: ', self.totalNumber
        self.collectNumber()
        self.totalNumber += self.number
        self.number = ''
        # wait for a number of 6 digits, if not, do NOT output!!
        self.waitForNumber('number', 6)

    def gotResults_numberaztwo(self, words, fullResults):
        """second part of the number"""
        self.collectNumber()
        self.totalNumber += self.number
        self.number = ''
        self.totalNumber += '.'
        # wait for a number of 6 digits, if not, do NOT output!!
        self.waitForNumber('number', 4)

# # # # <numbertwodigits> = {n0-9}{n0-9} | {n10-99};
# # # # <numberthreedigits> = {n0-9}+ | <__hundreds> | {n0-9} <numbertwodigits>;
    def gotResults_numbertwodigits(self, words, fullResults):
        numWords = self.getNumbersFromSpoken(words, asStr=1)
        numberString = ''.join(numWords)
        self._sofar += numberString
        
    def gotResults_numberthreedigits(self, words, fullResults):
        numWords = self.getNumbersFromSpoken(words, asStr=1)
        numberString = ''.join(numWords)
        self._sofar += numberString

    def gotResults_numberfourdigits(self, words, fullResults):
        numWords = self.getNumbersFromSpoken(words, asStr=1)
        numberString = ''.join(numWords)
        self._sofar += numberString

    def gotResults_numbersixdigits(self, words, fullResults):
        numWords = self.getNumbersFromSpoken(words, asStr=1)
        numberString = ''.join(numWords)
        self._sofar += numberString

    def gotResults(self, words, fullResults):
        # step 5, in got results collect the number:
        self.collectNumber()
        
        if self.totalNumber:
            # multiple numbers, AmsterdamZuid
            self.totalNumber += self.number
            print('gotResults totalNumber: ', self.totalNumber)
            if self.message:
                print('Error collecting the number, do NOT output the number...')
                print(self.message)
            else:
                self.outputNumber(self.totalNumber)
            if len(self.totalNumber) == 13 and self.totalNumber[-5] == '.':
                keystroke("{tab}")
            elif len(self.totalNumber) == 5 and self.totalNumber[0] == '.':
                keystroke("{tab}")
            
            return
        
        if self.page:
            ## page numbers rule (for child windows, adobe [acrord32] of pdf24.)
            self.lastPage, self.lastThroug = self.page, self.through
            print('setting lastPage and lastThroug: %s, %s'% (self.lastPage, self.lastThroug))
            isTop = (self.progInfo[2] == 'top')
            ma = getMetaAction('pagestart', progInfo=self.progInfo)
            if not ma:
                print('no metaactions defined for pagestart, stop command %s'% self.progInfo.prog)
                if isTop:
                    if self.through:
                        keystroke(" page %s-%s"% (self.page, self.through))
                    else:
                        keystroke(" page %s"% self.page)
                else:
                    print("cannot finish page command for child window: %s"% repr(self.progInfo))
                return

            action("<<pagestart>>")
            keystroke(self.page)
            if self.progInfo.prog == 'pdf24-creator' and self.through == '':
                self.through = self.page

            if self.through:
                ## only child window here:
                action("<<pagethrough>>")
                keystroke(self.through)
            action("<<pagefinish>>")
            return  # page command
            
        elif self.pair:
            self.pair = self.doMinus('pair', 'minus')
            print("(%s, %s) "% (self.number, self.pair))
            
          
        #elif self.listtupleargument:
        #    print 'self.listtupleargument in gotResults: %s'% self.listtupleargument
        #    if self.number:
        #        self.number = self.doMinus('number', 'minus')
        #        self.Items.append(self.number)                    
        #
        #    if self.dictated:
        #        self.Items.append(''.join(self.dictated))
        #        self.dictated = None
        #
        #    result = repr(self.Items)
        #    print 'result: %s'% self.Items
        #    if self.listtupleargument == 'list':
        #        print 'list: %s'% result
        #    elif self.listtupleargument == 'tuple':
        #        result = repr(tuple(self.Items))
        #        print 'tuple: %s'% result
        #    else:
        #        result = repr(tuple(self.Items)).replace(', ', ',')
        #        result = result.replace(', ',',')
        #        print 'argument: %s'% result
        #
        elif self.ibanCheck and self.ibanHeader:
            try:
                # print 'ibanheader: %s, number: %s'% (self.ibanHeader, self.number)
                result = Iban = iban.create_iban(self.ibanHeader[:2], self.ibanHeader[2:], self.number)
            except iban.IBANError as err:
                print('invalid iban %s, %s (%s)'% (self.ibanHeader, self.number, err))
                return
            if result[2:4] == str(self.ibanCheck):
                keystroke(result)
            else:
                print('invalid check: %s (%s) '% (self.ibanCheck, result))

        elif self.number:
            # last part if all others failed:
            self.number = self.doMinus('number', 'minus')
            self.outputNumber(self.number)

                      
    def outputNumber(self, number):
        if type(number) in [int, float]:
            number = str(number)

        keystroke(number)
        prog = unimacroutils.getProgName()
        if prog in ['iexplore', 'firefox', 'chrome', 'safari']:
            keystroke('{tab}')
        elif prog in ['natspeak']:
            keystroke('{enter}')
        elif prog in ['excel', 'winword', 'soffice']:
            keystroke('{tab}')



    def doMinus(self, number, minus):
        """return  the minus version of number, is self.minus is set

        pass in the names of the number variable and the name of the minus variable.
        return the wanted number.        
        """
        Nstring = getattr(self, number)
        Nstring = Nstring.strip()
        Minus = getattr(self, minus)
        if not Nstring:
            setattr(self, minus, False)
            return ''

        if Minus:
            if Nstring.startswith('-'):
                Nstring = Nstring[1:]
            else:
                Nstring = '-'+Nstring
            setattr(self, minus, False)
        return Nstring

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
