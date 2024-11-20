#
# Python Macro Language for Dragon NaturallySpeaking
#   (c) Copyright 1999 by Joel Gould
#   Portions (c) Copyright 1999 by Dragon Systems, Inc.
#
# unittestMouse.py
# testing the Unimacro mechanism for mousing, recording a position
# absolute or relative (absorrel),
# with respect to screen, activewindow or client area of active window (0, 1 or 5)
# and with respect to one of the corners of a window/client area (1 or 5)
#
# todo: more monitors.
# Quintijn Hoogenboom, july 2012

import sys
import os
import os.path
import natlink
import math
from dtactions.unimacro.unimacroactions import doAction as action
from dtactions.unimacro import unimacroutils as natqh
print('file: %s'% __file__)
#need this here (hard coded, sorry) for it can be run without NatSpeak being on
extraPaths = r"C:\natlink\unimacro", r"D:\natlink\unimacro"
for extraPath in extraPaths:
    if os.path.isdir(extraPath):
        if extraPath not in sys.path:
            sys.path.append(extraPath)
from dtactions.unimacro import unimacroutils
import sys
import unittest
import unittest
import UnimacroTestHelpers

import os
import os.path
import time
import pprint
import TestCaseWithHelpers
class TestError(Exception):pass

#----------------------------
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

natconnectOption = 0 # or 1 for threading, 0 for not. Seems to make difference
                     # with spurious error (if set to 1), missing gotBegin and all that...
logFileName = os.path.join(thisDir, "testresult.txt")



