#
# Python Macro Language for Dragon NaturallySpeaking
#   (c) Copyright 1999 by Joel Gould
#   Portions (c) Copyright 1999 by Dragon Systems, Inc.
#
from dtactions.unimacro import unimacroutils
from natlinkcore import natlinkutils
from dtactions.unimacro import unimacroactions as actions
actions.debugActions(1)

import unittest
import UnimacroTestHelpers
import time
import sys

##class UnimacroBasicTest(TestCaseWithHelpers.TestCaseWithHelpers):
class SearchTest(UnimacroTestHelpers.UnimacroTestHelpers):
    """Tests several search actions.

    executes on the active window which should be empty before starting!   

    """
      
    def setUp(self):
        self.doTestWindowIsEmpty(testName="setUp SearchTest needs an empty window to start with...")

    def tearDown(self):
        pass

    def getWindowContents(self):
        action = actions.doAction
        action('CLIPSAVE')
        action("<<selectall>><<copy>>")
        contents = unimacroutils.getClipboard()
        action('CLIPRESTORE')
        return contents

    def doTestClipboard(self, expected, testName=None):
        text = 'testing the clipboard'
        if testName:
            text += ': ' + testName
        action = actions.doAction
        contents = unimacroutils.getClipboard()
        self.assert_equal(expected, contents, text)


    def doTestActionResult(self, expected, commandString):
        result = Search.doAction(commandString)
        if expected and result:
            pass
        elif not expected and not result:
            pass
        else:
            self.assert_equal(expected, result, "result of action not as expected")



    def checkContents(self, expected, comment=""):
        """check expected tuple (clipboard, before, after)

        if selection was active, it came through a forward search, feeble part!
        
        """
        text = 'checking contents'
        if comment:
            text += ': %s'% comment
        action = actions.doAction
        action('CLIPSAVE')
        action("<<copy>>")
        clip = unimacroutils.getClipboard()
        lenClip = len(clip)
        # get to the left of the selection:
        action('<<leftafterforwardsearch %s>>{shift+ctrl+home}<<copy>>{ctrl+home}'% lenClip)
        begin = unimacroutils.getClipboard()
        lenBegin = len(begin)
        lengths = lenBegin + lenClip
        action('{right %s}'% lengths)
        action('{shift+ctrl+end}<<copy>>')
        end = unimacroutils.getClipboard()
        end = end.rstrip()
        lenEnd = len(end)
        action('<<selectall>><<copy>>')
        all = unimacroutils.getClipboard()
        all = all.rstrip()
        lenAll = len(all)
        action('CLIPRESTORE')
        self.assertEqual(lenAll, lenBegin+lenClip+lenEnd,
                          text + 'lengths do not match, total: %s, parts: %s, %s, %s'%
                          (lenAll, lenBegin, lenClip, lenEnd))
        action('VW')
        action("{ctrl+home}{right %s}{shift+right %s}"% (lenBegin, lenClip))
        self.assert_equal( expected, (begin, clip, end), text)    

    

        
    def test_basic_Search_actions(self):
        action = actions.doAction
        keystroke = actions.doKeystroke
        keystroke('aaa\nbb\n   ccc')
        action("{ctrl+home}")
        expected = ("", "", 'aaa\nbb\n   ccc')  # selection, before, after
        # if this test fails, one of the actions of "checkContents" does not work properly:
        self.checkContents(expected, comment="initial position")

        keystroke("{right}{shift+right}")
        expected = ("a", "a", 'a\nbb\n   ccc')  # selection, before, after
        self.checkContents(expected, comment="middle a selected")
        
        
        action("<<startsearch>>")
        keystroke("bb")
        action("<<searchgo>>")
        action("<<copy>>")
        self.doTestClipboard("bb", "clipboard contents not as expected")
        expected = ('aaa\n', 'bb', '\n   ccc')  # selection, before, after
        self.checkContents(expected, comment="after searchfor bb action ")        
        


# no main statement, run from command in _unimacrotest.py.

