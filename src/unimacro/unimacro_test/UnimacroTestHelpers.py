#
# Python Macro Language for Dragon NaturallySpeaking
#   (c) Copyright 1999 by Joel Gould
#   Portions (c) Copyright 1999 by Dragon Systems, Inc.
#
#   This script performs some basic tests of the NatLink system.  Dragon
#   NaturallySpeaking should be running with nothing in the editor window
#   (that you want to preserve) before these tests are run.
#   performed.
from pathlib import Path
from pprint import pprint
import sys
unimacrodir = Path('./..').normPath()
if unimacrodir not in sys.path:
    sys.path.append(unimacrodir)
from dtactions.unimacro import unimacroactions as actions
import unittest
import TestCaseWithHelpers
import re
import types
import natlink
from dtactions.unimacro import unimacroutils   
from natlinkcore import natlinkutils

from natlinkcore import natlinkutils
import win32gui
reWhiteSpace = re.compile('\s+')

class TestError(Exception):
    pass

class UnimacroTestHelpers(TestCaseWithHelpers.TestCaseWithHelpers):
    """providing helper functions for other unimacro tests
    """
    def squeeze_whitespace(self, text):
        return reWhiteSpace.sub(' ', text)

    def doTestForException(self, exceptionType,command,localVars={}):
        try:
            exec(command, globals(),localVars)
        except exceptionType:
            return
        raise TestError('Expecting an exception to be raised calling '+command)

    def assert_mod_partoftitle(self, expMod, expPartOfTitle=None, text=''):
        """check module and optional part of the window title with the actual

        """        
        mod, title, hndle = natlink.getCurrentModule()
        baseOfMod = natlinkutils.getBaseName(mod).lower()
        self.assert_equal(expMod, baseOfMod, "module unequal " + text)
        if expPartOfTitle:
            self.assert_(title.find(expPartOfTitle) >= 0,
                         'part of title "%s" does not match title "%s" in module "%s" " + text'%
                         (expPartOfTitle, title, mod))

    def doTestActionResult(self, expected, commandString):
        result = Search.doAction(commandString)
        if expected and result:
            pass
        elif not expected and not result:
            pass
        else:
            self.assert_equal(expected, result, "result of action not as expected")
        

    def assert_mod(self, expMod, text=''):
        """check module name with expected

        """        
        mod, title, hndle = natlink.getCurrentModule()
        baseOfMod = natlinkutils.getBaseName(mod).lower()
        self.assert_equal(expMod, baseOfMod, "module unequal " + text)
        
    def failIf_mod(self, expMod, text=''):
        """check module name with expected, should be UNEQUAL

        """
        mod, title, hndle = natlink.getCurrentModule()
        baseOfMod = natlinkutils.getBaseName(mod).lower()
        self.failIf(expMod == baseOfMod, "modules %s and %s are equal, should be unequal "%(expMod, baseOfMod) + text)
                

    #---------------------------------------------------------------------------
    # This utility subroutine will returns the contents of the NatSpeak window as
    # a string.  It works by using playString to select the contents of the
    # window and copy it to the clipboard.  We have to also add the character 'x'
    # to the end of the window to handle the case that the window is empty.

##    def getWindowContents(self):
##        natlinkutils.playString('{ctrl+end}x{ctrl+a}{ctrl+c}{ctrl+end}{backspace}')
##        contents = natlink.getClipboard()
##        if contents == 'x':
##            raise TestError,'Failed to read the contents of the NatSpeak window'
##        return contents[:-1]
    def getWindowContents(self):
        action = actions.doAction
        action('CLIPSAVE')
        action("<<selectall>><<copy>>")
        contents = unimacroutils.getClipboard()
        action('CLIPRESTORE')
        return contents
    
    def doTestActionResult(self, expected, commandString):
        result = actions.doAction(commandString)
        if expected and result:
            pass
        elif not expected and not result:
            pass
        else:
            self.assert_equal(expected, result, "result of action not as expected")


    def doTestWindowIsEmpty(self, testName=None):
        contents = self.getWindowContents()
        text = 'the window is NOT EMPTY'
        if testName:
            text += ': ' + testName
        if contents:
            self.fail(text)
            
        

    def doTestWindowContents(self, expected, testName=None):
        contents = self.getWindowContents()
            
        if testName:
            testText = 'Contents of window did not match expected text, testing %s'% testName
        else:
            testText = 'Contents of window did not match expected text'
        if type(expected) == list:
            for e in expected:
                if e == contents: return

            self.fail("contents: %s\nexpected one of: %s\n, %s"% (contents, expected, testText))                
        else:
            self.assert_equal(expected, contents, testText)
            
    def clearWindow(self):
        natlinkutils.playString('{ctrl+end}x{ctrl+a}{ctrl+c}{ctrl+end}{backspace}')
    #---------------------------------------------------------------------------
    # Utility function which calls a routine and tests the return value

    def doTestFuncReturn(self, expected,command,localVars={}):
        actual = eval(command,globals(),localVars)
        if actual != expected:
            raise TestError("Function call: %s\n  returned: %s\n  expected %s"%(command,repr(actual),repr(expected)))

    #---------------------------------------------------------------------------
    # This types the keysequence {alt+esc}.  Since this is a sequence trapped
    # by the OS, we must send as system keys.

    def playAltEsc(self):
        natlinkutils.playString('{alt+esc}',hook_f_systemkeys)

    #---------------------------------------------------------------------------

    def lookForNatspeakOrDragonPad(self):

        # This should find the NatSpeak window.  If the NatSpeak window is not
        # available (because, for example, NatSpeak was not started before 
        # running this script) then we will get the error:
        #   NatError: Error 62167 executing script execScript (line 1)

        try: natlink.execScript('AppBringUp "NatSpeak"')
        except natlink.NatError:
            raise TestError('The NatSpeak user interface is not running')
        try: natlink.execScript('Start "DragonPad"')
        except natlink.NatError:
            raise TestError('The DragonPad window cannot be started')
        
        # This will make sure that the NatSpeak window is empty.  If the NatSpeak
        # window is not empty we raise an exception to avoid possibily screwing 
        # up the users work.

        if self.getWindowContents():
            raise TestError('The NatSpeak/DragonPad window is not empty')
        mod, title, hndle = natlink.getCurrentModule()
        self.DragonPadMod = mod
        self.DragonPadHndle = hndle
        
    def wait(self, t=None):
        actions.do_Wait(t)

    def killNatspeakOrDragonPad(self):
        unimacroutils.SetForegroundWindow(self.DragonPadHndle)
        mod, title, hndle = natlink.getCurrentModule()
        self.assert_(mod == self.DragonPadMod and hndle == self.DragonPadHndle, "could not get back to Natspeak/DragonPad window")
        actions.killWindow()
        mod, title, hndle = natlink.getCurrentModule()
        self.failIf(mod == self.DragonPadMod and hndle == self.DragonPadHndle, "did not kill Natspeak/DragonPad window")

