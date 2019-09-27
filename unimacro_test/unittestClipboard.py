#
# Python Macro Language for Dragon NaturallySpeaking
#   (c) Copyright 1999 by Joel Gould
#   Portions (c) Copyright 1999 by Dragon Systems, Inc.
#
# unittestClipboard.py
#
# this module tests the clipboard module, natlinkclipboard in natlink/macrosystem/core,
# as developed by Christo Butcher clipboard.py for Dragonfly.
#
#
import six
import sys
import unittest
import types
import os
import os.path
import time
# import subprocess
import natlinkutilsqh
import actions
import TestCaseWithHelpers
import natlink
import natlinkclipboard

natconnectOption = 0 # no threading has most chances to pass...

def getBaseFolder(globalsDict=None):
    """get the folder of the calling module.

    either sys.argv[0] (when run direct) or
    __file__, which can be empty. In that case take the working directory
    """
    globalsDictHere = globalsDict or globals()
    baseFolder = ""
    if globalsDictHere['__name__']  == "__main__":
        baseFolder = os.path.split(sys.argv[0])[0]
        print 'baseFolder from argv: %s'% baseFolder
    elif globalsDictHere['__file__']:
        baseFolder = os.path.split(globalsDictHere['__file__'])[0]
        print 'baseFolder from __file__: %s'% baseFolder
    if not baseFolder or baseFolder == '.':
        baseFolder = os.getcwd()
        print 'baseFolder was empty, take wd: %s'% baseFolder
    return baseFolder

thisDir = getBaseFolder(globals())
logFileName = os.path.join(thisDir, "testresult.txt")
testFilesDir = os.path.join(thisDir, 'test_clipboardfiles')
if not os.path.isdir(testFilesDir):
    os.mkdir(testFilesDir)

