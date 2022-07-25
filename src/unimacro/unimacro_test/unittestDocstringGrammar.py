#
# Python Macro Language for Dragon NaturallySpeaking
#   (c) Copyright 1999 by Joel Gould
#   Portions (c) Copyright 1999 by Dragon Systems, Inc.
#
# unittestDocstringGrammar.py
#   This script performs some basic tests of the NatLink but
#   with the DocstringGrammar subclass.
#   This also tests features of IniGrammar, BrowsableGrammar and GrammarX
#   being the chain of grammars leading up to GrammarBase
#
# run from a (preferably clean) US user profile, easiest from IDLE.
# do not run from pythonwin. 
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

natconnectOption = 0 # or 1 for threading, 0 for not. Seems to make difference
                     # with spurious error (if set to 1), missing gotBegin and all that...
logFileName = os.path.join(thisDir, "testresult.txt")

#---------------------------------------------------------------------------
# These tests should be run after we call natConnect
# no reopen user at each test anymore..
# no default open window (open window will be the calling program)
# default .ini files pop up when you first run this test. just ignore them.
class UnittestDocstringGrammar(TestCaseWithHelpers.TestCaseWithHelpers):
    def setUp(self):
        if not natlink.isNatSpeakRunning():
            raise TestError('NatSpeak is not currently running')
        self.connect()
        self.user = natlink.getCurrentUser()[0]
        self.setMicState = "off"

    def tearDown(self):
        try:
            # give message:
            self.setMicState = "off"
            # kill things
            self.clearTestFiles()
        finally:
            self.disconnect()

        
    def connect(self):
        # start with 1 for thread safety when run from pythonwin:
        natlink.natConnect(natconnectOption)

    def disconnect(self):
        natlink.natDisconnect()
        
    def log(self, t):
        # only log to file:
        log(t)

    def clearTestFiles(self):
        """remove .py and .pyc files from the natlinkmain test

        """
        return
        # try to remove __main__.ini, but gives unexpected windows popping up
        #userdir = status.getUnimacroUserDirectory()
        #language = status.getLanguage()
        #print 'userdir: %s, language: %s'% (userdir, language)
        #userinidir = os.path.join(userdir, '%s_inifiles'%language)
        #if os.path.isdir(userinidir):
        #    mainfile = os.path.join(userinidir, '__main__.ini')
        #    if os.path.isfile(mainfile):
        #        os.remove(mainfile)
        #else:
        #    raise OSError("clearTestFiles, should be a valid directory: %s"% userinidir)

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
    
    def testGrammarActivateRules(self):
        """test a simple grammar with three exported rules.
        
        test the activation/deactivation of these rules, like in unittestNatlink
        (the testGrammar function)
        """
        class TestGrammar(natbj.DocstringGrammar):
            gramSpec = '<four> exported = rule four;'
            
            def __init__(self):
                natbj.DocstringGrammar.__init__(self)
                self.resetExperiment()

            def resetExperiment(self):
                self.sawBegin = 0
                self.recogType = None
                self.words = []
                self.fullResults = []
                self.error = None

            def gotBegin(self,moduleInfo):
                if self.sawBegin > nTries:
                    self.error = 'Command grammar called gotBegin twice'
                self.sawBegin += 1
                if moduleInfo != natlink.getCurrentModule():
                    self.error = 'Invalid value for moduleInfo in GrammarBase.gotBegin'

            def gotResultsObject(self,recogType,resObj):
                if self.recogType:
                    self.error = 'Command grammar called gotResultsObject twice'
                self.recogType = recogType
            def rule_one(self, words):
                'rule one <two>'
                pass
            def subrule_two(self, words):
                'subrule two'
                pass
            def rule_three(self, words):
                'rule three'
                pass

            def gotResults(self,words,fullResults):
                if self.words:
                    self.error = 'Command grammar called gotResults twice'
                self.words = words
                self.fullResults = fullResults

            def checkExperiment(self,sawBegin,recogType,words,fullResults):
                if self.error:
                    raise TestError(self.error)
                if self.sawBegin != sawBegin:
                    raise TestError('Unexpected result for GrammarBase.sawBegin\n  Expected %d\n  Saw %d'%(sawBegin,self.sawBegin))
                if self.recogType != recogType:
                    raise TestError('Unexpected result for GrammarBase.recogType\n  Expected %s\n  Saw %s'%(recogType,self.recogType))
                if self.words != words:
                    raise TestError('Unexpected result for GrammarBase.words\n  Expected %s\n  Saw %s'%(repr(words),repr(self.words)))
                if self.fullResults != fullResults:
                    raise TestError('Unexpected result for GrammarBase.fullResults\n  Expected %s\n  Saw %s'%(repr(fullResults),repr(self.fullResults)))
                self.resetExperiment()
       
        testActiveRules = self.doTestActiveRules
        testForException = self.doTestForException
        testGram = TestGrammar()
        
        expGramSpec =  \
