#
# Python Macro Language for Dragon NaturallySpeaking
#   (c) Copyright 1999 by Joel Gould
#   Portions (c) Copyright 1999 by Dragon Systems, Inc.
#
# unittestClipboard.py
#
# this module tests the clipboard module, natlinkclipboard in natlink/macrosystem/core,
# as developed by Christo Butcher clipboard.py for Dragonfly and
# enhanced by Quintijn Hoogenboom, 2019.

#
import sys
import unittest
import types
import os
import os.path
import time
from pathqh import path
# import subprocess

# def getBaseFolder(globalsDict=None):
#     """get the folder of the calling module.
# 
#     either sys.argv[0] (when run direct) or
#     __file__, which can be empty. In that case take the working directory
#     """
#     globalsDictHere = globalsDict or globals()
#     baseFolder = ""
#     if globalsDictHere['__name__']  == "__main__":
#         baseFolder = os.path.split(sys.argv[0])[0]
#         print('baseFolder from argv: %s'% baseFolder)
#     elif globalsDictHere['__file__']:
#         baseFolder = os.path.split(globalsDictHere['__file__'])[0]
#         print('baseFolder from __file__: %s'% baseFolder)
#     if not baseFolder or baseFolder == '.':
#         baseFolder = os.getcwd()
#     return baseFolder
thisDir = path('.')
unimacroFolder = (thisDir/'..').normpath()
if not unimacroFolder in sys.path:
    sys.path.append(unimacroFolder)
import TestCaseWithHelpers
import natlink
import natlinkclipboard
import actions
import natlinkutilsqh

natconnectOption = 0 # no threading has most chances to pass...

logFileName = thisDir/"testresult.txt"
print('start unittestClipboard', file=open(logFileName, 'w'))

testFilesDir = thisDir/'test_clipboardfiles'
if not testFilesDir.isdir():
    testFilesDir.mkdir()

