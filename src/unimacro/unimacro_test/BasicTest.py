#
# Python Macro Language for Dragon NaturallySpeaking
#   (c) Copyright 1999 by Joel Gould
#   Portions (c) Copyright 1999 by Dragon Systems, Inc.
#
#   This script performs some basic tests of the NatLink system.  Dragon
#   NaturallySpeaking should be running with nothing in the editor window
#   (that you want to preserve) before these tests are run.
#   performed.
from natlinkcore.pathqh import path
from pprint import pprint
import sys
unimacrodir = path('./..').normpath()
if unimacrodir not in sys.path:
    sys.path.append(unimacrodir)

from dtactions.unimacro import unimacroutils
import natlinkcore.natlinkutils as natut
from unimacro import actions
action = actions.doAction

import unittest
import TestCaseWithHelpers

##class UnimacroBasicTest(TestCaseWithHelpers.TestCaseWithHelpers):
class BasicTest(TestCaseWithHelpers.TestCaseWithHelpers):
      
    def setUp(self):
        pass
##        natlink.natConnect()
        

    def test_Something_in_unimacro(self):
        print('testing something')
        lang = unimacroutils.getLanguage()
        self.assert_equal("enx", lang, "testing should be done from an English speech profile, not: %s"% lang)

# no main statement, run from command in _unimacrotest.py.