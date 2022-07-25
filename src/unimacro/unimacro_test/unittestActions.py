# Python Macro Language for Dragon NaturallySpeaking
#   (c) Copyright 1999 by Joel Gould
#   Portions (c) Copyright 1999 by Dragon Systems, Inc.
#
# unittestActions.py
#   This script performs some basic tests of the NatLink but
#   with the Actions subclass.
#   especially the numbers parts of a spoken form list
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
from dtactions.unimacro.unimacroactions import doAction as action
from dtactions.unimacro.unimacroactions import doAction as action
from pathlib import Path
from dtactions.unimacro import unimacroactions as actions

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

thisDir = Path(getBaseFolder(globals()))

natconnectOption = 0 # or 1 for threading, 0 for not. Seems to make difference
                     # with spurious error (if set to 1), missing gotBegin and all that...
logFileName = os.path.join(thisDir, "testresult.txt")

testFilesDir = Path(thisDir)/'test_clipboardfiles'
if testFilesDir.isdir():
    print("test files for Bringup: %s"% testFilesDir)
else:
    raise OSError("no valid directory for test files: %s"% testFilesDir)
#---------------------------------------------------------------------------
# These tests should be run after we call natConnect
# no reopen user at each test anymore..
# no default open window (open window will be the calling program)
# default .ini files pop up when you first run this test. just ignore them.
class UnittestActions(TestCaseWithHelpers.TestCaseWithHelpers):
    def setUp(self):
        # if not natlink.isNatSpeakRunning():
        #     raise TestError('NatSpeak is not currently running')
        # self.connect()
        # self.user = natlink.getCurrentUser()[0]
        # self.setMicState = "off"
        pass

    def tearDown(self):
        # try:
        #     # give message:
        #     self.setMicState = "off"
        #     # kill things
        #     self.clearTestFiles()
        # finally:
        #     self.disconnect()
        pass
        
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

    def testKeystroke(self):
        """test in foreground window do some keystrokes with marks functions
        
        """
        log("test keystroke in the foreground window")
        # this one works, no ini file needed for the "hard key"
        keystroke("aaa{left 3}{del 3}")
        # keystroke("{shift+home}", hardKeys="{home}")
        # keystroke("{shift+home}", hardKeys=["{home}"])
        keystroke("xyz{shift+left 3}{ctrl+x}")
        

        
        # now get keystrokes AS IF in default child window:
        # proginfo = 
        
        
        # 


    def tttestGetSectionList(self):
        """test with fake program info for sections to be selected
        """
        progInfo = ("notepad", "title of notepad window", "child", 12345)
        sectionsList = actions.getSectionList(progInfo)
        expList = []
        
        

    def testAutoHotKey(self):
        """test ahk scripts
        """
        #action("AHK showmessageswindow.ahk")
    
        # action("AHK runcontrolget.ahk")
        
        action("AHK send hello")  ###h
        action("AHK send {backspace 4}")
        #

    def testUnimacroBringup(self):
        """test ahk scripts
        """
        notepadFile = testFilesDir/"testempty.txt"
        action("BRINGUP %s"% notepadFile)
        
#action("AHK send hello")
        

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
    suite = unittest.makeSuite(UnittestActions, 'test')
##    natconnectOption = 0 # no threading has most chances to pass...
    log('\nstarting tests with threading: %s\n'% natconnectOption)
    result = unittest.TextTestRunner().run(suite)
    dumpResult(result, logFile=logFile)
    
    logFile.close()

if __name__ == "__main__":
    run()