#---------------------------------------------------------------------------
# These tests should be run after we call natConnect
# no reopen user at each test anymore..
# no default open window (open window will be the calling program)
# default .ini files pop up when you first run this test. just ignore them.
class UnittestClipboard(TestCaseWithHelpers.TestCaseWithHelpers):
    def setUp(self):
        self.connect()
        self.isConnected = True
        self.thisHndle = natlink.getCurrentModule()[2]
        self.org_text = "xyz"*3
        natlinkclipboard.Clipboard.set_system_text(self.org_text)
        # self.setupWindows()
        self.setupTextFiles()
        print('thisHndle: %s'% self.thisHndle)
        # print 'explWinHndle: %s'% self.explWinHndle
        # print 'explThisDirHndle: %s'% self.explThisDirHndle
        print('text0Hndle: %s'% self.text0Hndle)
        print('text1Hndle: %s'% self.text1Hndle)
        print('text2Hndle: %s'% self.text2Hndle)
        pass
    
    def tearDown(self):
        for hndle in self.text0Hndle, self.text1Hndle, self.text2Hndle: #self.explWinHndle, self.explThisDirHndle, :
            natlinkutilsqh.SetForegroundWindow(hndle)
            natlink.playString("{alt+f4}")
        natlinkutilsqh.SetForegroundWindow(self.thisHndle)
        self.disconnect()
        self.isConnected = False

        
    def connect(self):
        # start with 1 for thread safety when run from pythonwin:
        natlink.natConnect(natconnectOption)
        sys.stdout = open(logFileName, 'a')
        sys.stderr = open(logFileName, 'a')

    def disconnect(self):
        natlink.natDisconnect()

    def setupWindows(self):
        """make several windows to which can be switched, and which can be copied from
        """
        dirWindows = "C:\\windows"
        result = actions.UnimacroBringUp(app=None, filepath=dirWindows)
        if not result:
            print('no result for %s'% dirWindows)
            return
        self.explWinHndle = natlink.getCurrentModule()[2]
        natlinkutilsqh.SetForegroundWindow(self.thisHndle)
        result = actions.UnimacroBringUp(app=None, filepath=thisDir)
        if not result:
            print('no result for %s'% thisDir)
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
        print('testempty: %s'% repr(curmod))
        self.text0Hndle = curmod[2]

        textFile1 = "testsmall.txt"
        textPath1 = os.path.join(testFilesDir, textFile1)
        open(textPath1, 'w').write("abacadabra\n"*2)
        result = actions.UnimacroBringUp(app=None, filepath=textPath1)
        time.sleep(1)
        curmod = natlink.getCurrentModule()
        print('testsmall: %s'% repr(curmod))
        self.text1Hndle = curmod[2]

        textFile2 = "testlarge.txt"
        textPath2 = os.path.join(testFilesDir, textFile2)
        open(textPath2, 'w').write("abacadabra\n"*1000)
        result = actions.UnimacroBringUp(app=None, filepath=textPath2)
        time.sleep(2)
        curmod = natlink.getCurrentModule()
        print('testlarge: %s'% repr(curmod))
        self.text2Hndle = curmod[2]
        
        natlinkutilsqh.SetForegroundWindow(self.thisHndle)
        pass
        
    def testCopyClipboard(self):
        """test the copying of the clipboard
        """
        cb = natlinkclipboard.Clipboard(save_clear=True)

        ## longer test:
        for i in range(1, 11):
            print('---- round: ', i)
            ## empty file:
            natlinkutilsqh.SetForegroundWindow(self.text0Hndle)
            # time.sleep(1)
            natlink.playString("{ctrl+a}{ctrl+c}")
            time.sleep(0.5)
            cb.copy_from_system(waiting_interval=0.1)
            # time.sleep(1)
            natlinkutilsqh.SetForegroundWindow(self.thisHndle)
            print('cb text: %s'% cb)
            got = cb.get_text()
            self.assert_equal("", got, "should have no text now")
    
            natlinkutilsqh.SetForegroundWindow(self.text1Hndle)
            # time.sleep(2)
            natlink.playString("{ctrl+a}{ctrl+c}")
            time.sleep(0.5)
            natlinkutilsqh.SetForegroundWindow(self.thisHndle)
            # print 'cb text: %s'% cb        
            cb.copy_from_system(waiting_interval=None)
            got = cb.get_text()
            exp = "abacadabra\nabacadabra\n"
            self.assert_equal(exp, got, "should have two lines of text")
    
            natlinkutilsqh.SetForegroundWindow(self.text2Hndle)
            # time.sleep(1)
            natlink.playString("{ctrl+a}{ctrl+c}")
            time.sleep(0.5)
            cb.copy_from_system(waiting_interval=None)
            natlinkutilsqh.SetForegroundWindow(self.thisHndle)
            t = cb.get_text()
            if t:
                got = len(t)
            else:
                print('no result from get_text: %s'% t)
                got = None
            exp = 11000
            self.assert_equal(exp, got, "should have long text now")
            # empty for the next round:
            cb.set_text("")
            time.sleep(1)
            
        cb.restore()
        got_org_text = natlinkclipboard.Clipboard.get_system_text()
        self.assert_equal(self.org_text, got_org_text, "restored text from clipboard not as expected")

    
    def tttestSetForegroundWindow(self):
        """test switching the different windows, including this
        
        This should work without problems with the AutoHotkey script...
        
        About 0.15 seconds to get a window in the foreground...

        """
        thisHndle = natlinkutilsqh.GetForegroundWindow()
        print("thisHndle: %s"% thisHndle)
        unknownHndle = 5678659
        hndles = [thisHndle, self.text0Hndle, self.text1Hndle, self.text2Hndle, unknownHndle]
        t0 = time.time()
        rounds = 10
        for i in range(1, rounds+1):
            print('start round %s'% i)
            for h in hndles:
                result = natlinkutilsqh.SetForegroundWindow(h)
                if result:
                    self.assert_not_equal(unknownHndle, h, "hndle should not be unknown (fake) hndle")
                else:
                    self.assert_equal(unknownHndle, h, "hndle should be one of the valid hndles")

            time.sleep(0.1)
        t1 = time.time()
        deliberate = rounds*0.1
        total = t1 - t0
        nettime = t1 - t0 - deliberate
        nswitches = rounds*len(hndles)
        timeperswitch = nettime/nswitches
        print('nswitches: %s, nettime: %.3f, time per switch: %.3f'% ( nswitches, nettime, timeperswitch))
        print('total: %s, deliberate: %s'% (total, deliberate))

    def tttestGet_current_directory(self):
        """test getting the current directory
        
        This one not really needed, better go with messages functions, use self.activeFolder from gotBegin.
        
        a way to get in with the debugger of Komodo:
        """
        hndle = 265916  # explorer, 
        func = self.grammarInstance.get_current_directory
        # fill here the windows hndle... (give window info from _general)
        result = func(hndle)
        print('result: %s'% result)

    
              
    def log(self, t):
        if self.isConnected:
            natlink.displayText(t, 0)
        else:
            print(t)
        print(t, file=open(logFileName, "a"))

def run():
    print('starting UnittestClipboard') 
    # trick: if you only want one or two tests to perform, change
    # the test names to her example def test....
    # and change the word 'test' into 'tttest'...
    # do not forget to change back and do all the tests when you are done.
    # each test does a natConnect and a natDisconnect...
    sys.stdout = open(logFileName, 'a')
    sys.stderr = open(logFileName, 'a')
    
    suite = unittest.makeSuite(UnittestClipboard, 'test')
    result = unittest.TextTestRunner().run(suite)
    
if __name__ == "__main__":
    print("run, result will be in %s"% logFileName)
    run()