#---------------------------------------------------------------------------
class UnittestMouse(TestCaseWithHelpers.TestCaseWithHelpers):
    def setUp(self):
        pass
    
    def tearDown(self):
        pass

    def tttest_getRectData(self):
        """test the small function getRectData in natlinkutilsqh
        
        give, from a given rectangle, width, height, xMin, yMin, xMax, yMax
        """
        ##     xMin, yMin, xMax, yMax
        rect = 10, 120, 1000, 900
        ##   width, heigth,  xMin, yMin, xMax, yMax
        expected = (990, 780, 10, 120, 1000, 900)
        got = natlinkutilsqh.getRectData(rect)
        self.assert_equal(expected, got, 'getRectData of "%s" did not return the correct results'% repr(rect))

        # rect can be tuple or list:
        ##     xMin, yMin, xMax, yMax
        rect = [-1000, -20, 0, 300]
        ##   width, heigth,  xMin, yMin, xMax, yMax
        expected =  (1000, 320, -1000, -20, 0, 300)
        got = natlinkutilsqh.getRectData(rect)
        self.assert_equal(expected, got, 'getRectData of "%s" did not return the correct results'% rect)

    def tttest_coordToRel_and_relToCoord(self):
        """test the functions to calculate relative coordinates and back
        
        functions are in natlinkutilsqh.py and are used with doMouse and getMousePosition
        
        (x can be exchanged to y of course)
        """
        xMin, xMax = 20, 1000
        # from xMin (relX positive)
        for x in (20, 200, 500, 800, 900, 990, 999):
            relX = natlinkutilsqh.coordToRel(x, xMin, xMax)
            self.assertTrue(relX >=0, "coordToRel, result should be positive (x: %s, xMin, %s, xMax: %s, relX: %.6s"%
                         (x, xMin, xMax, relX))
            relX = round(relX, 3)
            result = natlinkutilsqh.relToCoord(relX, xMin, xMax)
            self.assert_equal(x, result, "relative value changes coordinate: %s to %s"% (x, result), epsilon=0)

        # from xMax (relX negative)
        for x in (20, 200, 500, 800, 900, 990, 999):
            relX = natlinkutilsqh.coordToRel(x, xMin, xMax, side=1)
            relX = round(relX, 3)
            self.assertTrue(relX < 0, "coordToRel, result should be negative (x: %s, xMin, %s, xMax: %s, relX: %.6s"%
                         (x, xMin, xMax, relX))
            result = natlinkutilsqh.relToCoord(relX, xMin, xMax)
            self.assert_equal(x, result, "relative value changes coordinate (from xMax): %s to %s (relX: %.6s"% (x, result, relX), epsilon=0)


    def tttest_getOutsideWindow(self):
        """try to position on the taskbar and get the position
        """
        
        action("RMP(5, 1, 0.5, noclick)") # relative in foreground window, tune to your testing!
        action("MP(2, 500, 0, noclick)")   # move a bit to the right
        initialPosition = natlink.getCursorPos()
        mousePos = natlinkutilsqh.getMousePosition() # abs, screen, corner not relevant
        if mousePos is None:
            self.fail("could not get mouse position")
        x, y = mousePos
        absorrel, which = 0, 0
        natlinkutilsqh.doMouse(absorrel, which, x, y, mouse="noclick")
        finalPosition = natlink.getCursorPos()
        log('command outside window(?): %s, %s, %s, %s, initial: %s, final: %s'% (absorrel, which, x, y, repr(initialPosition), repr(finalPosition)))
        self.assert_equal(initialPosition, finalPosition, "position of mouse after move outside the current window should be the same\n"
                "absorrel: %s, which: %s"% (absorrel, which))


        
        
    def tttest_getPositions(self):
        """test setting and getting positions in all possible ways
        
        use action RMP to go to the wanted position.
        
        then each time get a position
        (absolute/relative, absorrel, screen, active window or client area (0, 1, 5),
        and relative to one of the corners (0, 1, 2, 3))
        setting it again and see if same position is found
        
        get with: getMousePosition
        set with: doMouse
        """
        #absorrel = 0 # absolute
        #which = 0 # whole screen
        #corner = 0 # top left
        action("RMP(5, 0.3, 0.4, noclick)") # relative in foreground window, tune to your testing!
        
        initialPosition = natlink.getCursorPos()
        for absorrel in (0, 1):
            for which in (0, 1, 5):
                for cornerPos in range(4):
                    #absorrel, which, cornerPos = 1, 0, 0
                    #absorrel = 1
                    # each test, little shifting for relative allowed
                    if absorrel:
                        epsilon = 0 # relative, position may shift a bit...
                    else:
                        epsilon = 0  # absolute, caculations must fit
                    if absorrel == 0 and which == 0 and cornerPos > 0:
                        print('invalid combination to test: absorrel: %s, which: %s, cornerPos: %s'% (absorrel, which, cornerPos))
                        continue
                    initialPosition = natlink.getCursorPos()
                        
                    mousePos = natlinkutilsqh.getMousePosition(absorrel, which, cornerPos)
                    if mousePos is None:
                        self.fail('getMousePosition in test suite should not result in None (absorrel: %s, which: %s, cornerPos: %s)'%
                                   (absorrel, which, cornerPos))
                    x, y = mousePos
                    natlinkutilsqh.doMouse(absorrel, which, x, y, mouse="noclick")
                    finalPosition = natlink.getCursorPos()
                    log('command: %s, %s, %s, %s, initial: %s, final: %s'% (absorrel, which, x, y, repr(initialPosition), repr(finalPosition)))
                    self.assert_equal(initialPosition, finalPosition, "position of mouse after simple action should be the same\n"
                            "absorrel: %s, which: %s, cornerPos: %s"% (absorrel, which, cornerPos),
                            epsilon=epsilon)
  
    def test_doMouse(self):
        """problem with doMouse (natlinkutilsqh) with second screen LEFT of first"""
        unimacroutils.doMouse(0, 0, 35, 188, 0)
        pass
                            

def log(t):
    """log to print and file if present

    note print depends on the state of natlink: where is goes or disappears...
    I have no complete insight is this, but checking the logfile afterwards
    always works (QH)
    """
    print(t)
    if logFile:
        logFile.write(t + '\n')


logFile = None

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

def run():
    global logFile, natconnectOption
    logFile = open(logFileName, "w")
    log("log messages to file: %s"% logFileName)
    log('starting UnittestMouse')
    # trick: if you only want one or two tests to perform, change
    # the test names to her example def tttest....
    # and change the word 'test' into 'tttest'...
    # do not forget to change back and do all the tests when you are done.
    suite = unittest.makeSuite(UnittestMouse, 'test')
##    natconnectOption = 0 # no threading has most chances to pass...
    log('\nstarting tests with threading: %s\n'% natconnectOption)
    natlink.natConnect(natconnectOption)
    result = unittest.TextTestRunner().run(suite)
    dumpResult(result, logFile=logFile)
    natlink.natDisconnect()
    logFile.close()

    

if __name__ == "__main__":
    run()
