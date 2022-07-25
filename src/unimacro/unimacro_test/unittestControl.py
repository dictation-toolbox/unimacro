#
# Python Macro Language for Dragon NaturallySpeaking
#   (c) Copyright 1999 by Joel Gould
#   Portions (c) Copyright 1999 by Dragon Systems, Inc.
#
# unittestControl.py
#   This script performs some testing of the control grammar
#   the site mechanism (of Qh private) in which modules of a website generating program
#   are tested specifically
#
from pathlib import Path
from pprint import pprint
import sys
unimacrodir = Path('./..').normPath()
if unimacrodir not in sys.path:
    sys.path.append(unimacrodir)

import unittest
import types
import os
import os.path
import TestCaseWithHelpers
import natlink


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
class UnittestControl(TestCaseWithHelpers.TestCaseWithHelpers):
    def setUp(self):
        natlink.natConnect()
        self.control = __import__("_control")
        self.grammarInstance = self.control.utilGrammar
    def tearDown(self):
        self.control.unload()
        natlink.natDisconnect()



    def testConnectWithLoadAllGrammars(self):
        """test the connection with show all grammars
        
        a way to get in with the debugger of Komodo:
        """
        func = self.grammarInstance.gotResults_show
        # print 'func: %s'% func
        result = func(['show', 'all', 'grammars'], {})
        # print 'result: %s'% result
    # def testConnectingWithSite(self):
    #     """test the connecting of a siteinstance
    #     
    #     a way to get in with the debugger of Komodo:
    #     """
    #     func = self.grammarInstance.getSiteInstance
    #     print 'func: %s'% func
    #     result = func('sg')
    #     print 'result: %s'% result
            
def log(t):
    print(t)

def run():
    log('starting unittestControl')
    # trick: if you only want one or two tests to perform, change
    # the test names to her example def test....
    # and change the word 'test' into 'tttest'...
    # do not forget to change back and do all the tests when you are done.
    suite = unittest.makeSuite(UnittestControl, 'test')
##    natconnectOption = 0 # no threading has most chances to pass...
    result = unittest.TextTestRunner().run(suite)
    print(result)
if __name__ == "__main__":
    run()
