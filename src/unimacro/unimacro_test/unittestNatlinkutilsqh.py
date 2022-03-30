#
# Python Macro Language for Dragon NaturallySpeaking
#   (c) Copyright 1999 by Joel Gould
#   Portions (c) Copyright 1999 by Dragon Systems, Inc.
#
# unittestNatlinkutilsqh.py
#   This script performs tests on the utilities in natlinkutilsqh.py
#   the site mechanism (of Qh private) in which modules of a website generating program
#   are tested specifically
#
import sys
import unittest
import types
import os
import os.path
import TestCaseWithHelpers
import natlink
from dtactions.unimacro import unimacroutils as natqh

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
logFileName = os.path.join(thisDir, "testresult.txt")

#---------------------------------------------------------------------------
# These tests should be run after we call natConnect
# no reopen user at each test anymore..
# no default open window (open window will be the calling program)
# default .ini files pop up when you first run this test. just ignore them.
class UnittestNatlinkutilsqh(TestCaseWithHelpers.TestCaseWithHelpers):
    def setUp(self):
        natlink.natConnect()
        
    def tearDown(self):
        natlink.natDisconnect()
        pass


    
    def testMatchTitle(self):
        """test the matchTitle function
        
        """
        modInfo = natlink.getCurrentModule()
        title = modInfo[1]
        ## construct a testword and a otherCaseTestWord:
        testword = title[2:]
        otherCaseTestWord = testword.lower()
        if otherCaseTestWord == testword:
            otherCaseTestWord = testword.upper()
            if otherCaseTestWord == testword:
                raise ValueError(" TEST ERROR, test of matchTitle fails because of invalid otherCaseTestWord: %s"% otherCaseTestWord)

        ## default case:
        got = unimacroutils.matchTitle(testword, modInfo=modInfo)
        exp = unimacroutils.getProgName(modInfo)
        self.assert_equal(exp, got, "matchTitle should be OK with testword: %s and window title: %s"% (testword, title))
        got = unimacroutils.matchTitle(testword, modInfo=modInfo)
        exp = unimacroutils.getProgName(modInfo)
        self.assert_equal(exp, got, "matchTitle should be OK with otherCaseTestWord: %s and window title: %s"% (otherCaseTestWord, title))

        ## rare different cases, all less important:
        got = unimacroutils.matchTitle(otherCaseTestWord, modInfo=modInfo, caseExact=1)
        exp = False
        self.assert_equal(exp, got, "matchTitle should fail with caseExact True: testword: %s and window title: %s"% (otherCaseTestWord, title))

        ## should match exact title, False!
        got = unimacroutils.matchTitle(otherCaseTestWord, modInfo=modInfo, titleExact=1)
        exp = False
        self.assert_equal(exp, got, "matchTitle should fail with titleExact True: testword: %s and window title: %s"% (otherCaseTestWord, title))
        got = unimacroutils.matchTitle(testword, modInfo=modInfo, titleExact=1)
        exp = False
        self.assert_equal(exp, got, "matchTitle should fail with titleExact True: testword: %s and window title: %s"% (testword, title))

        

        ## now for the whole title:
        wholeTitle = title
        exp = unimacroutils.getProgName(modInfo)
        got = unimacroutils.matchTitle(wholeTitle, modInfo=modInfo)
        self.assert_equal(exp, got, "matchTitle should be OK with whole title %s\nand window title: %s"% (wholeTitle, title))
        otherWholeTitle = wholeTitle.upper()
        if wholeTitle == otherWholeTitle:
            otherWholeTitle = wholeTitle.lower()
            if wholeTitle == otherWholeTitle:
                raise ValueError(" TEST ERROR, test of matchTitle wholeTitle fails because of invalid otherWholeTitle: %s"% otherWholeTitle)

        got = unimacroutils.matchTitle(wholeTitle, modInfo=modInfo, titleExact=1)
        self.assert_equal(exp, got, "matchTitle should be OK with whole title %s\nand window title: %s"% (wholeTitle, title))
        got = unimacroutils.matchTitle(wholeTitle, modInfo=modInfo, titleExact=1, caseExact=1)
        self.assert_equal(exp, got, "matchTitle should be OK with whole title %s\nand window title: %s"% (wholeTitle, title))

        got = unimacroutils.matchTitle(otherWholeTitle, modInfo=modInfo, titleExact=1)
        self.assert_equal(exp, got, "matchTitle should be OK with whole title %s\nand window title: %s"% (wholeTitle, title))
  
        got = unimacroutils.matchTitle(otherWholeTitle, modInfo=modInfo, titleExact=1, caseExact=1)
        exp = False
        self.assert_equal(exp, got, "matchTitle should fail with whole title %s\nand window title: %s"% (wholeTitle, title))
        got = unimacroutils.matchTitle(otherWholeTitle, modInfo=modInfo, titleExact=1, caseExact=1)
        self.assert_equal(exp, got, "matchTitle should be OK with whole title %s\nand window title: %s"% (wholeTitle, title))
                
        ## now for a list of possible test words:
        ListOfTestWords = ["xxxyyy", testword]
        exp = unimacroutils.getProgName(modInfo)
        got = unimacroutils.matchTitle(ListOfTestWords, modInfo=modInfo)


        ListOfTestWords = ["xxxyyy", otherCaseTestWord]
        exp = False
        got = unimacroutils.matchTitle(ListOfTestWords, modInfo=modInfo, caseExact=1)
            
def log(t):
    print(t)

def run():
    log('starting unittestNatlinkutilsqh')
    # trick: if you only want one or two tests to perform, change
    # the test names to her example def test....
    # and change the word 'test' into 'tttest'...
    # do not forget to change back and do all the tests when you are done.
    suite = unittest.makeSuite(UnittestNatlinkutilsqh, 'test')
##    natconnectOption = 0 # no threading has most chances to pass...
    result = unittest.TextTestRunner().run(suite)
    print(result)
if __name__ == "__main__":
    run()
