#
# Python Macro Language for Dragon NaturallySpeaking
#   (c) Copyright 1999 by Joel Gould
#   Portions (c) Copyright 1999 by Dragon Systems, Inc.
#
# unittestIniGrammar.py
#   This script performs some basic tests of the NatLink 
#   with the IniGrammar subclass.
#   This also tests features of IniGrammar, BrowsableGrammar and GrammarX
#   being the chain of grammars leading up to GrammarBase
#
#   especially test translate feature of the IniGrammar.
#   note special tests which should be made active with care, when in debugging mode for catching specific commands!
#   see def xxxx.....
#
import sys
import unittest
import types
import os
import os.path
import time
import traceback        # for printing exceptions
import TestCaseWithHelpers
import natlink
from natlinkcore import loader
from natlinkcore import natlinkstatus
from natlinkcore import inivars
from gramparser import GrammarError, SyntaxError

status = natlinkstatus.NatlinkStatus()

from natlinkcore import natlinkutils
from dtactions.unimacro import unimacroutils
from dtactions.unimacro import unimacroutils
import unimacro.natlinkutilsbj as natbj
from dtactions.unimacro.unimacroactions import doAction as action
from dtactions.unimacro.unimacroactions import doAction as action

class TestError(Exception):
    pass
ExitQuietly = 'ExitQuietly'

def getBaseFolder(globalsDict=None):
    """get the folder of the calling module.

    either sys.argv[0] (when run direct) or
    __file__, which can be empty. In that case take the working directory
    """
    globalsDictHere = globalsDict or globals()
    baseFolder = ""
    if globalsDictHere['__name__']  == "__main__":
        baseFolder = os.path.split(sys.argv[0])[0]
        print('baseFolder from argv: %s'% baseFolder)
    elif globalsDictHere['__file__']:
        baseFolder = os.path.split(globalsDictHere['__file__'])[0]
        print('baseFolder from __file__: %s'% baseFolder)
    if not baseFolder or baseFolder == '.':
        baseFolder = os.getcwd()
        print('baseFolder was empty, take wd: %s'% baseFolder)
    return baseFolder

thisDir = getBaseFolder(globals())

natconnectOption = 1 # or 1 for threading, 0 for not. Seems to make difference
                     # with spurious error (if set to 1), missing gotBegin and all that...
logFileName = os.path.join(thisDir, "testresult.txt")

