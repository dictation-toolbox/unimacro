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
# _repeat (was _generic_movement.py)

# Written by: Quintijn Hoogenboom (QH softwaretraining & advies)
# revisionDate = 'August 2003'/febr 2006
"""grammar in which the cursor, the mouse can move select and drag.

This grammar is based on Joel Gould's _mouse.py and Jonathan Epstein's
version of _generic_movement.py.

Also automatic repeating of commands is going to be implemented in this
grammar.

-added continuous search

"""

#
from dtactions.unimacro import unimacroutils
from dtactions.unimacro import unimacroutils
import unimacro.natlinkutilsbj as natbj
from natlinkcore import natlinkutils
from dtactions.unimacro.unimacroactions import doAction as action

import os
import os.path
import sys
import time         # for clock
import natlink
import natlinktimer
import types

DEBUG = 0

stateError = 'invalid state for timer routine'

# For caret movement, this represents the default speed in milliseconds
# between arrow keys

states = ['moving', 'selecting', 'repeating', 'mousing',
          'movingpage', 'selectingpage', 'dragging', 'searching']

defaultSpeed = {
    'normal': (50, 4000),
    'moving': (50, 2000),
    'selecting': (100, 3000),
    'movingpage':  (300, 5000),
    'selectingpage': (500, 6000),
    'repeating': (500, 5000),
    'mousing':  (2, 200),
    'dragging':  (2, 100),
    'searching':  (200, 4000),
    }
SPEED = {}
     
for state in states:
    if state in defaultSpeed:
        d = defaultSpeed[state]
        if len(d) == 2:
            rate = (d[1]/d[0])**0.25
            
            SPEED[state] = (d[0], int(d[0]*rate), int(d[0]*rate*rate),
                            int(d[0]*rate*rate*rate), d[1])
        elif len(d) == 5:
            SPEED[state] = defaultSpeed[state][:]
        else:
            print('no valid speeds for: %s'% state) 

defaultMousePixels = 1
waitingSpeed = 500
defaultSpeed = 500
minSpeed = 50
# For caret movement, this is the rate change applied when you make it
# faster.  For example, 1.5 is a 50% speed increase.

moveRateChange = 2.0
fastSlowChange = 3.0 
veryChange = 3.0

Counts = ['1','2','3','4','5','6','7','8','9','10','11','12','13',
          '14','15','16','17','18','19','20','25','30','35','40']
 
# flag for displaying all results through the DisplayMessage function
# gives an error in the English version when saying "wait", change therefore
# in "hold on"
showAll = 1

language = unimacroutils.getLanguage()        
normalSet = ['startMoving', 'startMousing', 'startRepeating', 'startSearching']
############################################################################
#
# Here are some of our instisnce variables
#
#   self.inTimer   set when the timer callback in installed
#   self.curSpeed       current movement speed (milliseconds for timer)
#