'''<one> exported = rule one <two>;
    <two> = subrule two;
<three> exported = rule three;
<four> exported = rule four;'''
        self.assert_equal(expGramSpec, testGram.gramSpec,"gramspec not as expected")
        
        testGram.load(testGram.gramSpec)
        testGram.activateAll()
        testActiveRules(testGram, ['one', 'three', 'four'])

        testGram.deactivateAll()
        testActiveRules(testGram, [])
        prev = None
        for rule in 'three', 'four', 'one', 'four', 'three':
            # activate:
            testGram.activate(rule)
            if prev:
                expList = [prev, rule]
            else:
                expList = [rule]
            testActiveRules(testGram, expList)
            # activate after all active:
            testGram.activateAll()
            testForException(GrammarError, "testGram.activate('%s')"% rule, locals())
            # activate after all unactive:
            testGram.deactivateAll()
            testGram.activate(rule)
            testActiveRules(testGram, [rule])
            prev = rule

        rule = 'one'
        testGram.activate(rule)
        testForException(GrammarError, "testGram.activate('%s')"% rule, locals())
        testGram.deactivateAll()
        testActiveRules(testGram, [])

        for SET in (['one', 'three', 'four'], ['three'], ['one', 'three', 'four'], ['one', 'three']):
            testGram.activateSet(SET)
            testActiveRules(testGram, SET)
            ##with original version of natlinkutils.py you get:
            ##AssertionError: Active rules not as expected:
            ##expected: ['three'], got: ['one', 'three']
            ##fix around line 420 (copy.copy) in natlinkutils.py, QH
    
        ## test exceptlist feature:
        ## ['one', 'three', 'four'] are the exported rules
        testGram.activateAll(exceptlist=['one'])
        testActiveRules(testGram, ['three', 'four'])
        testGram.activateAll(exceptlist=None)
        testActiveRules(testGram, ['one', 'three', 'four'])
        testGram.deactivateAll()
        testActiveRules(testGram, [])
        # extra in exceptlist does not matter:
        testGram.activateAll(exceptlist=['one', 'two', 'three', 'four', 'five'])
        testActiveRules(testGram, [])
        testGram.activateAll(exceptlist=['three', 'four'])
        testActiveRules(testGram, ['one'])
        testGram.activateAll(exceptlist=['one', 'three'])
        testActiveRules(testGram, ['four'])
        
        

        # try a few illegal grammars to make sure they are reported properly (we
        # already tested the grammar parser so this does not have to be
        # exhaustive)
        testGram.unload()
        testForException(SyntaxError,"testGram.load('badrule;')",locals())
        testForException(GrammarError,"testGram.load('<rule> = hello;')",locals())

        # most calls are not legal before load is called (successfully)
        testForException(natlink.NatError,"testGram.gramObj.activate('start',0)",locals())
        testForException(natlink.NatError,"testGram.gramObj.deactivate('start')",locals())
        testForException(natlink.NatError,"testGram.gramObj.setExclusive(1)",locals())
        testForException(natlink.NatError,"testGram.gramObj.emptyList('list')",locals())
        testForException(natlink.NatError,"testGram.gramObj.appendList('list','word')",locals())
        # clean up
        testGram.unload()
        
        

    #def testGrammarNumberFunctionsWithoutNumbersIni(self):
    #    """test the functions that convert numbers lists
    #    
    #    when the spokenforms.ini has been removed (temporarily)
    #    """
    #    class TestGrammar(natbj.DocstringGrammar):
    #        name = "testgrammarone"
    #        def __init__(self):
    #            natbj.DocstringGrammar.__init__(self)
    #        def rule_one(self, words):
    #            'rule one'
    #            pass
    #   
    #    testGram = TestGrammar()
    #    
    #    expGramSpec =  '''<one> exported = rule one;'''
    #    self.assert_equal(expGramSpec, testGram.gramSpec,"gramspec not as expected")
    #    
    #    # test the numbers convert function
    #    numIni = testGram.getNumbersInifile()
    #    language = 'enx'
    #    self.assert_equal(language, testGram.language, "Testing should take place with 'enx' speech profile, not: %s"% testGram.language)
    #    hundredGot = numIni.getList(language + "_prefixes", "hundred")
    #    expHundredList = ["hundred", "one hundred", "a hundred"]
    #    self.assert_equal(expHundredList, hundredGot, "list of 'hundred prefixes should be as expected")
    #    result = testGram.getSpokenFormsAboveHundred(102, numIni)
    #    expResult = ["hundred two", "one hundred two", "a hundred two"]
    #    self.assert_equal(expResult, result, "list for 102 not as expected")
    #    result = testGram.getSpokenFormsAboveHundred(335, numIni)
    #    expResult = ['three hundred thirty-five', 'three thirty-five']
    #    self.assert_equal(expResult, result, "list for 335 not as expected")

    def testGrammarNumberFunctions(self):
        """test the functions that convert numbers lists
        
        """
        class TestGrammar(natbj.DocstringGrammar):
            name = "testgrammarnumbers"
            def __init__(self):
                natbj.DocstringGrammar.__init__(self)
            def initialize(self):
                self.numresult = None
                self.switchOn()
            def rule_one(self, words):
                'rule one <n1-10>'
                pass
            def rule_two(self, words):
                'rule two  <numbers2to18>'
                pass
            def rule_three(self, words):
                'rule three  <n2to20>'
                pass
            def rule_four(self, words):
                'rule four  <numbers1-100>'
                self.numresult = self.getNumberFromSpoken(words[0])
            def rule_five(self, words):
                'rule five <n0-5>'
                self.numresult = self.getNumberFromSpoken(words[0])
            def checkExperiment(self, expected, testInfo):
                self.test.assert_equal(expected, self.numresult, testInfo)
            def gotBegin(self, modInfo):
                self.numresult = None # reset
                
                
        testGram = TestGrammar()
        testGram.test = self

        def doTestNumbersRecognition(words, expected, info):
            natlink.recognitionMimic(words)
            testGram.checkExperiment(expected, info)
        expGramSpec =  \
'''<one> exported = rule one <n1-10>;
<two> exported = rule two  <numbers2to18>;
<three> exported = rule three  <n2to20>;
<four> exported = rule four  <numbers1-100>;
<five> exported = rule five <n0-5>;'''
        self.assert_equal(expGramSpec, testGram.gramSpec,"gramspec not as expected")
        language = 'enx'
        self.assert_equal(language, testGram.language, "Testing should take place with 'enx' speech profile, not: %s"% testGram.language)
        doTestNumbersRecognition(["rule", "one", "two"], 2, "testing grammar rule one with number 2")
        
        


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
    # the test names to her example def test....
    # and change the word 'test' into 'tttest'...
    # do not forget to change back and do all the tests when you are done.
    suite = unittest.makeSuite(UnittestDocstringGrammar, 'test')
##    natconnectOption = 0 # no threading has most chances to pass...
    log('\nstarting tests with threading: %s\n'% natconnectOption)
    result = unittest.TextTestRunner().run(suite)
    dumpResult(result, logFile=logFile)
    
    logFile.close()

if __name__ == "__main__":
    run()