#---------------------------------------------------------------------------
# these testruns should be runs when natlink is NOT enabled, but Unimacro is. You establish this by configuring natlink etc.
# as you wish, and then Disable NatLink.
# This debugger run will start_natlink so has connection with all the Unimacro grammars. 
# Restart Dragon and kill extra Dragon instances in the tasks application before rerunning the whole procedure.
# Debugging done this way by Quintijn, September 2013
class UnittestIniGrammar(TestCaseWithHelpers.TestCaseWithHelpers):
    connected = 0
    def setUp(self):
        if not natlink.isNatSpeakRunning():
            raise TestError('NatSpeak is not currently running')
        if not self.connected:
            self.connect()
            self.user = natlink.getCurrentUser()[0]
            self.setMicState = "off"
            self.connected = 1

    def tearDown(self):
        # do nothing, leaving natlink on!
        return
        #try:
        #    # give message:
        #    self.setMicState = "off"
        #    # kill things
        #    self.clearTestFiles().2000
        #finally:
        #    self.disconnect()

    def makeInifile(self, inifilename, iniSpec=None):
        """make in subdirectory inifiles_test a new inifile of this name
        
        """
        inifilepath = os.path.join(thisDir, 'test_inifiles', inifilename)
        ini = inivars.IniVars(inifilepath)
        if iniSpec:
            ini.delete()
            ini.fromDict(iniSpec)
            ini.write()
        return ini
        
    def connect(self):
        # start with 1 for thread safety when run from pythonwin:
        print('connecting')
        natlink.natConnect(natconnectOption)
        # next line should be enabled when testing the testNumbersGrammar functions in debug mode:
        # otherwise disable!
        print('connected natlink (Unimacro)')
        pass

    #def disconnect(self):
        #"""is not called in this test file!"""
        #natlink.natDisconnect()
        
    def log(self, t):
        # only log to file:
        log(t)

    def wait(self, t=1):
        time.sleep(t)


    #---------------------------------------------------------------------------
    # This utility subroutine executes a Python command and makes sure that
    # an exception (of the expected type) is raised.  Otherwise a TestError
    # exception is raised

    def doTestForException(self, exceptionType,command,localVars={}):
        try:
            exec(command,globals(),localVars)
        except exceptionType:
            return
        raise TestError('Expecting an exception to be raised calling '+command)

    def doTestActiveRules(self, gram, expected):
        """gram must be a grammar instance, sort the rules to be expected and got
        """
        expected.sort()
        got = gram.activeRules
        got.sort()
        self.assertEqual(expected, got,
                         'Active rules not as expected:\nexpected: %s, got: %s'%
                         (expected, got))

    def doTestFuncReturn(self, expected,command,localVars=None):
        # account for different values in case of [None, 0] (wordFuncs)
        if localVars == None:
            actual = eval(command)
        else:
            actual = eval(command, globals(), localVars)

        if actual != expected:
            time.sleep(1)
        self.assertEqual(expected, actual, 'Function call "%s" returned unexpected result\nExpected: %s, got: %s'%
                          (command, expected, actual))
    def doTestNumberRecognition(self, words,numberResult):
        try:
            natlink.recognitionMimic(words)
        except natlink.MimicFailed:
            print('failed to recognise %s as testnumber'% words)
            return
        return 1 # success

    def doTestRecognition(self, words,shouldWork=1, log=None):
        if shouldWork:
            natlink.recognitionMimic(words)
            if log:
                self.log("recognised: %s"% words)
        else:
            self.doTestForException(natlink.MimicFailed,"natlink.recognitionMimic(words)",locals())
            if log:
                self.log("did not recognise (as expected): %s"% words)

    
    #def tttestBrowseAllGrammarsControl(self):
    #    """go into the browse all grammars via control grammar
    #       found errors in the BrowseGrammar procedures by debugging this function!!
    #    """
    #    loadedFiles = natlinkmain.loadedFiles
    #    import _control
    #    phrase = ['show', 'all', 'grammars']  # enx
    #    phrase = ['toon', 'alle', 'grammaticaas']  # nld dutch
    #    natlink.recognitionMimic(phrase)
    #    pass
    
    def xxxtestNumbersSimpleGrammarNld(self):
        """test the numbers grammar rules as written in natlinkutilsbj
        
        attach to the _number grammar, with language dutch (translated word for number is "getal").
        (this grammar must be in the Unimacro directory)
        please remove (if applicable) _number extended.py
        
        handle with care, run or debug ONLY this function, with NatLink disabled, see next function (below)
        get the seqsAndRules and fullResults by uncommenting 2 print lines in natlinkutils.py, lin 670.
        
        """
        natlinkmain.start_natlink()
        print('started natlink (Unimacro)')
        _number = __import__("_number simple")
        numbersgrammar = _number.thisGrammar
        
        ## 302000303:
        words = ['getal', 'drie', 'honderd', 'twee', 'miljoen', 'drie', 'honderd', 'drie']
        seqsAndRules = [(['getal'], 'testnumber'), (['drie'], '__1to99'), (['honderd'], '__hundreds'),
                        (['twee'], '__1to99'), (['miljoen'], '__millions'),
                        (['drie'], '__1to99'), (['honderd'], '__hundreds'), (['drie'], '__1to99')]
        fullResults = [('getal', 'testnumber'), ('drie', '__1to99'), ('honderd', '__hundreds'),
                        ('twee', '__1to99'), ('miljoen', '__millions'), ('drie', '__1to99'),
                        ('honderd', '__hundreds'), ('drie', '__1to99')]
        
        # now call the different functions in the resultsCallback procedure:
        numbersgrammar.callIfExists( 'gotResultsInit', (words, fullResults) )
        numbersgrammar.callRuleResultsFunctions(seqsAndRules, fullResults)
        numbersgrammar.callIfExists( 'gotResults', (words, fullResults) )
        numberExpected = '302000303'
        numbersgrammar.collectNumber()
        numberGot = numbersgrammar.number
        self.assertEqual(numberExpected, numberGot,
                          "numbers grammar gives unexpected result\nexpected: %s\ngot: %s"% (numberExpected, numberGot))
        #

        # next:
        # 3200005: (foutje: 3201005)
        words =  ['getal', 'drie', 'miljoen', 'twee', 'honderd', 'duizend', 'vijf']

        seqsAndRules = [(['getal'], 'testnumber'), (['drie'], '__1to99'), (['miljoen'], '__millions'),
                        (['twee'], '__1to99'), (['honderd'], '__hundreds'),
                        (['duizend'], '__thousands'), (['vijf'], '__1to99')]

        fullResults = [('getal', 'testnumber'), ('drie', '__1to99'), ('miljoen', '__millions'),
                       ('twee', '__1to99'), ('honderd', '__hundreds'),
                       ('duizend', '__thousands'), ('vijf', '__1to99')]

        numbersgrammar.callIfExists( 'gotResultsInit', (words, fullResults) )
        numbersgrammar.callRuleResultsFunctions(seqsAndRules, fullResults)
        numbersgrammar.callIfExists( 'gotResults', (words, fullResults) )
        numberExpected = '3200005'
        numbersgrammar.collectNumber()
        numberGot = numbersgrammar.number
        self.assertEqual(numberExpected, numberGot,
                          "numbers grammar gives unexpected result\nexpected: %s\ngot: %s"% (numberExpected, numberGot))
      
        # 324700024    (foutje: 3201005)
        words =  ['getal', 'drie', 'honderd', 'vierentwintig', 'miljoen', 'zeven', 'honderd', 'duizend', 'vierentwintig']

        seqsAndRules = [(['getal'], 'testnumber'), (['drie'], '__1to99'), (['honderd'], '__hundreds'), (['vierentwintig'], '__1to99'),
                        (['miljoen'], '__millions'),
                        (['zeven'], '__1to99'), (['honderd'], '__hundreds'), (['duizend'], '__thousands'), (['vierentwintig'], '__1to99')]

        fullResults = [('getal', 'testnumber'), ('drie', '__1to99'), ('honderd', '__hundreds'), ('vierentwintig', '__1to99'),
                       ('miljoen', '__millions'),
                       ('zeven', '__1to99'), ('honderd', '__hundreds'), ('duizend', '__thousands'), ('vierentwintig', '__1to99')]

        numbersgrammar.callIfExists( 'gotResultsInit', (words, fullResults) )
        numbersgrammar.callRuleResultsFunctions(seqsAndRules, fullResults)
        numbersgrammar.callIfExists( 'gotResults', (words, fullResults) )
        numberExpected = '324700024'
        numbersgrammar.collectNumber()
        numberGot = numbersgrammar.number
        self.assertEqual(numberExpected, numberGot,
                          "numbers grammar gives unexpected result\nexpected: %s\ngot: %s"% (numberExpected, numberGot))
       #
       
        # 3,5
        words =  ['getal', 'drie', 'komma', 'vijf']
        seqsAndRules = [(['getal'], 'testnumber'), (['drie'], '__0to99'), (['komma'], 'float'), (['vijf'], '__0to99')]
        fullResults = [('getal', 'testnumber'), ('drie', '__0to99'), ('komma', 'float'), ('vijf', '__0to99')]

        numbersgrammar.callIfExists( 'gotResultsInit', (words, fullResults) )
        numbersgrammar.callRuleResultsFunctions(seqsAndRules, fullResults)
        numbersgrammar.callIfExists( 'gotResults', (words, fullResults) )
        numberExpected = '3,5'
        numbersgrammar.collectNumber()
        numberGot = numbersgrammar.number
        self.assertEqual(numberExpected, numberGot,
                          "numbers grammar gives unexpected result\nexpected: %s\ngot: %s"% (numberExpected, numberGot))
       
    def ttttestNumbersExtendedFixedLengthNld(self):
        """test the numbers grammar rules as written in natlinkutilsbj
        
        attach to the _number grammar, with language dutch (translated word for number is "getal").
        (this grammar must be in the Unimacro directory)
        please remove (if applicable) _number_simple.py
        
        handle with care, run or debug ONLY this function, with NatLink disabled, see next function (below)
        
        
        """
        natlinkmain.start_natlink()
        print('started natlink (Unimacro)')
        _number = __import__("_number extended")
        numbersgrammar = _number.thisGrammar
        
        ## example fixed length punt (point) + four digits,
        ## to be dictated as "two thousand" ("twee duizend")
        words = ['punt', 'twee', 'duizend']
        fullResults = [('punt', 'numberaztwo'), ('twee', '__2to9before'), ('duizend', '__thousandslimited')]
        seqsAndRules= [(['punt'], 'numberaztwo'), (['twee'], '__2to9before'), (['duizend'], '__thousandslimited')]

        
        
        # ## 8623, note we test this inside the rule numberazone, initially developed for a user in Amsterdam Zuid
        # words = ['zesentachtig', 'drie', 'drie\xebntwintig']  #
        # seqsAndRules = [(['zesentachtig'], 'numberazone'), (['drie\xebntwintig'], 'numbertwodigits')]
        # fullResults = [('zesentachtig', 'numberazone'), ('drie\xebntwintig', 'numbertwodigits')]
        
        # now call the different functions in the resultsCallback procedure:
        numbersgrammar.callIfExists( 'gotResultsInit', (words, fullResults) )
        numbersgrammar.callRuleResultsFunctions(seqsAndRules, fullResults)
        numbersgrammar.callIfExists( 'gotResults', (words, fullResults) )
        numberExpected = '.2000'
        numbersgrammar.collectNumber()
        numberGot = numbersgrammar.number
        self.assertEqual(numberExpected, numberGot,
                          "numbers grammar gives unexpected result\nexpected: %s\ngot: %s"% (numberExpected, numberGot))
        #

        # next:
        # 3200005: (foutje: 3201005)
        words =  ['getal', 'drie', 'miljoen', 'twee', 'honderd', 'duizend', 'vijf']

        seqsAndRules = [(['getal'], 'testnumber'), (['drie'], '__1to99'), (['miljoen'], '__millions'),
                        (['twee'], '__1to99'), (['honderd'], '__hundreds'),
                        (['duizend'], '__thousands'), (['vijf'], '__1to99')]

        fullResults = [('getal', 'testnumber'), ('drie', '__1to99'), ('miljoen', '__millions'),
                       ('twee', '__1to99'), ('honderd', '__hundreds'),
                       ('duizend', '__thousands'), ('vijf', '__1to99')]

        numbersgrammar.callIfExists( 'gotResultsInit', (words, fullResults) )
        numbersgrammar.callRuleResultsFunctions(seqsAndRules, fullResults)
        numbersgrammar.callIfExists( 'gotResults', (words, fullResults) )
        numberExpected = '3200005'
        numbersgrammar.collectNumber()
        numberGot = numbersgrammar.number
        self.assertEqual(numberExpected, numberGot,
                          "numbers grammar gives unexpected result\nexpected: %s\ngot: %s"% (numberExpected, numberGot))
      
        # 324700024    (foutje: 3201005)
        words =  ['getal', 'drie', 'honderd', 'vierentwintig', 'miljoen', 'zeven', 'honderd', 'duizend', 'vierentwintig']

        seqsAndRules = [(['getal'], 'testnumber'), (['drie'], '__1to99'), (['honderd'], '__hundreds'), (['vierentwintig'], '__1to99'),
                        (['miljoen'], '__millions'),
                        (['zeven'], '__1to99'), (['honderd'], '__hundreds'), (['duizend'], '__thousands'), (['vierentwintig'], '__1to99')]

        fullResults = [('getal', 'testnumber'), ('drie', '__1to99'), ('honderd', '__hundreds'), ('vierentwintig', '__1to99'),
                       ('miljoen', '__millions'),
                       ('zeven', '__1to99'), ('honderd', '__hundreds'), ('duizend', '__thousands'), ('vierentwintig', '__1to99')]

        numbersgrammar.callIfExists( 'gotResultsInit', (words, fullResults) )
        numbersgrammar.callRuleResultsFunctions(seqsAndRules, fullResults)
        numbersgrammar.callIfExists( 'gotResults', (words, fullResults) )
        numberExpected = '324700024'
        numbersgrammar.collectNumber()
        numberGot = numbersgrammar.number
        self.assertEqual(numberExpected, numberGot,
                          "numbers grammar gives unexpected result\nexpected: %s\ngot: %s"% (numberExpected, numberGot))
       #
       
        # 3,5
        words =  ['getal', 'drie', 'komma', 'vijf']
        seqsAndRules = [(['getal'], 'testnumber'), (['drie'], '__0to99'), (['komma'], 'float'), (['vijf'], '__0to99')]
        fullResults = [('getal', 'testnumber'), ('drie', '__0to99'), ('komma', 'float'), ('vijf', '__0to99')]

        numbersgrammar.callIfExists( 'gotResultsInit', (words, fullResults) )
        numbersgrammar.callRuleResultsFunctions(seqsAndRules, fullResults)
        numbersgrammar.callIfExists( 'gotResults', (words, fullResults) )
        numberExpected = '3,5'
        numbersgrammar.collectNumber()
        numberGot = numbersgrammar.number
        self.assertEqual(numberExpected, numberGot,
                          "numbers grammar gives unexpected result\nexpected: %s\ngot: %s"% (numberExpected, numberGot))
       


       
    def xxxxtestNumbersSimpleGrammarEnx(self):
        """test the numbers grammar rules as written in natlinkutilsbj
        
        
        attach to the _number simple.py grammar, with language english (this grammar must be in the Unimacro directory)
        please remove (if applicable) _number extended.py

        !!Enable ONLY this test function, disable NatLink (leaving Unimacro and possibly Vocola enabled)
        !!enable the "start_natlink" line in def connect and
        then restart Dragon and run this module.
        
        Note the test function writes the number into this file, so leave the cursor here or after a comment
        before running the function!! Or you comment out the line self.outputNumber() (line 99) in _number simple.py.

        """
        natlinkmain.start_natlink()
        print('started natlink (Unimacro)')
        
        _number = __import__("_number simple")
        numbersgrammar = _number.thisGrammar
        
        
        ## testing leading 0: 03, oh three:
        words = ['Number', 'oh', 'three']
        seqsAndRules = [(['Number'], 'testnumber'), (['oh', 'three'], '__0to99')]
        fullResults =[('Number', 'testnumber'), ('oh', '__0to99'), ('three', '__0to99')]

        # now call the different functions in the resultsCallback procedure:
        numbersgrammar.callIfExists( 'gotResultsInit', (words, fullResults) )
        numbersgrammar.callRuleResultsFunctions(seqsAndRules, fullResults)
        numbersgrammar.callIfExists( 'gotResults', (words, fullResults) )
        numberExpected = '03'
        numberGot = numbersgrammar.number
        self.assertEqual(numberExpected, numberGot,
                          "numbers grammar gives unexpected result\nexpected: %s\ngot: %s"% (numberExpected, numberGot))


        ## 302000303:
        words = ['Number', 'three', 'hundred', 'two', 'million', 'three', 'hundred', 'three']
        seqsAndRules = [(['Number'], 'testnumber'), (['three'], '__1to99'), (['hundred'], '__hundreds'), (['two'], '__1to99'),
                        (['million'], '__millions'),
                        (['three'], '__1to99'), (['hundred'], '__hundreds'), (['three'], '__1to99')]
        fullResults =[('Number', 'testnumber'), ('three', '__1to99'), ('hundred', '__hundreds'), ('two', '__1to99'),
            ('million', '__millions'),
            ('three', '__1to99'), ('hundred', '__hundreds'), ('three', '__1to99')]

        # now call the different functions in the resultsCallback procedure:
        numbersgrammar.callIfExists( 'gotResultsInit', (words, fullResults) )
        numbersgrammar.callRuleResultsFunctions(seqsAndRules, fullResults)
        numbersgrammar.callIfExists( 'gotResults', (words, fullResults) )
        numberExpected = '302000303'
        numberGot = numbersgrammar.number
        self.assertEqual(numberExpected, numberGot,
                          "numbers grammar gives unexpected result\nexpected: %s\ngot: %s"% (numberExpected, numberGot))


    def xxxtestCalculatorNld(self):
        """test the numbers grammar rules in calculator grammar
        
        Note the precautions stated above around line 390.
        This is for testing the _calculator grammar in the debugger

        """
        natlinkmain.start_natlink()
        print('started natlink (Unimacro)')
        
        _calc = __import__("_calculator")
        calcgrammar = _calc.thisGrammar
        
        
        ## testing  simple calculation (dutch):
        seqsAndRules = [(['bereken'], 'calculation'), (['drie'], '__0to9'), (['plus'], 'operator'),
            (['vijf'], '__0to9'), (['is gelijk aan'], 'calculation')]
        fullResults = [('bereken', 'calculation'), ('drie', '__0to9'), ('plus', 'operator'), ('vijf', '__0to9'), ('is gelijk aan', 'calculation')]
        words = ['bereken', 'drie', 'plus', 'vijf', 'is gelijk aan']
        words = ['reken uit', 'drie', 'keer', 'min', 'vier', 'is gelijk aan']
        seqsAndRules = [(['reken uit'], 'calcnormal'), (['drie'], '__0to9'), (['keer', 'min'], 'operator'), (['vier'], '__0to9'), (['is gelijk aan'], 'calcnormal')]
        fullResults = [('reken uit', 'calcnormal'), ('drie', '__0to9'), ('keer', 'operator'), ('min', 'operator'), ('vier', '__0to9'), ('is gelijk aan', 'calcnormal')]

        # now call the different functions in the resultsCallback procedure
        # 
        calcgrammar.callIfExists( 'gotResultsInit', (words, fullResults) )
        calcgrammar.callRuleResultsFunctions(seqsAndRules, fullResults)
        calcgrammar.callIfExists( 'gotResults', (words, fullResults) )
        numberExpected = '03'
        numberGot = calcgrammar.number
        self.assertEqual(numberExpected, numberGot,
                          "calc grammar gives unexpected result\nexpected: %s\ngot: %s"% (numberExpected, numberGot))

    def xxxxtestKeystrokesGrammarEnx(self):
        """test the keystrokes grammar

        with language english (this grammar must be in the Unimacro directory)
        the inactive mode seemed not to be working. Deactivate was not enough. Hard to test.
        But hopefully solved, Quintijn, September 26, 2013...

        !!Enable ONLY this test function, disable NatLink (leaving Unimacro and possibly Vocola enabled)
        !!enable the "start_natlink" line in def connect and
        then restart Dragon and run this module.
        
        Note the test function writes the number into this file, so leave the cursor here or after a comment
        before running the function!! Or you comment out the line self.outputNumber() (line 99) in _number simple.py.

        """
        natlinkmain.start_natlink()
        print('started natlink (Unimacro)')
        import _keystrokes
        kgrammar = _keystrokes.thisGrammar
        
        
        # the Backspace gives an error:        
        words = ['Backspace']
        fullResults = [('Backspace', 'repkey')]
        seqsAndRules = [(['Backspace'], 'repkey')]

        # now call the different functions in the resultsCallback procedure:
        moduleInfo = natlink.getCurrentModule()
        # initialise things in gotBegin
        kgrammar.callIfExists( 'gotBegin', (moduleInfo,) )
        # and run the rules:
        kgrammar.callIfExists( 'gotResultsInit', (words, fullResults) )
        kgrammar.callRuleResultsFunctions(seqsAndRules, fullResults)
        kgrammar.callIfExists( 'gotResults', (words, fullResults) )
        pass
        ##

    #def xxxxtestFolderGrammarSiteSpecificationNld(self):
    #    """test the import of some site module. Specific option for Quintijn
    #    
    #    !!Enable ONLY this test function, disable NatLink (leaving Unimacro and possibly Vocola enabled)
    #    !!enable the "start_natlink" line in def connect and
    #    then restart Dragon and run this module.
    #    
    #    """
    #    natlinkmain.start_natlink()
    #    print 'started natlink (Unimacro)'
    #    import _folders
    #    fgrammar = _folders.thisGrammar
    #    fgrammar.getSiteInstance('sg')
    # if this error happens again, ensure utilsqh and inivars are same version as in
    # QH's miscqh folder. (Sept 2013)
    #    pass


    def xxxxtestControlGrammarNld(self):
        """test the reload of the control grammar
        
        The obsolete words seem to be reversed.

        !!Enable ONLY this test function, disable NatLink (leaving Unimacro and possibly Vocola enabled)
        !!enable the "start_natlink" line in def connect and
        then restart Dragon and run this module.
        
        Note the test function writes the number into this file, so leave the cursor here or after a comment
        before running the function!! Or you comment out the line self.outputNumber() (line 99) in _number simple.py.Zwitserland kiest Rooks hallo

        This test was because at reload time the self.gramSpec instance variable was used for translation instead of
        self.__class__.gramSpec.
        
        Next lines of test are not very sensible. Problem was at natlinkutilsbj line 2324, QH sept 2013

        """
        natlinkmain.start_natlink()
        print('started natlink (Unimacro)')
        import _control
        cgrammar = _control.utilGrammar  # why this name?
        print('gramSpec: %s'% cgrammar.gramSpec)
        words = ['schakel', 'in', 'toetsen']
        fullResults = [('schakel', 'switch'), ('in', 'switch'), ('toetsen', 'switch')]
        seqsAndRules = [(['schakel', 'in', 'toetsen'], 'switch')]

        moduleInfo = natlink.getCurrentModule()
        cgrammar.checkInifile()

        # now call the different functions in the resultsCallback procedure:
        print('after second initialise gramSpec: %s'% cgrammar.gramSpec)
        pass
        ##

    
    def tttestGrammarRepeatedTranslationsAndLoads(self):
        """test a simple grammar with rules that are translated, do multiple loads to check stability
        
        """
        class TestGrammar(natbj.IniGrammar):
            
            gramSpec = '<reload> exported = reload translated grammar;'
            
            def __init__(self):
                natbj.IniGrammar.__init__(self)

        testGram = TestGrammar()
        iniSpec = {'grammar name': {'name':'reload test'},
                   'grammar words':
            {'reload': ['opnieuw laden'],
 'rule': ['regel'],
 'test': ['test', 'testing'],
 'translated': ['vertaald', 'translated']}}
        testGram.ini = self.makeInifile('testreloadtranslated.ini', iniSpec=iniSpec)

        # test the translation words dictionary from fake inifile (iniSpec) above:        
        expGramSpec = ['<four> exported = rule four;']
        expGramScanList = []
        expDict =  {'reload': ['opnieuw laden'],
 'rule': ['regel'],
 'test': ['test', 'testing'],
 'translated': ['vertaald', 'translated']}
        gotDict = testGram.getDictOfGrammarWordsTranslations()
        self.assert_equal(expDict, gotDict,  "translated words dict not as expected")
        
        # do the translation step:
        gotGramSpec = testGram.translateGrammar(testGram.gramSpec)
        expGramSpec =  "<reload> exported = 'opnieuw laden' (vertaald|translated) grammar;"
        self.assert_equal(expGramSpec, gotGramSpec,  "translated grammar was not as expected")
        expGramWords =  {'reload': ['opnieuw laden'], 'translated': ['vertaald', 'translated']}
        gotGramWords = testGram.gramWords
        self.assert_equal(expGramWords, gotGramWords,  "gramwords dict after translation not as expected")

        gotGotGramSpec = testGram.translateGrammar(testGram.gramSpec)
        self.assert_equal(gotGramSpec, gotGotGramSpec, "twice translated grammar should be the same as once translated")

        gotGotGramWords = testGram.gramWords
        self.assert_equal(expGramWords, gotGotGramWords,  "gramwords dict after double translation not as expected")
                   
        # clean up
        testGram.unload()


    def tttestGrammarTranslation(self):
        """test a simple grammar with rules that are translated
        
        either other language or with synonyms
        """
        class TestGrammar(natbj.IniGrammar):
            
            gramSpec = '<four> exported = rule four;'
            
            def __init__(self):
                natbj.IniGrammar.__init__(self)

        testGram = TestGrammar()
        iniSpec = {'grammar name': {'name':'test rule four'},
                   'grammar words':
            {'four':'four;for', 'rule': 'regel'}}
        testGram.ini = self.makeInifile('testrulefour.ini', iniSpec=iniSpec)

        # test the translation words dictionary from fake inifile (iniSpec) above:        
        expGramSpec = ['<four> exported = rule four;']
        expGramScanList = []
        expDict =  {'four': ['four', 'for'], 'rule': ['regel']}
        gotDict = testGram.getDictOfGrammarWordsTranslations()
        self.assert_equal(expDict, gotDict,  "translated words dict not as expected")
        
        # do the translation step:
        gotGramSpec = testGram.translateGrammar(testGram.gramSpec)
        expGramSpec = '<four> exported = regel (four|for);';
        self.assert_equal(expGramSpec, gotGramSpec,  "translated grammar was not as expected")
        
        ### now try small changes in the rule ( no extra parens needed):
        testGram.gramSpec = '<fourparens> exported = rule (four);'
        gotGramSpec = testGram.translateGrammar(testGram.gramSpec)
        expGramSpec = '<fourparens> exported = regel (four|for);';
        self.assert_equal(expGramSpec, gotGramSpec,  "translated no extra parens needed grammar was not as expected")
        ## try other variants of no parens needed
        testGram.gramSpec = '<fourparens2> exported = rule (four|five|six);'
        gotGramSpec = testGram.translateGrammar(testGram.gramSpec)
        expGramSpec = '<fourparens2> exported = regel (four|for|five|six);';
        self.assert_equal(expGramSpec, gotGramSpec,  "translated no extra parens needed grammar was not as expected")
        # another:
        testGram.gramSpec = '<fourparens3> exported = rule [three|four|five|six];'
        gotGramSpec = testGram.translateGrammar(testGram.gramSpec)
        expGramSpec = '<fourparens3> exported = regel [three|four|for|five|six];';
        self.assert_equal(expGramSpec, gotGramSpec,  "translated no extra parens needed grammar was not as expected")
        # another:
        testGram.gramSpec = '<fourparens4> exported = rule [four];'
        gotGramSpec = testGram.translateGrammar(testGram.gramSpec)
        expGramSpec = '<fourparens4> exported = regel [four|for];';
        self.assert_equal(expGramSpec, gotGramSpec,  "translated no extra parens needed grammar was not as expected")
        
        
        expGramWords =  {'four': ['four', 'for'], 'rule': ['regel']}
        gotGramWords = testGram.gramWords
        self.assert_equal(expGramWords, gotGramWords,  "gramwords dict after translation not as expected")
        
               
        # clean up
        testGram.unload()


    def tttestGrammarTranslationComplicated(self):
        """test a little bit more involved grammar with rules that are translated
        
        either other language or with synonyms
        """
        class TestGrammar(natbj.IniGrammar):
            
            gramSpec = '''#demo translation
<one> exported = rule <two> ['a lot'] EXTRA;
#more rules:
<two> = Exported with {two} {one} [and ['a lot'|little]] more; # additional comment
#try to do my best'''
            
            def __init__(self):
                natbj.IniGrammar.__init__(self)

        testGram = TestGrammar()
        iniSpec = {'grammar name': {'name':'test rule one two'},
                   'grammar words':
            {'four':'four;for',
             'rule': 'regel',
             'one': 'een',
             'Exported': 'Uitgevoerd|"een beetje Afgevoerd"',
             'extra': 'Extra',
             'A lot':'veel',
             'more': 'more',
             'little': '"een beetje"|weinig'}}
        testGram.ini = self.makeInifile('testruleonetwo.ini', iniSpec=iniSpec)

        # test the translation words dictionary from fake inifile (iniSpec) above:        
        expDict =     {'a lot': ['veel'],
 'exported': ['Uitgevoerd', 'een beetje Afgevoerd'],
 'extra': ['Extra'],
 'four': ['four', 'for'],
 'little': ['een beetje', 'weinig'],
 'one': ['een'],
 'rule': ['regel']}
        gotDict = testGram.getDictOfGrammarWordsTranslations()
        self.assert_equal(expDict, gotDict,  "translated words dict not as expected")
        
        # do the translation step:
        gotGramSpec = testGram.translateGrammar(testGram.gramSpec)
        expGramSpec = '''#demo translation\n<one> exported = regel <two> ['veel'] Extra;\n#more rules:\n<two> = (Uitgevoerd|'een beetje Afgevoerd') with {two} {one} [and ['veel'|'een beetje'|weinig]] more; # additional comment\n#try to do my best'''
        self.assert_equal(expGramSpec, gotGramSpec,  "translated grammar was not as expected")
        testGram.load(gotGramSpec)
        expRules = ['one']
        gotRules = testGram.validRules
        self.assert_equal(expRules, gotRules, "translated grammar does not load into the correct rules")
               
        # clean up
        testGram.unload()

    def testGrammarTranslationInifileHandling(self):
        """test the changes of translated words and obsolete words in the inifile
        
        """
        class TestGrammar(natbj.IniGrammar):
            
            gramSpec = '''#grammar with simple translation
<simple> exported = rule one;
'''
            
            def __init__(self):
                natbj.IniGrammar.__init__(self)

        testGram = TestGrammar()
        iniSpec = {'grammar name': {'name':'test inifile handling'},
                   }
        testGram.ini = self.makeInifile('testinifilehandling.ini', iniSpec=iniSpec)

        # test the translation words dictionary from fake inifile (iniSpec) above:        
        expDict =  {}
        gotDict = testGram.getDictOfGrammarWordsTranslations()
        self.assert_equal(expDict, gotDict,  "translated words dict not as expected")
        
        # no translation yet:
        gotGramSpec = testGram.translateGrammar(testGram.gramSpec)
        expGramSpec = None  # no translation yet
        self.assert_equal(expGramSpec, gotGramSpec,  "no translated grammar at this moment")
        
        expIniSpec =    {'grammar name': {'name': 'test inifile handling'}}

        gotIniSpec = testGram.ini.toDict()
        self.assert_equal(expIniSpec, gotIniSpec, "non-translated grammar does not produce expected ini file")
        
        ## make an obsolete word and translate again:
        testGram.gramSpec = '''<simple> exported = rule;'''
        gotGramSpec = testGram.translateGrammar(testGram.gramSpec)
        expGramSpec = None  # no translation yet

        self.assert_equal(expGramSpec, gotGramSpec,  "no translated grammar at this moment")
      
        expIniSpec =    {'grammar name': {'name': 'test inifile handling'}}
        gotIniSpec = testGram.ini.toDict()
        self.assert_equal(expIniSpec, gotIniSpec, "non-translated grammar does not produce expected ini file")


        ## now introduce a synonym
        testGram.gramSpec = '''<simple> exported = rule one;'''
        iniSpec = {'grammar name': {'name':'test inifile handling'},
                'grammar words': {'one': 'synonym'}
                   }
        testGram.ini = self.makeInifile('testinifilehandling.ini', iniSpec=iniSpec)
        
        gotGramSpec = testGram.translateGrammar(testGram.gramSpec)
        expGramSpec =  '<simple> exported = rule synonym;'

        self.assert_equal(expGramSpec, gotGramSpec,  "no translated grammar at this moment")
      
      
        ## note the language is here "zyx", so not enx of nld:      
        expIniSpec =        {'grammar name': {'name': 'test inifile handling'},
 'grammar non translated words': {'info1': 'These grammar words can be translated.',
                                   'info2': 'See http://qh.antenna.nl/unimacro/features/translations for more info',
                                   'words': ['rule']},
 'grammar words': {'one': 'synonym'}}

        gotIniSpec = testGram.ini.toDict()
        self.assert_equal(expIniSpec, gotIniSpec, "translated grammar does not produce expected ini file")


        ## remove the translated word:
        testGram.gramSpec = '''<simple> exported = rule;'''
        # go on with the previous inifile        
        
        gotGramSpec = testGram.translateGrammar(testGram.gramSpec)
        expGramSpec =  None # again no translation

        self.assert_equal(expGramSpec, gotGramSpec,  "no translated grammar at this moment")
      
        expIniSpec =       {'grammar name': {'name': 'test inifile handling'},
 'grammar non translated words': {'info1': 'These grammar words can be translated.',
                                   'info2': 'See http://qh.antenna.nl/unimacro/features/translations for more info',
                                   'words': ['rule']},
 'grammar obsolete words': {'one': ['synonym']}}

        gotIniSpec = testGram.ini.toDict()
        self.assert_equal(expIniSpec, gotIniSpec, "non translated grammar with obsolete words does not produce expected ini file")

        ## make translated word active again, catching the translation:
        testGram.gramSpec = '''<simple> exported = rule one;'''
        # go on with the previous inifile        
        
        gotGramSpec = testGram.translateGrammar(testGram.gramSpec)
        # if no translation, None is returned
        expGramSpec =  None  ### u'<simple> exported = rule synonym;'

        self.assert_equal(expGramSpec, gotGramSpec,  "no translated grammar at this moment")
      
        expIniSpec =    {'grammar name': {'name': 'test inifile handling'},
 'grammar non translated words': {'info1': 'These grammar words can be translated.',
                                   'info2': 'See http://qh.antenna.nl/unimacro/features/translations for more info',
                                   'words': ['rule']},
 'grammar obsolete words': {'one': ['synonym']}}
        gotIniSpec = testGram.ini.toDict()
        self.assert_equal(expIniSpec, gotIniSpec, "non translated grammar with obsolete words does not produce expected ini file")


        ## make translated words active again, catching the translation:
        testGram.gramSpec = '''<simple> exported = rule one;'''
        ##
        ## augment ini spec with items that can be removed:
        ## identical words are NOT remembered!!
        ##
        iniSpec =     {'grammar name': {'name': 'test inifile handling'},
'grammar non translated words': {'info1': 'These grammar words can be changed if you want synonyms for them.',
                                  'info2': 'See http://qh.antenna.nl/unimacro/features/translations for more info',
                                  'words': ['rule']},
'grammar words': {'one': ['synonym', 'one'], 'rule': ['rule']},
'grammar obsolete words': {'two': ['keep'], 'three': ['three|also keep'], 'four': ['four']}}

        testGram.ini = self.makeInifile('testinifilehandling.ini', iniSpec=iniSpec)
        
        gotGramSpec = testGram.translateGrammar(testGram.gramSpec)
        expGramSpec =  '<simple> exported = rule (synonym|one);'

        self.assert_equal(expGramSpec, gotGramSpec,  "translated grammar with synonyms not correct")
      
        expIniSpec =     {'grammar name': {'name': 'test inifile handling'},
 'grammar non translated words': {'info1': 'These grammar words can be translated.',
                                   'info2': 'See http://qh.antenna.nl/unimacro/features/translations for more info',
                                   'words': ['rule']},
 'grammar obsolete words': {'three': ['three|also keep'], 'two': ['keep']},
 'grammar words': {'one': ['synonym', 'one']}}

        gotIniSpec = testGram.ini.toDict()
        self.assert_equal(expIniSpec, gotIniSpec, "non translated grammar with obsolete words does not produce expected ini file")


        ## now translated also the last word of the grammar:
        testGram.ini.set('grammar words', 'rule', 'regel')
        testGram.ini.write()
        pass
        gotGramSpec = testGram.translateGrammar(testGram.gramSpec)
        expGramSpec =  '<simple> exported = rule (synonym|one);'
        
        expIniSpec =  {'grammar name': {'name': 'test inifile handling'},
 'grammar obsolete words': {'three': ['three|also keep'], 'two': ['keep']},
 'grammar words': {'one': ['synonym', 'one'], 'rule': 'regel'}}

        gotIniSpec = testGram.ini.toDict()
        self.assert_equal(expIniSpec, gotIniSpec, "non translated grammar with obsolete words does not produce expected ini file")
 

    def tttestGrammarTranslationTwoLinesDoubleWord(self):
        """test a little bit more involved grammar, try if additional newlines are caugth and double words correctly translated
        
        """
        class TestGrammar(natbj.IniGrammar):
            
            gramSpec = '''#test comment with translation
<doubleword> exported = rule <two> ['right click'|"double click"];
<two> = 'another rule' exported;
'''
            
            def __init__(self):
                natbj.IniGrammar.__init__(self)

        testGram = TestGrammar()
        iniSpec = {'grammar name': {'name':'test rule doubleword'},
                   'grammar words':
            {'right click':'rechts klik; rechter klik',
             'double click': 'dubbelklik',
             'rule': 'regel',
             'another rule': 'nog een regel'}}
        testGram.ini = self.makeInifile('testruledoubleword.ini', iniSpec=iniSpec)

        # test the translation words dictionary from fake inifile (iniSpec) above:        
        expDict =        {'another rule': ['nog een regel'],
 'double click': ['dubbelklik'],
 'right click': ['rechts klik', 'rechter klik'],
 'rule': ['regel']}
        gotDict = testGram.getDictOfGrammarWordsTranslations()
        self.assert_equal(expDict, gotDict,  "translated words dict not as expected")
        
        # do the translation step:
        gotGramSpec = testGram.translateGrammar(testGram.gramSpec)
        expGramSpec =  '''#test comment with translation
<doubleword> exported = regel <two> ['rechts klik'|'rechter klik'|"dubbelklik"];
<two> = 'nog een regel' exported;'''

        self.assert_equal(expGramSpec, gotGramSpec,  "translated grammar was not as expected")
        testGram.load(gotGramSpec)
        expRules = ['doubleword']
        gotRules = testGram.validRules
        self.assert_equal(expRules, gotRules, "translated grammar does not load into the correct rules")
        
        # use for testing the showInifile function:
        #testGram.showInifile()
        
               
        # clean up
        testGram.unload()


