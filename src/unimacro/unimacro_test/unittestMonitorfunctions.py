#
# Python Macro Language for Dragon NaturallySpeaking
#   (c) Copyright 1999 by Joel Gould
#   Portions (c) Copyright 1999 by Dragon Systems, Inc.
#
# unittestMonitorfunction.py
# this script tests the monitor functions, which control windows on (multiple)
# monitors.
# note monitorfunctions.py is in the Unimacro release.
# this test can be run standalone, without NatSpeak or NatLink being on or
# activated.
#
#
# Developed by Quintijn Hoogenboom, q.hoogenboom@antenna.nl /
# http://qh.antenna.nl/unimacroß
import sys
import os
import os.path

# trick in order to be sure the unimacro directory is in sys.path:
thisDir = os.path.dirname(__file__)
unimacroDir = os.path.normPath(os.path.join(thisDir, '..'))
if os.path.isdir(unimacroDir):
    if unimacroDir not in sys.path:
        sys.path.append(unimacroDir)

import unittest
import time
import win32gui
import win32ui
import TestCaseWithHelpers
class TestError(Exception):pass

#---------------------------------------------------------------------------
class UnittestMonitorfunctions(TestCaseWithHelpers.TestCaseWithHelpers):
    def setUp(self):
        """setup with 2 monitors, primary left,
            NatSpeak taskbar top primary (29 height),
            Windows taskbar left secondary monitor (width 109)
            (you can check your parameters by running monitorfunctions.py itself)
        """
        mf.monitor_info()
        mf.VIRTUAL_SCREEN = [0, 0, 2704, 1050]
        mf.NMON = 2
        mf.BORDERX = mf.BORDERY = 1
        mf.MONITOR_HNDLES = [65537, 65539]
        mf.MONITOR_INFO[65537] = {'Device': '\\\\.\\DISPLAY1',
                'Flags': 1,
                'Monitor': (0, 0, 1680, 1050),
                'Work': (0, 29, 1680, 1050),
                'offsetx': 0,
                'offsety': 29}
        mf.MONITOR_INFO[65539] = {'Device': '\\\\.\\DISPLAY2',
                'Flags': 0,
                'Monitor': (1680, 0, 2704, 768),
                'Work': (1787, 0, 2704, 768),
                'offsetx': 107,
                'offsety': 0}
                   
    def tearDown(self):
        mf.monitor_info()
        
    
    def wait(self, multiple=1):
        time.sleep(0.1*multiple)
    def visibleWait(self, multiple=1):
        time.sleep(0.7*multiple)

    def doTestGetDistanceInDirection(self, RA, BB, angle, expDist, epsilon=0.01):
        """check the result of the function _get_distance_in_direction
        
        (calculating the distance to an edge of the bounding box)
        """
        mess = "doTestGetDistanceInDirection"
        dist = mf._get_distance_in_direction(RA, BB, angle)
        mess1 = "%s: testing distance, angle: %s"% (mess, angle)
        self.assert_equal(expDist, dist,mess1, epsilon=epsilon)
        return dist

    def test_changing_monitor_info(self):
        """this is a vulnerable test, see if changing (fake) monitor data come through
        """
        fake_nmon = 7
        fake_virtual_screen = [0,0,100,100]
        nmon_now = mf.NMON
        v_s_now = mf.VIRTUAL_SCREEN[:]
        mf.fake_monitor_info_for_testing(nmon=7, virtual_screen=fake_virtual_screen)
        expected = fake_nmon
        actual = mf.NMON
        self.assert_equal(expected, actual, "fake monitor info, NMON not as expected")
        expected = fake_virtual_screen
        actual = mf.VIRTUAL_SCREEN
        self.assert_equal(expected, actual, "fake monitor info, VIRTUAL_SCREEN not as expected")
        

    def test_get_distance_in_direction(self):
        RA = [100, 200, 900, 600]
        boundingbox = [0, 0, 1200, 800]
        BB = boundingbox
        funcDistance = self.doTestGetDistanceInDirection
        funcDistance(RA, BB, 0, 200)
        funcDistance(RA, BB, 10, 203.08)
        funcDistance(RA, BB, 30, 230.94)
        funcDistance(RA, BB, 60, 346.41)
        funcDistance(RA, BB, 90, 300)
        funcDistance(RA, BB, 100, 304.63)
        funcDistance(RA, BB, 130, 311.14)
        funcDistance(RA, BB, 160, 212.84)
        funcDistance(RA, BB, 180, 200)
        funcDistance(RA, BB, 190, 203.08)
        funcDistance(RA, BB, 200, 212.84)
        funcDistance(RA, BB, 209, 206.27)
        funcDistance(RA, BB, 210, 200)
        funcDistance(RA, BB, 220.5, 153.98)
        funcDistance(RA, BB, 260, 101.54)
        funcDistance(RA, BB, 270, 100.0)
        funcDistance(RA, BB, 280, 101.54)
        funcDistance(RA, BB, 300, 115.47)
        funcDistance(RA, BB, 325, 174.34)
        funcDistance(RA, BB, 340, 212.84)
        funcDistance(RA, BB, 350, 203.09)
        funcDistance(RA, BB, 359, 200.030)
        funcDistance(RA, BB, 360, 200)
        funcDistance(RA, BB, 361, 200.03)
        
        # testing slow changes (jumps of maximum)
        dist = 200
        for i in range(360):
            newDist = funcDistance(RA, BB, i, expDist=dist,epsilon=10)
            #print 'i: %s dist: %s delta:(%s)'% (i, newDist, newDist - dist)
            dist = newDist
            
        # R outside BB:
        BB = [0, 0, 1000, 800]
        # first quadrant
        funcDistance( [0, -10, 900, 700], BB, 45, 0)
        funcDistance( [0, -10, 900, 700], BB, 89, 0)
        funcDistance( [0, -10, 900, 700], BB, 90, 100)
        
        # second quadrant
        funcDistance( [0, 10, 1000, 700], BB, 90, 0)
        funcDistance( [0, 10, 1000, 700], BB, 100, 0)
        funcDistance( [0, 10, 1000, 700], BB, 170, 0)
        funcDistance( [0, 10, 1000, 700], BB, 180, 100)

        # third quadrant
        funcDistance( [10, 10, 1000, 900], BB, 190, 0)
        funcDistance( [10, 10, 1000, 900], BB, 200, 0)
        funcDistance( [10, 10, 1000, 900], BB, 225, 0)
        funcDistance( [10, 10, 1000, 900], BB, 270, 10)
        
        # fourth quadrant
        funcDistance( [10, -10, 1000, 900], BB, 290, 0)
        funcDistance( [10, -10, 1000, 900], BB, 300, 0)
        funcDistance( [10, -10, 1000, 900], BB, 325, 0)
        funcDistance( [10, -10, 1000, 900], BB, 360, 0)

        for i in range(362):
            # at all edges no distance:
            funcDistance(BB, BB, i, 0, epsilon=0)
        
        
    def doTestNewCoordinatesSameMonitor(self, begin, end, size, width,
                                        positioning, expBegin, expEnd):
        """check the result of the function is resultx, resulty
        """
        mess = "doTestNewCoordinatesSameMonitor"
        begin1, end1 = mf._get_new_coordinates_same_monitor(begin, end, size, width, positioning)
        mess1 = "%s: testing begin of result"% mess
        self.assert_equal(expBegin, begin1, mess1)
        mess1 = "%s: testing end of result"% mess
        self.assert_equal(expEnd, end1, mess1)

    def test_get_new_coordinates_same_monitor(self):
        testname = 'test_get_new_coordinates_same_monitor'
        funcSame = self.doTestNewCoordinatesSameMonitor
        # width same (move)
        funcSame(10, 790, 1000, None, 'left', 0, 780)
        funcSame(10, 790, 1000, None, 'middle', 110, 890)
        funcSame(10, 790, 1000, None, 'right', 220, 1000)
        # useless, nothing changes:
        funcSame(10, 790, 1000, None, 'relative', 10, 790)
        # width 0.5
        funcSame(10, 790, 1000, 0.5, 'left', 0, 500)
        funcSame(10, 790, 1000, 0.5, 'middle', 250, 750)
        funcSame(10, 790, 1000, 0.5, 'right', 500, 1000)
        funcSame(10, 790, 1000, 0.5, 'relative', 22, 522)


    def doTestNewCoordinatesResizeOtherMonitor(self, begin, end, oldSize, newSize,
                                                     expBegin, expEnd):
        """check the result of the function is resultx, resulty
        """
        mess = "doTestNewCoordinatesResizeOtherMonitor"
        begin1, end1 = mf._get_new_coordinates_resize_other_monitor(begin, end, oldSize, newSize)
        mess1 = "%s: testing begin of result"% mess
        self.assert_equal(expBegin, begin1, mess1)
        mess1 = "%s: testing end of result"% mess
        self.assert_equal(expEnd, end1, mess1)


    
    def test_get_new_coordinates_resize_other_monitor(self):
        funcResizeOther = self.doTestNewCoordinatesResizeOtherMonitor
        # resize, 
        # on and off, back and forth:
        funcResizeOther(10, 790, 800, 1200, 15, 1185)
        funcResizeOther(15, 1185, 1200, 800, 10, 790)
     
    def doTestNewCoordinatesFixedOtherMonitor(self, begin, end, oldSize, newSize,
                                                     expBegin, expEnd):
        """check the result of the function is resultx, resulty
        """
        mess = "doTestNewCoordinatesFixedOtherMonitor"
        begin1, end1 = mf._get_new_coordinates_fixed_other_monitor(begin, end, oldSize, newSize)
        mess1 = "%s: testing begin of result"% mess
        self.assert_equal(expBegin, begin1, mess1)
        mess1 = "%s: testing end of result"% mess
        self.assert_equal(expEnd, end1, mess1)

     
    def test_get_new_coordinates_fixed_other_monitor(self):
        
        funcFixedOther = self.doTestNewCoordinatesFixedOtherMonitor
        # fixed 
        # on and off, back and forth:
        funcFixedOther(10, 790, 800, 1200, 210, 990)
        funcFixedOther(210, 990, 1200, 800, 10, 790)


    def doTestMovePixelsAndBack(self, oldRA, amount, direction, expRA, opposite, mess):
        """move pixels one way, test and move back, test
        """
        mi = mf.MONITOR_INFO[65537]
        mess2 = mess + '  expected RA, after moving (PIXEL) amount: %s, direction: %s'% (amount, direction)
        newRA = mf._move_resize_restore_area(oldRA, resize=0, direction=direction,
                                             amount=amount, units='pixels',keepinside=0, keepinsideall=0,
                                             monitor_info=mi)
        self.assert_equal(expRA, newRA, mess2)
        backRA = mf._move_resize_restore_area(newRA, resize=0, direction=opposite,
                                             amount=amount, units='pixels',keepinside=0, keepinsideall=0,
                                             monitor_info=mi)
        mess2 = mess + 'expected RA, after moving (back) (PIXEL) amount: %s, direction: %s'% (amount, opposite)
        self.assert_equal(oldRA, backRA, mess2)
        
    def doTestMovePixels(self, oldRA, amount, direction, expRA, mess):
        """move pixels one way, test
        """
        mi = mf.MONITOR_INFO[65537]
        mess2 = mess + '  expected RA, after moving (PIXEL) amount: %s, direction: %s'% (amount, direction)
        newRA = mf._move_resize_restore_area(oldRA, resize=0, direction=direction,
                                             amount=amount, units='pixels',keepinside=0, keepinsideall=0,
                                             monitor_info=mi)
        self.assert_equal(expRA, newRA, mess2)
        
    def doTestMoveRelative(self, oldRA, amount, direction, expRA, mess):
        """move relative to some side or corner
        """
        mi = mf.MONITOR_INFO[65537]
        mess2 = mess + '  expected RA, after moving (RELATIVE) amount: %s, direction: %s'% (amount, direction)
        newRA = mf._move_resize_restore_area(oldRA, resize=0, direction=direction,
                                             amount=amount, units='relative',keepinside=0, keepinsideall=0,
                                             monitor_info=mi)
        self.assert_equal(expRA, newRA, mess2)
        

    def test_move_resize_restore_area_move_pixels(self):
        """test the function which gives back a new RA
                
        moving an amount of pixels
                
        """
        testname = "test_move_resize_restore_area_move_pixels"
        ##############################
        #### first set of variables,  no resize
        # no resize, 
        oldRA = [10, 20, 790, 580]
        
        # left, right
        #amount, direction, opposite = 5, 'left', 'right'
        self.doTestMovePixelsAndBack([10, 20, 790, 580], 5, 'left', [5, 20, 785, 580], 'right', testname)
        
        #up, down:
        self.doTestMovePixelsAndBack([10, 20, 790, 580], 6, 'up', [10, 14, 790, 574], 'down', testname)
        
        # lefttop, rightbottom:[13, 27, 793, 577]
        self.doTestMovePixels([10, 30, 790, 580], 6, 'lefttop', [8, 24, 788, 574], testname)
        self.doTestMovePixels([10, 30, 790, 580], 60, 'rightbottom', [64, 57, 844, 607], testname)
        self.doTestMovePixels([10, 30, 790, 580], 12, 'leftbottom', [10, 42, 790, 592], testname)
        self.doTestMovePixels([10, 30, 790, 580], 100, 'righttop', [110, 27, 890, 577], testname)

        # relative amounts:
        self.doTestMoveRelative([10, 30, 790, 580], 0.1, 'lefttop', [9, 27, 789, 577], testname)
        self.doTestMoveRelative([10, 30, 790, 580], 0.5, 'lefttop', [5, 15, 785, 565], testname)
        self.doTestMoveRelative([10, 30, 790, 580], 1, 'lefttop', [0, 0, 780, 550], testname)
        
        self.doTestMoveRelative([10, 30, 790, 580], 0.1, 'righttop', [99, 27, 879, 577], testname)
        self.doTestMoveRelative([10, 30, 790, 580], 0.5, 'righttop', [455, 15, 1235, 565], testname)
        self.doTestMoveRelative([10, 30, 790, 580], 1, 'righttop', [900, 0, 1680, 550], testname)

        self.doTestMoveRelative([10, 30, 790, 580], 0.1, 'rightbottom', [99, 74, 879, 624], testname)
        self.doTestMoveRelative([10, 30, 790, 580], 0.5, 'rightbottom', [455, 251, 1235, 801], testname)
        self.doTestMoveRelative([10, 30, 790, 580], 1, 'rightbottom', [900, 471, 1680, 1021], testname)

        self.doTestMoveRelative([10, 30, 790, 580], 0.1, 'leftbottom', [9, 74, 789, 624], testname)
        self.doTestMoveRelative([10, 30, 790, 580], 0.5, 'leftbottom', [5, 251, 785, 801], testname)
        self.doTestMoveRelative([10, 30, 790, 580], 1, 'leftbottom', [0, 471, 780, 1021], testname)


    def doTestAdjustCoordinatesSideCornersMove(self, oldRA, amountx, amounty,
                                                    side_corner, expRA, mess):
        """test the result of an adjustment to one side or corner
        """
        resize = 0
        newRA = mf._adjust_coordinates_side_corners(oldRA, amountx, amounty, resize,
                                                 side_corner=side_corner, min_size=(100, 70))
        mess1 = "doTest_adjust_coordinates_side_corners_move, %s with\namountx: %x, amounty: %s\n" \
                "resize: %s, side_corner: %s"% (mess, amountx, amounty, resize, side_corner)
        mess2 = "%s, TESTING expectedRA"% mess1
        self.assert_equal(expRA, newRA, mess2)
        
    def doTestAdjustCoordinatesSideCornersResizePlus(self, oldRA, amountx, amounty,
                                                    side_corner, expRA, mess):
        """test the result of an adjustment to one side or corner, making larger, resize = 1
        """
        resize = 1
        newRA = mf._adjust_coordinates_side_corners(oldRA, amountx, amounty, resize,
                                                 side_corner=side_corner, min_size=(100, 70))
        mess1 = "doTestAdjustCoordinatesSideCornersResizePlus, %s with\namountx: %x, amounty: %s\n" \
                "resize: %s, side_corner: %s"% (mess, amountx, amounty, resize, side_corner)
        mess2 = "%s, TESTING expectedRA"% mess1
        self.assert_equal(expRA, newRA, mess2)

    def doTestAdjustCoordinatesSideCornersResizeMinus(self, oldRA, amountx, amounty,
                                                    side_corner, expRA, mess):
        """test the result of an adjustment to one side or corner, making smaller, resize = -1
        """
        resize = -1
        newRA = mf._adjust_coordinates_side_corners(oldRA, amountx, amounty, resize,
                                                 side_corner=side_corner, min_size=(100, 70))
        mess1 = "doTestAdjustCoordinatesSideCornersResizePlus, %s with\namountx: %x, amounty: %s\n" \
                "resize: %s, side_corner: %s"% (mess, amountx, amounty, resize, side_corner)
        mess2 = "%s, TESTING expectedRA"% mess1
        self.assert_equal(expRA, newRA, mess2)
        
 
    def test_adjust_coordinates_side_corners(self):
        """test the function which adjusts the RA towards a corner point
                
        """
        testname = "test_adjust_coordinates_side_corners"
        #
        funcMove = self.doTestAdjustCoordinatesSideCornersMove
        funcMove([10, 20, 790, 580], -5, -6, 'lefttop', [5, 14, 785, 574], "moving to lefttop")
        # to lefttop also without giving this direction:
        funcMove([10, 20, 790, 580], -5, -6, None, [5, 14, 785, 574], "moving to lefttop(None given)")
        
        funcMove([10, 20, 790, 580], 5, -6, 'righttop', [15, 14, 795, 574], "moving to righttop")
        # to lefttop also without giving this direction:
        funcMove([10, 20, 790, 580], 5, -6, None, [15, 14, 795, 574], "moving to righttop (None given)")
        
        funcMove([10, 20, 790, 580], 5, 6, 'rightbottom', [15, 26, 795, 586], "moving to rightbottom")
        # to lefttop also without giving this direction:
        funcMove([10, 20, 790, 580], 5, 6, None, [15, 26, 795, 586], "moving to rightbottom (None given)")
        
        funcMove([10, 20, 790, 580], -5, 6, 'leftbottom', [5, 26, 785, 586], "moving to leftbottom")
        # to lefttop also without giving this direction:
        funcMove([10, 20, 790, 580], -5, 6, None, [5, 26, 785, 586], "moving to leftbottom (None given)")
        
        # not exactly in the direction (overshooting possibly)
        funcMove([10, 20, 790, 580], -50, 6, 'leftbottom', [-40, 26, 740, 586], "moving to the left of leftbottom")
        funcMove([10, 20, 790, 580], -5, -60, 'leftbottom', [5, -40, 785, 520], "moving up instead of to leftbottom")
        
        #### second set of variables, with resize = 1 (making window larger)
        funcStretch = self.doTestAdjustCoordinatesSideCornersResizePlus
        funcStretch([10, 20, 790, 580], -5, -6, 'lefttop', [5, 14, 790, 580], "stretching (larger) to lefttop")
        # to lefttop also without giving this direction:
        funcStretch([10, 20, 790, 580], -5, -6, None, [5, 14, 790, 580], "stretching (larger) to lefttop(None given)")
        
        funcStretch([10, 20, 790, 580], 5, -6, 'righttop', [10, 14, 795, 580], "stretching (larger) to righttop")
        # to righttop also without giving this direction:
        funcStretch([10, 20, 790, 580], 5, -6, None,[10, 14, 795, 580], "stretching (larger) to righttop (None given)")
        
        funcStretch([10, 20, 790, 580], 8, 7, 'rightbottom', [10, 20, 798, 587], "stretching (larger) to rightbottom")
        # to rightbottom also without giving this direction:
        funcStretch([10, 20, 790, 580], 8, 7, None, [10, 20, 798, 587], "stretching (larger) to rightbottom (None given)")
        
        funcStretch([10, 20, 790, 580], -3, 9, 'leftbottom', [7, 20, 790, 589], "stretching (larger) to leftbottom")
        # to leftbottom also without giving this direction:
        funcStretch([10, 20, 790, 580], -3, 9, None, [7, 20, 790, 589], "stretching (larger) to leftbottom (None given)")
        
        # not exactly in the direction (overshooting possible, keepinside is checked later)
        funcStretch([10, 20, 790, 580], -50, 6, 'leftbottom', [-40, 20, 790, 586], "stretching (larger) to the left of leftbottom")
        funcStretch([10, 20, 790, 580], -5, -60, 'leftbottom', [5, 20, 790, 520], "stretching (larger) up instead of to leftbottom")
        
        # making size minimal:
        funcStretch([10, 20, 790, 580], 1000, 0, 'lefttop', [690, 20, 790, 580], "resizing too much left side, using min_size[0]")
        funcStretch([10, 20, 790, 580], 0, 700, 'lefttop', [10, 510, 790, 580], "resizing too much top, using min_size[1]")
        funcStretch([10, 20, 790, 580], -1000, 0, 'rightbottom', [10, 20, 110, 580], "resizing too much right side, using min_size[0]")
        funcStretch([10, 20, 790, 580], 0, -700, 'rightbottom', [10, 20, 790, 90], "resizing too much bottom, using min_size[1]")
        # combined:
        funcStretch([10, 20, 790, 580], -1000, 700, 'righttop', [10, 510, 110, 580], "resizing too much righttop, using min_size")
        funcStretch([10, 20, 790, 580], 1000, -700, 'leftbottom', [690, 20, 790, 90], "resizing too much leftbottom, using min_size")
        
        #### third set of variables, with resize = -1 (making window smaller)
        funcShrink = self.doTestAdjustCoordinatesSideCornersResizeMinus
        funcShrink([10, 20, 790, 580], -5, -6, 'lefttop', [5, 14, 790, 580], "adjusting to lefttop (resize -1 ignored)")
        # shrink from rightbottom if not side_corner given:
        funcShrink([10, 20, 790, 580], -5, -6, None, [10, 20, 785, 574], "shrinking (smaller) at rightbottom (None given)")
        
        funcShrink([10, 20, 790, 580], 5, -6, 'righttop', [10, 14, 795, 580], "adjust at righttop  (resize -1 ignored)")
        # to lefttop also without giving this direction:
        funcShrink([10, 20, 790, 580], 5, -6, None, [15, 20, 790, 574], "shrinking (smaller) at leftbottom (None given)")
        
        funcShrink([10, 20, 790, 580], 8, 7, 'rightbottom', [10, 20, 798, 587], "adjust at rightbottom  (resize -1 ignored)")
        # to lefttop also without giving this direction:
        funcShrink([10, 20, 790, 580], 8, 7, None, [18, 27, 790, 580], "shrinking (smaller) at lefttop (None given)")
        
        funcShrink([10, 20, 790, 580], -3, 9, 'leftbottom', [7, 20, 790, 589], "adjust at (resize -1 ignored)")
        # to lefttop also without giving this direction:
        funcShrink([10, 20, 790, 580], -3, 9, None, [10, 29, 787, 580], "shrinking (smaller) at righttop (None given)")
        

        # making size minimal (identical to funcStretch above, because resize is not used when direction is given):
        # combined, see examples with funcStretch.
        funcShrink([10, 20, 790, 580], -1000, 700, 'righttop', [10, 510, 110, 580], "resizing too much righttop, using min_size")
        funcShrink([10, 20, 790, 580], 1000, -700, 'leftbottom', [690, 20, 790, 90], "resizing too much leftbottom, using min_size")

        # shrinking with automatic direcion to keeping min_size:
        funcShrink([10, 20, 790, 580], -1000, 700, None, [10, 510, 110, 580], "shrinking too much direction None, using min_size")
        funcShrink([10, 20, 790, 580], 1000, -700, None, [690, 20, 790, 90], "shrinking too much direction None, using min_size")
        funcShrink([10, 20, 790, 580], 1000, 700, None, [690, 510, 790, 580], "shrinking too much direction None, using min_size")
        funcShrink([10, 20, 790, 580], -1000, -700, None, [10, 20, 110, 90], "shrinking too much direction None, using min_size")
        
        ###############################
        ##### fourth set of variables, with 'center' values, making resize dependent on amountx, amounty
        ## no resize, not important from which side_corner you start
        #resize = 0
        #oldRA = [10, 20, 790, 580]
        #oldWidth, oldHeight = oldRA[2] - oldRA[0], oldRA[3] - oldRA[1]
        #amountx, amounty = -5, -6
        #
        ## most sensible direction:
        #side_corner = 'center'
        #testRA = oldRA[:]
        #newRA = mf._adjust_coordinates_side_corners(oldRA[:], amountx, amounty, resize,
        #                                         side_corner=side_corner, minSize=10)
        #expRA = [13, 23, 788, 576]
        ## assert for testing:
        #mess = '%s, oldRA should be unchanged.'% testname
        #self.assert_equal(testRA, oldRA, mess)
        #
        #messgroup = '%s, resize centered.'% testname
        #mess = '%s, testing expected RA'% messgroup
        #self.assert_equal(expRA, newRA, mess)
        
        # invalid values for side_corner:
        RA = [10, 20, 790, 580]
        func = mf._adjust_coordinates_side_corners
        self.assertRaises(ValueError, func, RA, 0, 0, 0, side_corner='typo')
        self.assertRaises(ValueError, func, RA, 0, 0, 0, side_corner=0)
        self.assertRaises(ValueError, func, RA, 0, 0, 0, side_corner=1)

        # invalid values for resize:
        self.assertRaises(ValueError, func, RA[:], 4, 5, resize='typo', side_corner=None)
        self.assertRaises(ValueError, func, RA[:], 2, 6, resize=1.3, side_corner=None)
        self.assertRaises(ValueError, func, RA[:], 1, 7, resize=-2, side_corner=None)

    def doTestGetAngleDistanceReverse(self, px, py, qx, qy, expAngle, expDist, mess):
        """test angle distance from p towards q and back
        """
        mess1 = "test_get_angle_distance_reverse, %s"% mess
        # first function:

        angle, dist = mf._get_angle_distance(px, py, qx, qy)
        mess2 = '%s, distance'% mess1
        self.assert_equal(expDist, dist, mess2, epsilon=0.01)
        mess2 = '%s, angle'% mess1
        self.assert_equal(expAngle, angle, mess2, epsilon=0.01)
        # second function:
        deltax, deltay = mf._get_deltax_deltay_from_angle_distance(angle, dist)
        expDeltax = qx - px
        expDeltay = qy - py
        mess2 = '%s calculating back, deltax'% mess1
        self.assert_equal(expDeltax, deltax, mess2, epsilon=0.01)
        mess2 = '%s calculating back, deltay'% mess1
        self.assert_equal(expDeltay, deltay, mess2, epsilon=0.01)
        

    def test_get_angle_distance_reverse(self):
        """test the function which calculates angle and distance between two points
        
        plus the reverse function _get_deltax_deltay_from_angle_distance
        
        
        """
        testname = "test_get_angle_distance_reverse"
        self.doTestGetAngleDistanceReverse(50, 50, 200, 0, 71.5650511771, 158.11, "first quadrant")
        self.doTestGetAngleDistanceReverse(50, 700, 1000, 800, 96.0, 955.24, "second quadrant")
        self.doTestGetAngleDistanceReverse(80, 50, 0, 600, 188.27, 555.78, "third quadrant")
        self.doTestGetAngleDistanceReverse(20, 100, 0, 0, 348.7, 101.98, "fourth quadrant")

        self.doTestGetAngleDistanceReverse(0, 100, 0, 0, 0, 100, "point up")
        self.doTestGetAngleDistanceReverse(300, 600, 1000, 600,  90, 700, "point right")
        self.doTestGetAngleDistanceReverse(800, 50, 800, 600,  180, 550, "point down")
        self.doTestGetAngleDistanceReverse(200, 0, 0, 0, 270, 200, "point left")

        self.doTestGetAngleDistanceReverse(1, 1, 1, 1, 0, 0, "no distance")
        
def run():
    print('starting unittestMonitorfunctions')
    unittest.main()
    

if __name__ == "__main__":
    run()
