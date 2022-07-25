# (unimacro - natlink macro wrapper/extensions)
# (c) copyright 2003 Quintijn Hoogenboom (quintijn@users.sourceforge.net)
#                    Ben Staniford (ben_staniford@users.sourceforge.net)
#                    Bart Jan van Os (bjvo@users.sourceforge.net)
#
# This file is part of a SourceForge project called "unimacro" see
# http://unimacro.SourceForge.net).
#
# "unimacro" is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License, see:
# http://www.gnu.org/licenses/gpl.txt
#
# "unimacro" is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; See the GNU General Public License details.
#
# "unimacro" makes use of another SourceForge project "natlink",
# which has the following copyright notice:
#
# Python Macro Language for Dragon NaturallySpeaking
#   (c) Copyright 1999 by Joel Gould
#   Portions (c) Copyright 1999 by Dragon Systems, Inc.
#
# solitaire.py
#
# Written by: Quintijn Hoogenboom (QH softwaretraining &
# advies),2002, revised October 2003
# march 2011: change sol to solitaire
"""Grammar for playing solitaire (patience) hands-free

Extensive use is made of mouse (dragging) routines.
"""

import natlink
import win32gui
import types
import time
import os
import os.path
import win32api
from dtactions.unimacro import unimacroutils
from natlinkcore import natlinkutils
from dtactions.unimacro import unimacroutils
import unimacro.natlinkutilsbj as natbj
from dtactions.unimacro.unimacroactions import doAction as action
from dtactions.unimacro.unimacroactions import doAction as action


#aantal carden en aantal stapelplaatsen:
cnum = list(range(1,8))
snum = list(range(1,5))
#card sizes and spacing:
#kwidth, kheight = 72, 96
kwidth, kheight = 93, 121
hspace, vspace = 10,6
cardhspace, cardvspace = 5, 6 # space in stack (horizontal) and on stacks (vertical)
# for mouse lower or higher:
deltaY = 14

# waiting times:
pauzesDelta = 0.1
minPause = 0.5

language = unimacroutils.getLanguage()