def log(t):
    """log to print and file if present

    note print depends on the state of natlink: where is goes or disappears...
    I have no complete insight is this, but checking the logfile afterwards
    always works (QH)
    """
    print(t)
    if logFile:
        logFile.write(t + '\n')
    
#---------------------------------------------------------------------------
# run
#
# This is the main entry point.  It will connect to NatSpeak and perform
# a series of tests.  In the case of an error, it will cleanly disconnect
# from NatSpeak and print the exception information,
def dumpResult(testResult, logFile):
    """dump into 
    """
    if testResult.wasSuccessful():
        mes = "all succesful"
        logFile.write(mes)
        return
    logFile.write('\n--------------- errors -----------------\n')
    for case, tb in testResult.errors:
        logFile.write('\n---------- %s --------\n'% case)
        logFile.write(tb)
        
    logFile.write('\n--------------- failures -----------------\n')
    for case, tb in testResult.failures:
        logFile.write('\n---------- %s --------\n'% case)
        logFile.write(tb)

    


logFile = None

def run():
    global logFile, natconnectOption
    logFile = open(logFileName, "w")
    log("log messages to file: %s"% logFileName)
    log('starting unittestNatlink')
    # trick: if you only want one or two tests to perform, change
    # the test names to her example def tttest....
    # and change the word 'test' into 'tttest'...
    # do not forget to change back and do all the tests when you are done.
    suite = unittest.makeSuite(UnittestIniGrammar, 'test')
##    natconnectOption = 0 # no threading has most chances to pass...
    log('\nstarting tests with threading: %s\n'% natconnectOption)
    result = unittest.TextTestRunner().run(suite)
    dumpResult(result, logFile=logFile)
    
    logFile.close()

if __name__ == "__main__":
    run()