ancestor = natbj.IniGrammar
class ThisGrammar(ancestor):
    # when we unload the grammar, we must make sure we clear the timer
    # callback so we keep a variable which is set when we currently own
    # the timer callback

    def __init__(self):
        
        self.inTimer = 0
        self.iconState = 0
        self.state = ''
        self.inside = 0
        self.insideCommand = 0
        self.waiting = 0
        self.drag = 0
        ancestor.__init__(self)

    def unload(self):
        if self.inTimer:
            self.cancelMode()
        ancestor.unload(self)

    # This is our grammar.  The rule 'start' is what is normally active.  The
    # rules 'moving' and 'mousing' are used when we are in caret or
    # mouse movement mode.
    name = 'repeat'
    iniIgnoreGrammarLists = ['mouseCount', 'moveCount'] # are set in this module

    if language == 'nld':
        name = 'herhaal'
        gramSpec = """
# these rules are active when we are moving, mousing or repeating:
<moving> exported = (<changeMoving>|<speed>|<moveDir>|<reverse>|
                          <acceleration>|<moveCount>)+ [<endMoving>] |
                     <endMoving>;
<mousing> exported = (<changeMousing>|<speed>|<mouseDir>|<reverse>|
                          <acceleration>|<mouseCount>)+ [<endMousing>] |
                      <endMousing>;
<searching> exported = (<changeSearching>|<speed>|<searchDir>|<reverse>|
                          <acceleration>|<moveCount>)+ [<endSearching>] |
                      <endSearching>;
<repeating> exported = <changeRepeating>;


# here are the rules controlling speeds etc. (inside the timer)        
<changeMoving> = beweeg|selecteer|blok|'ga verder'|'ga door'|'verder'|
                    (begin|einde)[van](regel|document);
<changeMousing> = muis|sleep|'ga verder'|'ga door'|'verder' ;
<changeRepeating> = dummy;
<changeSearching> =  beweeg|selecteer|blok|zoek|'zoek verder'|'ga verder'|'ga door'|'verder';


<endMoving> = stop [bewegen|selecteren|beweeg|blok|selecteer]| OK | wacht | okee;
<endMousing> = stop [muis|muizen|sleep|slepen]| OK | wacht | okee | klik | 'dubbel klik';
<endSearching> = stop [zoek|zoeken]| OK | wacht | okee;
<endRepeating> = stop [herhaal|herhalen] | OK | wacht | okee;

<reverse> = [ga] terug;
<acceleration> = [[heel]veel] (sneller| langzamer);
<speed> = [[heel] erg] (snel|langzaam) | normaal| gestaag;
<moveDir> = [pagina|alinea|regel] (omhoog|omlaag) |
              [woord] (links|rechts);
<moveCount> = {moveCount};
<mouseDir> = omhoog | omlaag |links | rechts;
<searchDir> = omhoog | omlaag | verder | terug;
<mouseCount> = {mouseCount}[stappen|sprongen|pixels|stap|sprong|pixel];
# here are the subrules which deal with caret movement
<startMoving> exported = (BEWEEG|BLOK|SCROLL) (<speed>|<moveDir>|<moveCount>)+;
<startMousing> exported = MUIS (BEWEEG|SLEEP)
                                [<speed>|<mouseDir>|<mouseCount>]+;
<startRepeating> exported = Herhaal dat <speed>;
<startSearching> exported = Zoek continu [<searchDir>|<speed>|<moveCount>]+;
        """
    else:
        # non Dutch:
        gramSpec = """
# these rules  are active when we are moving, mousing or repeating:
<moving> exported = (<changeMoving>|<speed>|<moveDir>|<reverse>|
                          <acceleration>|<moveCount>)+ [<endMoving>] |
                     <endMoving>;
<mousing> exported = (<changeMousing>|<speed>|<mouseDir>|<reverse>|
                          <acceleration>|<mouseCount>)+ [<endMousing>] |
                      <endMousing>;
<searching> exported = (<changeSearching>|<speed>|<searchDir>|<reverse>|
                          <acceleration>|<moveCount>)+ [<endSearching>] |
                      <endSearching>;
<repeating> exported = <changeRepeating>;

# here are the rules controlling speeds etc. (inside the timer)        
<changeMoving> = move|select|'go on'|(begin|end)[of](line|document);
<changeMousing> =  move|drag|'go on'|continue;
<changeSearching> =  move|select|search|'go on'|continue;
<changeRepeating> = dummy;

<endMoving> = stop [moving]| OK | 'hold on' | 'hold it';
<endMousing> = stop [mousing]| OK | 'hold on' | 'hold it' | click | 'double click';
<endSearching> = stop [searching]| OK | 'hold on' | 'hold it'|cancel;
<endRepeating> = stop [repeating|repeat] | OK | 'hold on' | 'hold it'|cancel;

<reverse> = reverse [direction] | [go] back;
<acceleration> = [much] (faster | slower);
<speed> = [very] (fast|slow) | normal | steady;
<moveDir> = [page|paragraph|line] (up | down) |
              [word] (left | right);
<moveCount> = {moveCount};
<mouseDir> = up | down |left | right;
<mouseCount> = {mouseCount};
<searchDir> = forward | back | up | down;
# here are the subrules which deal with caret movement
<startMoving> exported = Start (Moving|Selecting|Scrolling)
                               [<speed>|<moveDir>|<moveCount>]+;
<startMousing> exported = MOUSE (MOVE|DRAG|'Start Moving'|'Start Dragging')
                                [<speed>|<mouseDir>|<mouseCount>]+;
<startRepeating> exported = Repeat That <speed>;
<startSearching> exported = Search continue [<searchDir>|<speed>|<moveCount>]+;
        """

    def initialize(self):
        debugPrint('init language: %s' % language)
        self.load(self.gramSpec, allResults = 1)
        self.activateSet(normalSet, exclusive=0)
        #self.setList('count', Counts)
        self.setList('moveCount', Counts)
        self.setList('mouseCount', Counts)
        self.nPhrase = 1
        self.nTimes = 1
        self.state = ''
        self.inside = 0
        self.insideCommand = 0
        self.waiting = 0
        self.cancelMode()
        self.curDir = ''
        self.curSpeed = 0
        self. mouseSteps = 10
        self. mouseJumps = 10

        self.prevHandle = 0
        self.startScroll = 0
        debugPrint('end of initialise')
            
    # This subroutine cancels any active movement mode

    def cancelMode(self):
        debugPrint('cancelMode')
        natlink.setTrayIcon()

        if self.inTimer: 
            natlinktimer.setTimerCallback(self.onTimer,0)
            self.inTimer = 0
            if self.drag:
                debugPrint('switch of dragging')
                xPos,yPos = natlink.getCursorPos()
                if self.drag == 2:
                    natlink.playEvents([(natlinkutils.wm_rbuttonup,xPos,yPos)])
                else:
                    natlink.playEvents([(natlinkutils.wm_lbuttonup,xPos,yPos)])
                self.drag = 0
            elif self.state == 'searching':
                self.stopSearch()

        self.state = ''
        self.minorState = ''
        self.curDir = ''
        self.Count = 0
        self. mouseSteps = 10
        self.inside = 0
        self.insideCommand = 0
        self.waiting = 0
        self.drag = 0
        self.repeatFlag = 0
        self.hadRepeat = 0
        self.repeatStuff = None
        self.lastResults = []
        self.activateSet(normalSet, exclusive=0)
        
    resetExclusiveMode = cancelMode