ancestor = natbj.DocstringGrammar
class ThisGrammar(ancestor):
    name = 'solitaire'
    iniIgnoreGrammarLists = ['snum', 'cnum'] # are set in this module

    #gramSpec = """ # in the rules docstrings!
    #    """

    def initialize(self):
        global language
        if self.load(self.gramSpec):
            self.setNumbersList("cnum", cnum)
            self.setNumbersList("snum", snum)
            print('grammar solitaire (%s) active'% self.name)
            self.prevHandle = -1
            self.stackAuto = 0
            self.pause = 1
            self.inTimer = 0
            self.pauseTime = 4
        else:
            language = ""
                        
    def cancelMode(self):
        #self.setExclusive(0)
        if self.inTimer:
            print('cancel timer')
            natlink.setTimerCallback(None,0)
            self.inTimer = 0

    def onTimer(self):
        if natlink.getMicState() != 'on':
            print('mic switched off, cancel timer')
            self.cancelMode()
            return
        modInfo = natlink.getCurrentModule()
        if modInfo[2] != self.prevHandle:
            print('window handle changed, cancel timer')
            self.cancelMode()
            return
        print('in onTimer: %.1f'% time.clock())
        self.rule_newcard([])
        

    def gotBegin(self,moduleInfo):
        print('gotbegin, cancelmode')
        self.cancelMode()
        winHandle = moduleInfo[2]
        if self.prevHandle == winHandle: return
        self.prevHandle = winHandle
        if moduleInfo[0].lower().find('solitaire.exe') > 0 and unimacroutils.isTopWindow(moduleInfo[2]):
            if self.checkForChanges:
                print('grammar solitaire (%s) checking the inifile'% self.name)
                self.checkInifile()
            print('self.mayBeSwitchedOn: %s'% self.mayBeSwitchedOn)
            exclusive = self.mayBeSwitchedOn == 'exclusive'
            self.activateAll(exclusive=exclusive)
        else:
            self.deactivateAll()

    #  Bij het initialiseren wordt de horizontale spatiejering uitgerekend.
    #    Er wordt van uitgegaan dat het venster niet te smal staat.
    def gotResultsInit(self,words,fullResults):
        """initialize screen sizes (guesses)
        """
        global hspace, vspace, cardhspace, cardvspace
        clrect = win32gui.GetClientRect(self.prevHandle)
        xMax, yMax = clrect[2]-1, clrect[3]-1
        hspace = (xMax - 7*kwidth)/8
        cardhspace = int(hspace/2)
        cardvspace = vspace
        ## print 'hSpace: %s, xMax: %s, yMax: %s'% (hspace, xMax, yMax)

    def rule_auto(self, words):
        "stack automatically"
        self.stackAuto = 1

    def rule_exclusive(self, words):
        "solitaire [non] exclusive"
        #switches on auto stacking, {ctrl+a} after each move
        self.prevHandle = None # to reactivate in gotBegin
        self.cancelMode()
        if self.hasCommon(words, 'non'):
            self.mayBeSwitchedOn = 1
        else:
            self.mayBeSwitchedOn = 'exclusive'

    # say stop, or even undo the last action
    def rule_stop_undo(self, words):
        "'hold on'|stop|undo"
        self.cancelMode()
        if self.hasCommon(words, 'undo'):
            keystroke('{ctrl+z}')

    #  Go to a card and click on it
    def rule_card(self, words):
        "card {cnum}"
        k = self.getNumberFromSpoken(words[-1])
        self.moveTo(cardpos(k))
        unimacroutils.buttonClick()

    #  Draw a new card and position on the last opened card
    def rule_newcard(self, words):
        "'new card'|next|continue"
        self.moveTo(firstrowpos(1))
        unimacroutils.buttonClick()
        self.moveTo(firstrowpos(2))
        if self.hasCommon(words, 'continue'):
            timeEachMilliseconds = max(1, self.pauseTime)*500
            print('set the timer to %s'% timeEachMilliseconds)
            natlink.setTimerCallback(self.onTimer, timeEachMilliseconds)
            self.inTimer = 1
            
    # Sometimes the mouse is a bit too high (if the stack grows longer)
    # with this command you position the mouse a bit higher or lower
    def rule_lower(self,words):
        "mouse (lower|higher) [{cnum}]"
        n = self.getNumberFromSpoken(words[-1]) or 1
        d = n*deltaY
        if self.hasCommon(words, 'lower'):
            pass
        elif self.hasCommon(words, 'higher'):
            d = -d
        unimacroutils.doMouse(0,2,0,d,0)

    #  Deze grammatica regel stelt de waittijd na elk (deel) van een
    #    commando in. Zie "pauzes" bovenin dit standpunt
    def rule_wait(self, words):
        "pauses (0 |{cnum})"
        i = int(words[-1])
        self.pause = i

    #  Drag a card from the current position to one of the card columns or
    #                                        to one of the 4 stacks
    def rule_to(self, words):
        "to ((stack {snum})|{cnum})"
        
        to = self.getNumberFromSpoken(words[-1])
        unimacroutils.rememberMouse()

        if self.hasCommon(words, 'stack'):
            to = firstrowpos(to+3)
        else:
            to = cardpos(to)
        self.dragTo(to)
        unimacroutils.cancelMouse()
        unimacroutils.buttonClick()

    def rule_testposition(self, words):
        "test position ((stack {snum})|{cnum})"
        #test the stack and piles positions
        #lefttop = (0,0)
        #unimacroutils.doMouse(0, 5, 0,0, 'move')
        #x, y = unimacroutils.getMousePosition(1)
        #print 'screen x,y: %s, %s'% (x,y)
        #x, y = unimacroutils.getMousePosition(5)
        #print 'client: x,y: %s, %s'% (x,y)
        #time.sleep(2)
        to = self.getNumberFromSpoken(words[-1])
        unimacroutils.rememberMouse()

        if self.hasCommon(words, 'stack'):
            to = firstrowpos(to+3)
        else:
            to = cardpos(to)
        print('position: %s'% repr(to))
        self.moveTo(to)
        
    def rule_cardnumto(self, words):
        "[card] {cnum} to ((stack {snum})|{cnum})"
        #card with number to a stack or another card column
        #
        #the first word is optional,and is recognised with the function
        #self.hasCommon, which can handle translations or synonyms
        print('cardnumto: %s'% words)
        unimacroutils.rememberMouse()
        if self.hasCommon(words[0],['card']):
            ww = words[1:]
        else:
            ww = words[:]

        # go to numbered card with mouse:
        From = self.getNumberFromSpoken(words[0])
        self.moveTo(cardpos(From))        

        unimacroutils.rememberMouse()
        to = self.getNumberFromSpoken(words[-1])

        # check if you go to a stack or another card column:        
        if self.hasCommon(words, 'stack'):
            to = firstrowpos(to+3)
        else:
            to = cardpos(to)
        self.dragTo(to)
        unimacroutils.cancelMouse()
        unimacroutils.buttonClick()
    
    def rule_cardto(self, words):
        "card to ((stack {snum})|{cnum})"
        #drag the last drawn card to a stack or to a pile
        print('cardto: %s'% words)

        unimacroutils.rememberMouse()
        self.moveTo(firstrowpos(2))        
        to = self.getNumberFromSpoken(words[-1])
        
        if self.hasCommon(words, 'stack'):
            to = firstrowpos(to+3)
        else:
            to = cardpos(to)
        self.dragTo(to)
        unimacroutils.cancelMouse()
        unimacroutils.buttonClick()
    
    def gotResults(self,words,fullResults):
        """if stack auto, do after each move a {ctrl+a}"""
        if self.stackAuto:
            keystroke('{ctrl+a}')
        
    #  paused a given number of milliseconds 
    #   if this variable = 0 no pausing is done.        
    #    The length of the pauses can be given with
    #    command "pauzes (0 | 1 | 2 | 3 | 4 | 5 | 6 | 7)". 
    #   At the top of this file the increment of the pausing is given.
    def Wait(self, t=None):
        if not t:
            unimacroutils.Wait(self.pause*pauzesDelta+minPause)
        else:
            unimacroutils.Wait(t)

    # move to the given position and have a short wait:
    def moveTo(self, pos):
        unimacroutils.doMouse(0,5, pos[0], pos[1], 'move')
        self.Wait()

    # drag from current position to the new position
    # Pause a few times, dependent on the pause state.
    def dragTo(self, pos):
        xold,yold = unimacroutils.getMousePosition(5)
        print('hold down: %s, %s'% (xold, yold))
        unimacroutils.doMouse(0,5,xold, yold, 'down')
        xyincr = 50
        nstepsx = int(abs(pos[0]-xold)/xyincr)
        nstepsy = int(abs(pos[1]-yold)/xyincr)
        nsteps = max(nstepsx, nstepsy)
        print('nstepsx: %s, nstepsy: %s, nsteps: %s'% (nstepsx, nstepsy, nsteps))
        ysteps = int((pos[1]-yold)/nsteps)
        xsteps = int((pos[0]-xold)/nsteps)
        x, y = xold, yold
        for i in range(nsteps):
            x += xsteps
            y += ysteps
            unimacroutils.doMouse(0,5, x, y, 'move')
            self.Wait(0.01)
        if x != pos[0] or y != pos[1]:
            print('final move: %s, %s, %s, %s'% (x, pos[0], y, pos[1]))
            unimacroutils.doMouse(0,5, pos[0], pos[1], 'move')
            self.Wait(0.01)            
        unimacroutils.doMouse(0,5, pos[0], pos[1], 'move')
        self.Wait(0.01)
        unimacroutils.releaseMouse()
        self.Wait()

            