#---------------------------------------------------------------------------
# These tests should be run after we call natConnect
# no reopen user at each test anymore..
# no default open window (open window will be the calling program)
# default .ini files pop up when you first run this test. just ignore them.
class UnittestClipboard(TestCaseWithHelpers.TestCaseWithHelpers):
    def setUp(self):
        self.connect()
        self.thisHndle = natlink.getCurrentModule()[2]
        self.org_text = "xyz"*3
        natlinkclipboard.Clipboard.set_system_text(self.org_text)
        # self.setupWindows()
        self.setupTextFiles()
        print 'thisHndle: %s'% self.thisHndle
        # print 'explWinHndle: %s'% self.explWinHndle
        # print 'explThisDirHndle: %s'% self.explThisDirHndle
        print 'text0Hndle: %s'% self.text0Hndle
        print 'text1Hndle: %s'% self.text1Hndle
        print 'text2Hndle: %s'% self.text2Hndle

    def tearDown(self):
        for hndle in self.text0Hndle, self.text1Hndle, self.text2Hndle: #self.explWinHndle, self.explThisDirHndle, :
            natlinkutilsqh.SetForegroundWindow(hndle)
            natlink.playString("{alt+f4}")
        natlinkutilsqh.SetForegroundWindow(self.thisHndle)
        self.disconnect()

        pass

        
    def connect(self):
        # start with 1 for thread safety when run from pythonwin:
        natlink.natConnect(natconnectOption)

    def disconnect(self):
        natlink.natDisconnect()

    def setupWindows(self):
        """make several windows to which can be switched, and which can be copied from
        """
        dirWindows = "C:\\windows"
        result = actions.UnimacroBringUp(app=None, filepath=dirWindows)
        if not result:
            print 'no result for %s'% dirWindows
            return
        self.explWinHndle = natlink.getCurrentModule()[2]
        natlinkutilsqh.SetForegroundWindow(self.thisHndle)
        result = actions.UnimacroBringUp(app=None, filepath=thisDir)
        if not result:
            print 'no result for %s'% thisDir
            return
        self.explThisDirHndle = natlink.getCurrentModule()[2]
        natlinkutilsqh.SetForegroundWindow(self.thisHndle)
        pass
        
    def setupTextFiles(self):
        """make some text files for clipboard testing
        """
        textFile0 = "testempty.txt"
        textPath0 = os.path.join(testFilesDir, textFile0)
        open(textPath0, 'w')
        result = actions.UnimacroBringUp(app=None, filepath=textPath0)
        time.sleep(1)
        curmod = natlink.getCurrentModule()
        print 'testempty: %s'% repr(curmod)
        self.text0Hndle = curmod[2]

        textFile1 = "testsmall.txt"
        textPath1 = os.path.join(testFilesDir, textFile1)
        open(textPath1, 'w').write("abacadabra\n"*2)
        result = actions.UnimacroBringUp(app=None, filepath=textPath1)
        time.sleep(1)
        curmod = natlink.getCurrentModule()
        print 'testsmall: %s'% repr(curmod)
        self.text1Hndle = curmod[2]

        textFile2 = "testlarge.txt"
        textPath2 = os.path.join(testFilesDir, textFile2)
        open(textPath2, 'w').write("abacadabra\n"*1000)
        result = actions.UnimacroBringUp(app=None, filepath=textPath2)
        time.sleep(2)
        curmod = natlink.getCurrentModule()
        print 'testlarge: %s'% repr(curmod)
        self.text2Hndle = curmod[2]
        natlinkutilsqh.SetForegroundWindow(self.thisHndle)
        pass
        
    def testCopyClipboard(self):
        """test the copying of the clipboard
        """
        cb = natlinkclipboard.Clipboard(save_clear=True)

        ## empty file:
        natlinkutilsqh.SetForegroundWindow(self.text0Hndle)
        time.sleep(1)
        natlink.playString("{ctrl+a}{ctrl+c}")
        # time.sleep(1)
        cb.copy_from_system(wait_for_change=None)
        time.sleep(1)
        natlinkutilsqh.SetForegroundWindow(self.thisHndle)
        print 'cb text: %s'% cb
        got = cb.get_text()
        self.assert_equal(u"", got, "should have no text now")

        natlinkutilsqh.SetForegroundWindow(self.text1Hndle)
        time.sleep(2)
        natlink.playString("{ctrl+a}{ctrl+c}")
        # time.sleep(2)
        natlinkutilsqh.SetForegroundWindow(self.thisHndle)
        # print 'cb text: %s'% cb        
        cb.copy_from_system(wait_for_change=None)
        got = cb.get_text()
        exp = u"abacadabra\nabacadabra\n"
        self.assert_equal(exp, got, "should have two lines of text")

        natlinkutilsqh.SetForegroundWindow(self.text2Hndle)
        time.sleep(1)
        natlink.playString("{ctrl+a}{ctrl+c}")
        # time.sleep(1)
        cb.copy_from_system(wait_for_change=None)
        natlinkutilsqh.SetForegroundWindow(self.thisHndle)
        t = cb.get_text()
        if t:
            got = len(t)
        else:
            print 'no result from get_text: %s'% t
            got = None
        exp = 11000
        self.assert_equal(exp, got, "should have long text now")
            
        cb.restore()
        got_org_text = natlinkclipboard.Clipboard.get_system_text()
        self.assert_equal(self.org_text, got_org_text, "restored text from clipboard not as expected")

    
    def tttestGet_current_directory(self):
        """test getting the current directory
        
        This one not really needed, better go with messages functions, use self.activeFolder from gotBegin.
        
        a way to get in with the debugger of Komodo:
        """
        hndle = 265916  # explorer, 
        func = self.grammarInstance.get_current_directory
        # fill here the windows hndle... (give window info from _general)
        result = func(hndle)
        print 'result: %s'% result

  
            
def log(t):
    print t

def run():
    log('starting UnittestClipboard')
    # trick: if you only want one or two tests to perform, change
    # the test names to her example def test....
    # and change the word 'test' into 'tttest'...
    # do not forget to change back and do all the tests when you are done.
    suite = unittest.makeSuite(UnittestClipboard, 'test')
    result = unittest.TextTestRunner().run(suite)
    print result
if __name__ == "__main__":
    natlink.natConnect()
    run()