##    def waitMode(self):
##        if self.waiting:
##            debugPrint('in timer, already waiting')
##            return
##        self.waiting = 1
##        natlink.setTimerCallback(self.onTimer, waitingSpeed)
##        
##    def resumeMode(self):
##        if not self.waiting:
##            debugPrint('resume, was not waiting!')
##            return
##        self.waiting = 0
##        self.startNow()g
##
    def onTimer(self):
##        if self.lastClock:
##            diff = int((time.clock() - self.lastClock) * 1000 )
        if natbj.IsDisplayingMessage:
            debugPrint('in timer, displaying message, returning')
            return
        moduleInfo = natlink.getCurrentModule()
        if natlink.getMicState() == 'on' and moduleInfo[2] == self.moduleInfo[2]:
            if self.inside or self.insideCommand:
                self.setTrayIcon(1)
                return
            elif self.waiting:
                self.setTrayIcon(1) 
                return
            elif self.doAction():
                return   # this is the only good exit from onTimer!!!!
        self.cancelMode()

    def startNow(self):
        self.moduleInfo = natlink.getCurrentModule()
        k = self.state + self.minorState
        s = self.curSpeed + 2  # very slow =2 -->> 0
        if self.waiting:
            natlinktimer.setTimerCallback(self.onTimer, waitingSpeed)
        elif k == 'mousing' or self.state == 'dragging':
            speed = SPEED[k][s]
            steps = defaultMousePixels
            print('mousing/dragging, speed: %s, steps: %s'% (speed, steps)) 
            if s < minSpeed:
                steps = (minSpeed//speed) + 1
                speed = steps*speed
                if steps < defaultMousePixels:
                    steps = defaultMousePixels
                    speed = speed*defaultMousePixels/steps
                    print('enlarge steps: %s, new speed: %s'% (steps, speed))
            else:
                speed = s
            debugPrint('mouse starting with speed: %s, steps: %s'% (speed, steps))
            natlinktimer.setTimerCallback(self.onTimer, speed)
            self.mouseSteps = steps
        elif k in SPEED:
            debugPrint('starting with speed: %s'% SPEED[k][s])
            natlinktimer.setTimerCallback(self.onTimer, SPEED[k][s], debug=1)
        else:
            debugPrint("timer starting with unknown speed for state/minorstate: %s"%k)
            natlinktimer.setTimerCallback(self.onTimer, defaultSpeed)
            
        self.inTimer = 1
        
    def doAction(self):
##         debugPrint('start doAction state: %s, dir: %s, count: %s'% \
##                   (self.state, self.curDir, self.Count))
        if self.state in ['moving', 'selecting','searching']:
            if not self.curDir:
                debugPrint('do action, no direction specified')
                return
            key = 'ext' + self.curDir
            if self.minorState == 'page':
                if self.curDir == 'down':
                    key = 'extpgdn'
                elif self.curDir == 'up':
                    key = 'extpgup'
                else:
                    debugPrint('invalid direction for minorState page: %s' % self.curDir)
            elif self.minorState in ['word', 'paragraph'] :
                key = 'ctrl+' + key

            if self.waiting and self.Count:
                nowCount = " " + repr(self.Count)
            else:
                nowCount = ""
                
        if self.state == 'moving':
            if self.startScroll:
                keyBefore = ''                
                if self.curDir == 'up': keyBefore = 'extpgup'
                elif self.curDir == 'down': keyBefore = 'extpgdn'
                elif self.curDir == 'left': keyBefore = 'ctrl+extpgdn'
                elif self.curDir == 'right': keyBefore = 'ctrl+extpgup'
                else:
                    debugPrint('invalid direction in scrollcommand: %s'% self.curDir)
                if keyBefore:
                    natlinkutils.playString("{"+keyBefore+"}")
                self.startScroll = 0
            self.setTrayIcon(1)
            natlinkutils.playString("{"+key+nowCount+"}")
        
        elif self.state == 'selecting':
            self.setTrayIcon(1)
            natlinkutils.playString("{shift+"+key+nowCount+"}")
        elif self.state == 'repeating':
            self.setTrayIcon(1)
            self.repeatNow()
        elif self.state == 'searching':
            self.setTrayIcon(1)
            if not self.curDir:
                print('searching, no current direction: %s, assume down'% self.curDir)
                self.curDir = self.getLastSearchDirection() or 'down'
            self.insideCommand = 1
            count = self.Count or 1
            for i in range(count):
                res = self.searchForText(self.curDir)
                self.curDir = self.getLastSearchDirection()
                if res == -2:
                    # missing search, did cancel mode
                    return
            unimacroutils.visibleWait()
            self.insideCommand = 0
        elif self.state == 'mousing':
            self.setTrayIcon(1)
            if self.Count:
                self.moveMouse(self.curDir, self.Count*self.mouseJumps)
            else:
                self.moveMouse(self.curDir, self.mouseSteps)
        elif self.state == 'dragging':
            self.setTrayIcon(1)
            if self.Count:
                self.moveMouse(self.curDir, self.Count*self.mouseJumps)
            else:
                self.moveMouse(self.curDir, self.mouseSteps)
        else:
            return

        self.lastClock = time.time()
        return 1 # good exit

    def gotBegin(self,moduleInfo):
        if natbj.IsDisplayingMessage:
            debugPrint('displaying message, ignoring generic movement')
            return
        if self.inTimer:
            self.inside = 1
 
    def gotResultsObject(self,recogType,resObj):
        if natbj.IsDisplayingMessage:
            debugPrint('displaying message, ignoring generic movement')
            return

        if recogType == 'reject':
            return
        handle = natlink.getCurrentModule()[2]
        if handle != self.prevHandle:
            # new window, empty lastResults list:
            self.lastResults = []
            self.prevHandle = handle
            self.repeatFlag = 0
        words = resObj.getWords(0)[:]
        if recogType == 'other':
            #print 'resultObject, %s,  repeatFlag: %s' % (words, self.repeatFlag)
            if self.repeatFlag:
                if words != self.repeatStuff:
                    self.cancelMode()
            elif self.inTimer:
                self.cancelMode()
            elif natlink.getCallbackDepth() < 3:
                if self.lastResults and words == self.lastResults[-1]:
                    pass
                else:
                    self.lastResults.append(words)
                    if len(self.lastResults) > 6:
                        self.lastResults = self.lastResults[1:]
                #debugPrint('lastResults: %s' % `self.lastResults`)
            else:
                debugPrint('callbackdepth %s, words: %s'%(natlink.getCallbackDepth(), words))
            self.inside = 0
            return
##        skipped this, because it interferes with _message:
##        elif recogType == 'reject':
##            if self.inTimer and self.missed:
##                self.doAction()
##                self.startNow()
        elif recogType == 'self':
            self.nDir = ''
            self.Count = 0
            self.nSpeed = None
            self.dirState = ''
            debugPrint('---starting phrase')
            debugPrint('callbackdepth %s, words: %s'%(natlink.getCallbackDepth(), words))
            if showAll:
                self.DisplayMessage('<%s>'% ' '.join(words))
        else:
            print('recogtype: %s'% recogType)
        self.inside = 0
            
    def gotResults_reverse(self,words,fullResults):
        debugPrint('reverse: %s'%repr(words))
        if self.nDir:
            self.flush()
        d = self.curDir
        if d == 'up': d = 'down'
        elif d == 'down': d = 'up'
        elif d == 'right': d = 'left'
        elif d == 'left': d = 'right'
        if d:
            self.nDir = d
            self.dirState = self.minorState

    def gotResults_moveCount(self,words,fullResults):
        for w in words:
            if self.Count: self.flush()
            debugPrint('moveCount: %s'%w)
            self.Count = int(w)

    def gotResults_mouseCount(self,words,fullResults):
        if self.Count: self.flush()
        for w in words:
            debugPrint('mouseCount: %s'%w)
            if w in Counts:
                self.Count = int(w)
            elif self.hasCommon(w, ('pixel', 'pixels')):
                self.mouseJumps = 1
                self.flush()
            elif self.hasCommon(w, ('stap', 'stappen')):
                self.mouseJumps = 10
                self.flush()
            elif self.hasCommon(w, ('sprong', 'sprongen.')):
                self.mouseJumps = 100
                self.flush()

        
    def gotResults_moveDir(self,words,fullResults):
        for w in words:
            debugPrint('direction: %s'% w)
            if self.nDir:
                self.flush()
            d = ''
            if w in ['pagina', 'page']: self.dirState = 'page'
            elif w in ['alinea', 'paragraph']: self.dirState = 'paragraph'
            elif w in ['word', 'woord']: self.dirState = 'word'
            elif w in ['up', 'omhoog']: d = 'up'
            elif w in ['down', 'omlaag']: d = 'down'
            elif w in ['right', 'rechts']: d = 'right'
            elif w in ['left', 'links']: d = 'left'
            if d:
                self.nDir = d

    def gotResults_searchDir(self,words,fullResults):
        for w in words:
            debugPrint('direction: %s'% w)
            if self.nDir:
                self.flush()
            d = ''
            if w in ['omhoog', 'terug', 'back', 'up']: d = 'up'
            elif w in ['forward', 'omlaag', 'verder', 'down']: d = 'down'
            if d:
                self.nDir = d

    def gotResults_mouseDir(self,words,fullResults):
        for w in words:
            debugPrint('mouseDir: %s'% w)
            if   w in ['up', 'omhoog']: d = 'up'
            elif w in ['down', 'omlaag']: d = 'down'
            elif w in ['right', 'rechts']: d = 'right'
            elif w in ['left', 'links']: d = 'left'
            else:
                print('invalid direction:', w)
                return
            if d != self.curDir:
                self.curDir = d
                self.minorState = ''
            newState = self.minorState
            # to be filled in!
            if newState != self.minorState:
                self.minorState = newState

    def gotResults_endMoving(self,words,fullResults):
        if self.nDir or self.Count or self.nSpeed != None:
            self.flush()
        debugPrint('end moving: %s'% repr(words))
        for w in words:
            if w in ['hold','hold on', 'hold it', 'wacht']:
                self.waiting =  1
                debugPrint('waiting mode')
                return
            else:
                self.cancelMode()

    def gotResults_endMousing(self,words,fullResults):
        if self.nDir or self.Count or self.nSpeed != None:
            self.flush()
        debugPrint('end mousing: %s'% repr(words))
        for w in words:
            if w in ['hold','hold on', 'hold it', 'wacht']:
                self.waiting =  1
                debugPrint('waiting mode')
                return
            else:
                self.cancelMode()
            if self.hasCommon(words, ['click', 'klik']):
                natlinkutils.buttonClick()
            elif self.hasCommon(words, ['double click', 'dubbel klik']):
                natlinkutils.buttonClick('left', 2)

    def gotResults_endSearching(self,words,fullResults):
        if self.nDir or self.Count or self.nSpeed != None:
            self.flush()
        debugPrint('end searching: %s'% repr(words))
        for w in words:
            if w in ['hold','hold on', 'hold it', 'wacht']:
                self.waiting =  1
                debugPrint('waiting mode')
                return
            else:
                self.cancelMode()
                if self.hasCommon(words, ['cancel', 'annuleren']):
                    self.searchGoBack()
                    

    def gotResults_endRepeating(self,words,fullResults):
        if self.nDir or self.Count or self.nSpeed != None:
            self.flush()
        debugPrint('end repeating: %s'% repr(words))
        for w in words:
            if w in ['hold','hold on', 'hold it', 'wacht']:
                self.waiting =  1
                debugPrint('waiting mode')
                return
            else:
                self.cancelMode()


    def gotResults_changeMoving(self,words,fullResults):
        if self.nDir or self.Count or self.nSpeed != None:
            self.flush()
        b = r = ''
        for w in words:
            if b and r:
                natlinkutils.playString("{"+r+b+"}")
                b = r = ''
            if w in ['go on', 'ga door', 'ga verder', 'verder']:
                debugPrint('going on')
                self.waiting = 0
            elif w in ['move', 'beweeg']:
                if self.state != 'selecting':
                    self.state = 'moving'
                self.waiting = 0
            elif w in ['select','selecteer']:
                self.state = 'selecting'
                self.waiting = 0
            elif w in ['begin']:
                b = 'Home'
            elif w in ['einde','end']:
                b = 'End'
            elif w in ['line', 'regel']:
                r = 'ext'
            elif w in ['document']:
                r = 'ctrl+ext'
        if b and r:
            natlinkutils.playString("{"+r+b+"}")
            b = r = ''
            
    def gotResults_changeSearching(self,words,fullResults):
        if self.nDir or self.Count or self.nSpeed != None:
            self.flush()
        for w in words:
            if w in ['go on', 'ga door', 'ga verder', 'verder', 'continue']:
                debugPrint('going on')
                self.waiting = 0
            elif w in ['zoek', 'search']:
                continue
            elif w in ['move', 'beweeg']:
                debugPrint('change to state moving')  
                self.activateSet(['moving'], exclusive = 1)
                self.state = 'moving'

    def gotResults_changeMousing(self,words,fullResults):
        if self.nDir or self.Count or self.nSpeed != None:
            self.flush()
        for w in words:
            if w in ['go on', 'ga door', 'ga verder', 'verder', 'continue']:
                debugPrint('going on')
                self.waiting = 0
            

    def gotResults_speed(self,words,fullResults):
        if self.Count:
            self.flush()
            
        factor = 1

        for w in words:
            if w in ['heel', 'erg', 'very']:
                factor = factor * 2
            elif w in ['slow', 'langzaam']:
                self.nSpeed = factor 
            elif w in ['fast', 'snel']:
                self.nSpeed = -factor 
            elif w in ['normal', 'normaal', 'steady', 'gestaag']:
                self.nSpeed = 0
            else:
                print('speed, invalid keyword:', w)
        self.nSpeed = max(min(self.nSpeed, 2), -2)
        debugPrint ('speed words: %s, speed: %s' % (repr(words), self.nSpeed))


    def gotResults_acceleration(self,words,fullResults):
        if self.Count:
            self.flush()
        factor = 1
        self.nSpeed = self.curSpeed        
        for w in words:
            if w in ['much', 'veel', 'very', 'heel']:
                factor = factor * 2
            elif w in ['slower', 'langzamer']:
                diff =  factor
            elif w in ['faster', 'sneller']:
                diff = -factor
            else:
                print('acceleration, invalid keyword:', w)
                debugPrint ('acceleration, invalid keyword: %s'% w)
        self.nSpeed = self.nSpeed + diff
        self.nSpeed = max(min(self.nSpeed, 2), -2)
        debugPrint ('acceleration words: %s, new speed: %s' % (repr(words), self.nSpeed))

    def gotResults_startMoving(self,words,fullResults):
        self.activateSet(['moving'], exclusive = 1)
        if self.hasCommon(words, ['BEWEEG', 'Moving']):
            self.state = 'moving'
        elif self.hasCommon(words, ['BLOK', 'Selecting']):
            self.state = 'selecting'
        elif self.hasCommon(words, ['Scrolling', "SCROLL"]):
            self.startScroll = 1 
            self.state = 'moving'

    def gotResults_startSearching(self,words,fullResults):
        self.activateSet(['searching'], exclusive = 1)
        self.curDir = self.getLastSearchDirection()
        self.state = 'searching'
        

    def gotResults_startMousing(self,words,fullResults):
        self.activateSet(['mousing'], exclusive = 1)
        debugPrint('start mousing %s' % repr(words))
        if self.hasCommon(words, ["MUIS",'MOUSE']):
            self.state = 'mousing'
        if self.hasCommon(words, ["SLEEP",'DRAG']):
            self.state = 'dragging'
            xPos,yPos = natlink.getCursorPos()
            if self.hasCommon(words, ["SNELMENU",'RIGHT']):
                self.drag = 2
                natlink.playEvents([(natlinkutils.wm_rbuttondown,xPos,yPos)])
            else:
                self.drag = 1
                natlink.playEvents([(natlinkutils.wm_lbuttondown,xPos,yPos)])

    def gotResults_startRepeating(self,words,fullResults):
        self.state = 'repeating'


    def gotResults_test(self,words,fullResults):
        self.cancelMode()
        print('words in test', words)
        natlink.recognitionMimic(words)

        
    def gotResults_nfrase(self,words,fullResults):
        self.nPhrase = int(words[0])
            
    def gotResults_repeat(self,words,fullResults):
        if words[0] in ['Herhaal', 'Repeat']:
            self.nPhrase = 1
            self.nTimes = 1
        self.hadRepeat = 1

##    def gotResults_again(self,words,fullResults):
##        global hadRepeatGrammar 
##        nAgain = len(words)/2in 3
##        self.hadResult = 1
##        repeatFlag = 1
##        for i in range(nAgain):
##            RepeatNow(nPhrase, nTimes)
##            hadRepeatGrammar = 1
##            if not repeatFlag:
##                return None
            
    def gotResults_count(self,words,fullResults):
        self.nTimes = int(words[0])

    def startAgain(self):
        self.activateSet(['start','again'])

    def gotResults(self,words,fullResults):
        if self.repeatFlag:
            return
        if self.hadRepeat:
            debugPrint('gotResults, hadRepeat aan')
            self.repeatNow()
            self.hadRepeat = 0
            return
        if self.Count or self.nSpeed != None or self.nDir:
            self.flush()
        if self.state in states:
            self.startNow()
        debugPrint ('end of phrase (gotResults): %s'% repr(words))
        self.inside = 0 

    def flush(self):
        debugPrint('flush, nDir: %s, Count: %s, nSpeed: %s'%
                   (self.nDir, self.Count, self.nSpeed))
        if self.nDir:
            self.curDir = self.nDir
            self.nDir = ''
            self.minorState = self.dirState
            self.dirState = ''
        if self.Count:
            self.waiting = 1
            self.doAction()
            self.Count = 0
            return

        if self.nSpeed != None:
            self.curSpeed = self.nSpeed
            self.nSpeed = None
        self.waiting = 0
        self.doAction()
        

    def moveMouse(self,direction,count):
        xPos,yPos = natlink.getCursorPos()
        if direction == 'up': yPos = yPos - count
        elif direction == 'down': yPos = yPos + count
        elif direction == 'left': xPos = xPos - count
        elif direction == 'right': xPos = xPos + count
        xSize,ySize = natlink.getScreenSize()
        if xPos < 0: xPos = 0
        if xPos >= xSize: xPos = xSize - 1
        if yPos < 0: yPos = 0
        if yPos >= ySize: yPos = ySize - 1
        natlink.playEvents([(natlinkutils.wm_mousemove,xPos,yPos)])


    # This turns on the tray icon depending on the movement direction.
    # self.iconS tate is used to toggle the image to animate the icon.            
    def setTrayIcon(self,toggleIcon):
        if self.state in ['moving', 'selecting', 'mousing','dragging', 'searching']:
            iconName = self.curDir
            toolTip = self.state + ' ' +self.curDir
        elif self.state == 'repeating':
            toolTip = 'repeating commands'
            iconName = os.path.join(iconDirectory, 'repeat')
        else:
            natlink.setTrayIcon()
            print('setTrayIcon, invalid state:', self.state)
            return

        if self.waiting:
            toolTip = 'WAITING'
        
        if not toggleIcon or self.iconState:
            self.iconState = 0
        else:
            self.iconState = 1
            if self.waiting:
                iconName = os.path.join(iconDirectory, 'waiting')
            else:
                iconName = iconName + '2'

##        print 'iconName: %s'% iconName
        try:            
            if iconName[1] == ':':
                # absolute path, attach extension:
                iconName = iconName + '.ico'
        except IndexError:
            print('cannot set tray icon, no iconName (_repeat), try to clear')
            natlink.setTrayIcon()
        try:
            natlink.setTrayIcon(iconName,toolTip,self.onTrayIcon)
        except natlink.NatError:
            print('cannot set tray icon (_repeat), try to clear')
            natlink.setTrayIcon()
                    

    # This is called if the user clicks on the tray icon.  We simply cancel
    # movement in all cases.
## taken from GrammarX:
##    def onTrayIcon(self,message):
##        natlink.setTrayIcon()
##        self.cancelMode()

    def repeatNow(self):
        debugPrint('repeatNow: %s times, %s phrases' % (self.nTimes, self.nPhrase))
        # put repeat mode ON:
        self.repeatFlag = 1
        itemrange = list(range(len(self.lastResults)))
        if not itemrange:
            self.repeatFlag = 0
            return None
        itemrange = itemrange[-self.nPhrase:]
        #print 'na itemrange:', itemrange
        for n in range(self.nTimes):
            for i in itemrange:
                if not self.repeatFlag:
                    return None  # if something else happened
                self.repeatStuff= self.lastResults[i]
                natlink.recognitionMimic(self.repeatStuff)                
            # reset repeat mode:
        self.repeatFlag = 0
        self.repeatStuff = None
# This is a simple utility subroutine.  It takes two lists of words and 
# returns the first word it finds which is in both lists.  We use this to
# extract special words (like the direction) from recognition results.

def findKeyWord(list1,list2):
    for word in list1:
        if word in list2: 
            return word
    return None

startTime = time.time()
if DEBUG:
    fOutName = 'c:\\DEBUG '+__name__+'.txt'
    debugFile = open(fOutName, 'w')
    print('DEBUG uitvoer naar: %s'% fOutName)

def debugPrint(t):
    if not DEBUG: return
    print('_gm: %s'% t)
    if type(t) == bytes:
        debugFile.write(t)
    else:
        debugFile.write(repr(t))
    debugFile.write('\n')
    debugFile.flush()


iconDirectory = os.path.join(unimacroutils.getUnimacroDirectory(), 'icons')
if not os.path.isdir(iconDirectory):
    raise Exception('icon folder not present (for repeat and waiting icon): %s'% iconDirectory)

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
        thisGrammar.cancelMode()