#  Het berekenen van de coordinaten van cardnummer,i kan liggen
#    tussen 1 en 
def cardpos(i):
    x = i*(hspace+kwidth)-0.5*kwidth
    y = int(2*vspace) + int(2.1*kheight)
    return x,y

# Het berekenen van een positie van een card op de eerste rij.
# Positie 1 is de stapel waaruit gedeeld wordt,
# positie 2 is het stapeltje gedeelde carden,
# en positie i + 3 is de positie van een stapel (i tussen 1 en 4)
def firstrowpos(i):
    """calculate the positions of the first row
    
    1 is pile of closed cards (to click on for new card)
    2 is last cards drawn
    i+3 is stack (stapel) 1,2,3,4
    """
    x = i*(hspace+kwidth)-0.5*kwidth
    if i == 2:
        x += cardhspace
    y = vspace + cardvspace + int(0.5*kheight)
    return x,y

# standard stuff Joel (adapted for possible empty gramSpec, QH, unimacro)
thisGrammar = ThisGrammar()
if thisGrammar.gramSpec:
    thisGrammar.initialize()
else:
    thisGrammar = None

def unload():
    #pylint:disable=W0603
    global thisGrammar
    if thisGrammar: thisGrammar.unload()
    thisGrammar = None

def changeCallback(type,args):
    # not active without special version of natlinkmain,
    # call the cancelMode, to switch off exclusive mode when mic toggles:
    if ((type == 'mic') and (args=='on')):
        return   # check WAS in natlinkmain...
    if thisGrammar:
        print('cancel')
        thisGrammar.cancelMode()
