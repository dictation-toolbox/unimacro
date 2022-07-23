
#
# Python Macro Language for Dragon NaturallySpeaking
#   (c) Copyright 1999 by Joel Gould
#   Portions (c) Copyright 1999 by Dragon Systems, Inc.
#
from pathlib import Path
from pprint import pprint
import sys
unimacrodir = Path('./..').normPath()
if unimacrodir not in sys.path:
    sys.path.append(unimacrodir)
from dtactions.unimacro import unimacroutils
from natlinkcore import natlinkutils
import natlink
from dtactions.unimacro import unimacroactions as actions
# reload(actions)
action = actions.doAction

import unittest
import UnimacroTestHelpers
import time

##class UnimacroBasicTest(TestCaseWithHelpers.TestCaseWithHelpers):
class ActionsTest(UnimacroTestHelpers.UnimacroTestHelpers):
    """Tests several features of the unimacro actions mechanism.

    The wait actions take a little bit more time than asked for.

    Also underlying functions are tested, for example:
test_Convert_to_python_args_numbers
test_Convert_to_python_args_strings,  which are used in converting and actions string
    into a tuple that can be called in python.

    Also the mechanism that an action stops if one of the parts
    (notably a USC,a unimacro shorthand command) returns false.


    """
      
    def setUp(self):
        pass

    def tearDown(self):
        pass


    def doTimingOfAction(self, commandString, timeWanted, epsilon=0.2):
        t0 = time.time()
        actions.doAction(commandString)
        t1 = time.time()
        self.assert_equal(timeWanted, t1-t0, mess="timing not as expected", epsilon=epsilon)

    def doTestActionResult(self, expected, commandString):
        result = actions.doAction(commandString)
        if expected and result:
            pass
        elif not expected and not result:
            pass
        else:
            self.assert_equal(expected, result, "result of action not as expected")

    def test_Convert_to_python_args_numbers(self):
        """numbers should be returned as numbers except when they have leading zeros

        """        
        testFuncReturn = self.doTestFuncReturn
        func = actions.convertToPythonArgs
        testFuncReturn(None, 'func("")', localVars=locals())
        testFuncReturn((0,1,2), 'func("0, 1, 2")', localVars=locals())
        testFuncReturn((0,), 'func("0")', localVars=locals())
        testFuncReturn((23,), 'func("23")', localVars=locals())
        # leading zeros, return string:.        
        testFuncReturn(("0023",), 'func("0023")', localVars=locals())
        testFuncReturn((0.23,), 'func("0.23")', localVars=locals())
        testFuncReturn((0.23, 0, 3.45), 'func("0.23, 0, 3.45")', localVars=locals())

        
    def test_Convert_to_python_args_strings(self):
        """ open and close quotes should be removed from strings

        before passing them to the python function
        """
        testFuncReturn = self.doTestFuncReturn
        func = actions.convertToPythonArgs

        testFuncReturn(('abc',), 'func("abc")', localVars=locals())
        # quotes should be removed:
        testFuncReturn(("single quoted string",), 'func("\'single quoted string\'")', localVars=locals())
        # comma separates:
        testFuncReturn(("double quoted string",), 'func(\'"double quoted string"\')', localVars=locals())
        testFuncReturn(('abc', 'def', 'ghi'), 'func("abc, def, ghi")', localVars=locals())

    def test_Wait_action(self):
        """ waiting should last about the specified time and return true
        """
        testTime = self.doTimingOfAction
        testTime("W", 0.1) # with a tolerance of 0.2 seconds
## these tests take a bit more time, so uncomment only if you want to specifically test to them:
##        testTime("W 1", 1)
##        testTime("W 0.4", 0.4)
##        testTime("W; W", 0.3)
        testActionResult = self.doTestActionResult
        
        testActionResult(1, "W")
        testActionResult(1, "W; W; W")

    def test_KW(self):
        """ kill window testing
        """
        # setup, bringing Dragonpad with open dialog in front:
        action("BRINGUP dragonpad")
        action("testing KW actions")
        action("W 1")
        action("{ctrl+o}") # open dialog dragonpad
        action("W 0.5")
        modInfo = natlink.getCurrentModule()
        handle = modInfo[2]
        self.assert_ (not unimacroutils.isTopWindow(handle), "dialog should be open now")

        # do Notepad and kill, without text in it, so NO SaveAs dialog:
        action("BRINGUP Notepad")
        action("W 0.5")
        action("KW")
        action("W 0.5")
        # now NO kill letter should be printed, because it is again in the
        # DragonPad open dialog:  It
        self.doTestWindowIsEmpty("line in dialog box should be empty now")

        # this is the case in which the kill letter is done inside the SaveAs dialog
        # of Notepad:
        action("BRINGUP Notepad")
        action("abacadabra")
        action("W 0.5")
        action("KW")
        action("W 0.5")
        self.doTestWindowIsEmpty("line in dialog box should still be empty")

        # close DragonPad dialog, leave DragonPad open (if needed)        
        action("{esc}")
        action("<<selectall>><<delete>>")
        action("W 0.5")
        self.doTestWindowIsEmpty("should leave DragonPad empty after testing Kill Window (KW)")
        
        
    def test_Miscelaneous_action_results(self):
        """Actions should return true except some

        A chain of actions is splitted by ";".        
        
        the USC that returns false should also be the return value of the whole action
        """
        testActionResult = self.doTestActionResult
        testActionResult(1, "BRINGUP dragonpad")
        testActionResult(1, "abc")
        
        testActionResult(1, "ghi; W; déf")
        testActionResult(1, "klm; nop")
