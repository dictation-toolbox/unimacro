"""unittest of unimacro stuff

This module tests unimacro things.

The test files (unittest) in the subfolder "unimacro_test", and have name like "BasicTest.py".

The test class name MUST be identical to the filename.

Tests can be run one alone (call unimacro test testname) or
or all (call unimacro test all)

instance variables that are passed to all tests:
-self.doAll (so the test knows it is a single test or a complete suite)

"""
import os
import sys
import unittest
import glob
import natlink
from natlinkcore import natlinkstatus
import unimacro.natlinkutilsbj as natbj
from dtactions.unimacro import unimacroutils
from dtactions.unimacro import utilsqh
from dtactions.unimacro import unimacroactions as actions

status = natlinkstatus.NatlinkStatus()

class UnittestGrammar(natbj.IniGrammar):
    language = unimacroutils.getLanguage()        
    name = 'unimacro test'
    iniIgnoreGrammarLists = ['tests'] # are set in this module
    gramSpec = """
<onetest> exported = unimacro test {tests};
<alltests> exported = unimacro test (all);
    """

    def initialize(self):
        self.load(self.gramSpec)
        self.activateAll()
        self.switchOnOrOff()
        self.setList('tests', self.getTestNames()) # also fill self.testNames, self.allTests
        self.filesToSkipInResult = ["unittest.py", "TestCaseWithHelpers.py"]

    def gotBegin(self,moduleInfo):
        if self.checkForChanges:
            self.checkInifile()
            self.setList('tests', self.getTestNames())

    def gotResults_onetest(self, words, fullResults):
        """do one of the unittests"""
        test = words[-1]
        self.doAll = 0
        print("---------------------------------do unimacro unittest for: %s"% test)
        self.doUnitTests([test])

    def gotResults_alltests(self, words, fullResults):
        """do all the unittests"""
        print("---------------------------------do all unimacro unittests")
        tests = list(self.allTests.keys())
        tests.sort()
        self.doAll = 1
        self.doUnitTests(tests)

    def getTestNames(self):
        """get the test names, with side effect builds a dict of all the tests

        the result (the testNames) can then be filled in the list {tests}
        self.allTests (dict) contains the names: files entries
        """
        self.testFolder = os.path.join(status.getUnimacroDirectory(), "unimacro_test")
        testFiles = glob.glob(os.path.join(self.testFolder, "*test.py"))
##        print 'testFiles: %s'% testFiles
        testNames = list(map(self.extractTestName, testFiles))
        print('testNames: %s'% testNames)
        self.allTests = dict(list(zip(testNames, testFiles)))
        return testNames

    def extractTestName(self, fullPath):
        """remove path, .py and "Test" from filename to get pronouncable test"""
        name = os.path.basename(fullPath).lower()
        name = utilsqh.removeFromEnd(name, ".py", ignoreCase=1)
        name = utilsqh.removeFromEnd(name, "test", ignoreCase=1)
        return name

    def showInifile(self):
        commandExplanation = "Names of tests: \n%s\n---------------"% '\n'.join(self.testNames)
        super(UnittestGrammar, self).showInifile(commandExplanation=commandExplanation)

    def doUnitTests(self, tests):
        # self.checkSysPath(self.testFolder)  # append unimacro_test if needed
        suiteAll = None
        self.activeTests = []

        for test in tests:
            print('do test %s (%s)'% (test, self.allTests[test]))
            suite = self.addUnitTest(test, self.allTests[test])
            if suite:
                self.activeTests.append(test)
                if suiteAll:
                    suiteAll.addTest(suite)
                else:
                    suiteAll = suite
        if suiteAll:
            natlink.setMicState('off')
            result = unittest.TextTestRunner().run(suiteAll)
            print('after testing------------------------------------')
            self.dumpResult(result, filesToSkip=self.filesToSkipInResult)            
            natlink.setMicState('on')

        else:
            print("nothing valid to test")

    def addUnitTest(self, test, fileName):
        """do one of the unittests"""
##        actions.Message("starting test %s"% fileName)

        test_path = os.path.join(sys.prefix, 'Lib', 'site-packages', 'unimacro', 'unimacro_test')
        if not os.path.isdir(test_path):
            raise OSError(f'cannot add unittest for Unimacro, test_path invalid: "{test_path}"')
        if not test_path in sys.path:
            sys.path.append(test_path)
        modName = os.path.basename(fileName)
        modName = utilsqh.removeFromEnd(modName, ".py", ignoreCase=1)
    
        testMod = __import__(modName)
        testClassName = modName
        try:
            testClass = getattr(testMod, testClassName)
        except AttributeError:
            print('****cannot find test class in test module, skipping test: %s'% testClassName)
            return None
        suite = unittest.makeSuite(testClass, 'test')
        return suite

    def checkSysPath(self, folder):
        """add to sys.path if not present yet"""
        if folder in sys.path:
            return
        print('adding to path: %s'% folder)
        sys.path.append(folder)

    def dumpResult(self, testResult, filesToSkip=None):
        """dump into txt file "testresult" in unimacro_test folder

        slightly different version in voice coder (test_defs.py)
        """
        alert = len(self.activeTests) > 0
        testResultFile = os.path.join(self.testFolder, "testresult.txt")
        f = open(testResultFile, 'w')
        if testResult.wasSuccessful():
            if alert:
                mes = "all succesful: %s"% self.activeTests
                actions.Message(mes, "Unimacro Tests succesful")
            else:
                mes = "test passed: %s"% self.activeTests[0]
                self.DisplayMessage(mes)
            f.write(mes+'\n'*2)
            f.close()
            return
        f.write("results of tests: %s\n"% self.activeTests)
        f.write('\n--------------- errors -----------------\n')
        for case, tb in testResult.errors:
            f.write('\n---------- %s --------\n'% case)
            cleanTb = utilsqh.cleanTraceback(tb, filesToSkip)
            f.write(cleanTb)
        f.write('\n--------------- failures -----------------\n')
        for case, tb in testResult.failures:
            f.write('\n---------- %s --------\n'% case)
            cleanTb = utilsqh.cleanTraceback(tb, filesToSkip)
            f.write(cleanTb)

        f.close()
        mes = "there were errors with testing unimacro: %s\n\nPlease consult the outputfile: %s"% \
              (self.activeTests, testResultFile)
        actions.Message(mes, "Unimacro Tests failure", alert=alert)
        self.openFileDefault(testResultFile, mode="edit", name='test result')

    
        

    
# standard stuff Joel (adapted for possible empty gramSpec, QH, unimacro)
thisGrammar = UnittestGrammar()
if thisGrammar.gramSpec:
    thisGrammar.initialize()
else:
    thisGrammar = None

def unload():
    #pylint:disable=W0603
    global thisGrammar
    if thisGrammar:
        thisGrammar.unload()
    thisGrammar = None


