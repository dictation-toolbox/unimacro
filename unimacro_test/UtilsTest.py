#
# Python Macro Language for Dragon NaturallySpeaking
#   (c) Copyright 1999 by Joel Gould
#   Portions (c) Copyright 1999 by Dragon Systems, Inc.
#
#   This script performs some tests of natlinkutilsqh functions.
#   The DragonPad window is used, and killed afterwards
#
#   NaturallySpeaking should be running with nothing in the DragonPad window
#   (that you want to preserve) before these tests are run.
#
natqh = __import__('natlinkutilsqh')
natut = __import__('natlinkutils')
reload(natqh)
import actions
action = actions.doAction

import unittest, types
import TestCaseWithHelpers


##class UnimacroUtilsTest(TestCaseWithHelpers.TestCaseWithHelpers):
class UtilsTest(TestCaseWithHelpers.TestCaseWithHelpers):

    # run from dragonpad      
    def setUp(self):
        actions.doAction("BRINGUP dragonpad")

    def tearDown(self):
        actions.doAction("BRINGUP dragonpad; KW")
        
    def log(self, mess):
        if type(mess) == types.StringType:
            actions.doAction(mess)
        else:
            actions.doAction(str(mess))

    def test_Something_in_unimacro(self):
        self.log('testing something')
        actions.doAction("W")
        lang = natqh.getLanguage()
        self.assert_equal("enx", lang, "testing should be done from an English speech profile, not: %s"% lang)

    def test_matchModule(self):
        """check if dragonpad is reported as top window

        and the open dialog as child window

         behaviour changed in python version 2.3.4!!
        """        
        progInfo = natqh.getProgInfo()
        self.log("progInfo: %s"% `progInfo`)
        actions.doAction("LW")
        ## changed in 2013 from 3 to 4 items:
        self.assert_equal(4, len(progInfo), "progInfo should be tuple of 4")
        self.assert_equal(u'top', progInfo[2], "DragonPad should be a top window")
        actions.doAction("<<fileopen>>")
        progInfo = natqh.getProgInfo()
        actions.doAction("{esc}")
        self.assert_equal(4, len(progInfo), "progInfo should be tuple of 4")
        self.assert_equal(u'child', progInfo[2], "DragonPad open dialog should be a child window")
        
    def test_actionsIniFilePresent(self):
        """see if the ini file of actions is there
        can be used to manually test the copying of sample ini files in different configurations
        """
        pass
        ## think about testing the import of actions module in different config settings
        # eg with and without Unimacro enabled, also with different possibilities of sample ini files

        
# no main statement, run from command in _unimacrotest.py