## next two tests need user interaction.  Activate if you specifically want to test them:
##        testActionResult(1, 'YESNO "please answer yes"')
##        testActionResult(False, 'YESNO please answer no')
        # helper USC commands F and T return False and True:
        testActionResult(False, 'F')
        testActionResult(1, 'T')
        testActionResult(False, 'F; abc')
        testActionResult(1, 'T; def')
        
    def test_Continuation_of_actions(self):
        """If part of the action returns false the action is stopped

        """        
        testWindowContents = self.doTestWindowContents
        
        testActionResult = self.doTestActionResult
        testActionResult(1, "BRINGUP dragonpad")
        testActionResult(1, "<<selectall>><<delete>>")
        # F (false) so nothing happens:
        testActionResult(False, "F; abc")
        testWindowContents("")

        # T (true), so continue "ghi" is printed:        
        testActionResult(1, "T; ghi")
        testWindowContents("ghi")

    def test_one_line_yesno_box(self):
        """should display, answer yes

        """        
        testWindowContents = self.doTestWindowContents
        testActionResult = self.doTestActionResult
        
        testActionResult(True, "YESNO actions test: please answer yes")
        testActionResult(False, "YESNO now please answer No")

         
    def test_Return_to_window(self):
        """bringup calc and wait for calc to be there. 

        """        
        testActionResult = self.doTestActionResult
        testActionResult(1, "RW")
        testActionResult(1, "BRINGUP calc")
        testActionResult(1, "RTW")
        testActionResult(1, "BRINGUP cal")
        testActionResult(1, "<<windowclose>>")
        testActionResult(1, "RTW")

    def test_DATE(self):
        """trying different DATE calls

        """        
        testActionResult = self.doTestActionResult
        testActionResult(1, "BRINGUP dragonpad")
        testActionResult(1, "DATE; ' '")
        testActionResult(1, "DATE 0, print; ' '")
        testActionResult(1, "DATE %d/%m, print; ' '")
        testActionResult(1, "DATE 0, speak")
        testActionResult(1, "DATE %d/%m/%Y")
        testActionResult(1, "DATE %d/%m/%Y, speak")
        testActionResult(1, "YESNO Did you hear a short and a full date?")
        action("KW")
        
    def test_TIME(self):
        """trying different TIME calls

        """        
        testActionResult = self.doTestActionResult
        testActionResult(1, "BRINGUP dragonpad")
        testActionResult(1, "TIME; ' '")
        testActionResult(1, "TIME 0, print; ' '")
        testActionResult(1, "TIME 0, speak")
        testActionResult(1, "TIME %M %H")
        testActionResult(1, "TIME %M %H, speak")
        testActionResult(1, "YESNO Did you hear a normal and a reversed time?")
        action("KW")
        

    def test_HW(self):
        """trying different HW situations

        """        
        testWindowContents = self.doTestWindowContents
        testActionResult = self.doTestActionResult
        testActionResult(1, "BRINGUP dragonpad")
        testActionResult(1, "{ctrl+a}{del}Doing HW test")
        # testing one simple word:
        testActionResult(1, "HW hello")
        testWindowContents("Doing HW test hello")

        testActionResult(1, "{ctrl+a}{del}")

        # test a compound word (U.S. Customs) with a few other words, commas needed:        
        testActionResult(1, "HW U.S. Customs, is, one, word")
        testWindowContents("U.S. Customs is one word")
        testActionResult(1, "{ctrl+a}{del}")

        # test a compound word only (first try goes wrong, because it tries ["U.S.", "Customs"] first.
        testActionResult(1, "HW U.S. Customs")
        testWindowContents("U.S. Customs")

        # trie the command scratch that:        
        testActionResult(1, "{ctrl+a}{del}")
        testActionResult(1, "hello there.")
        testActionResult(1, "HW testing scratch that")
        testWindowContents(["hello there. Testing scratch that",
                            "hello there.  Testing scratch that"], "double spacing possible after period")
        testActionResult(1, "HW scratch that")
        testWindowContents("")

        # trie unrecognised words:
        testActionResult(0, "HW akskskskskskskskksskkssk")

                
    def FAILS_test_multiline_yesno_box(self):
        """should display, answer yes

        messages with multiple lines can only be called from python, not from
        an actions line, please consult also the MessageTest.py
                

        """        
        testWindowContents = self.doTestWindowContents
        testActionResult = self.doTestActionResult
        mes = ["This is window", "that consists of multiple lines","please answer YES again"]
        ### fails::::.
        testActionResult(1, "YESNO %s"% '\n'.join(mes))

         

    

        



# no main statement, run from command in _unimacrotest.py.

