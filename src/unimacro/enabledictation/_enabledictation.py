# (unimacro - natlink macro wrapper/extensions)))
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
# _enabledictation.py

# make applications select-and-say, by inserting the dictobj class.
# no command grammars are inserted, this was done in the _global_dictation.py project.
# the applications that are "caught" are defined in windowsparameters.py
# currently only the windows messaging trick for checking and changing the foreground control is used.
# 
#  written by: Quintijn Hoogenboom (QH softwaretraining & advies)
#  September 2014
# 
"""make more windows select-and-say

The class needed here is the VoiceDictation class, which intercepts the
VDct of NatSpeak,

When speech starts, the onTextBegin of the dictobj instance (of VoiceDictation)
which is self.dictobj is called.

The callback function onTextChange is called when dictation has been recognised (of self.dictobj)

inside the VoiceDictation instance there is self.dictObj, which is the link to
the (intercepted) dictation object.

"""
import win32api
import win32gui
import win32con
import time
import os
import sys
import types
import re
#print 'sys.path: %s'% sys.path
import unimacro.messagefunctions as mess
import windowparameters

defaultWaitTime = 0.2  # change to slow down or speed up actions.

import natlink
from dtactions.unimacro.unimacroactions import doAction as action
from dtactions.unimacro.unimacroactions import doAction as action

from natlinkcore import natlinkutils
from dtactions.unimacro import unimacroutils
from dtactions.unimacro import unimacroutils
import unimacro.natlinkutilsbj as natbj

from time import sleep  

class VoiceDictation:
    dictObj = None  # is going to hold the internal dictObj (from natlink)
    #ctrl = None
    # Initialization.  Create a DictObj instance 
    # activate if outside the special text window

    def initialize(self):
        if self.dictObj != None:
            D("dictObj already initialized")
            return
        self.__class__.dictObj = natlink.DictObj()
        #self.__class__.app = None
        #self.__class__.ctrl = None  # to be filled in getEditControl
        self.dictObj.setBeginCallback(self.onTextBegin)
        self.dictObj.setChangeCallback(self.onTextChange)
        self.WindowsParameters = windowparameters.PROGS
        self.appNames = list(self.WindowsParameters.keys())
        print('_enabledictation tries applications: %s'% self.appNames)
        
        self.activeApp = None
        #self.getEditControl()
        # updated in updateState:
        self.lastSel = (0,0)
        self.lastSelText = ""
        self.prevHndle = None
        self.ctrl = None # hndle of the foreground control inside an application
        self.app = None  # hndle of the current foreground application (from moduleInfo)
        self.dctactive = None


    def onTextBegin(self,moduleInfo):
        """at start of each utterance, like gotBegin for command grammars
        """
        hndle = moduleInfo[2]
        if hndle != self.prevHndle:
            self.prevHndle = hndle
            if self.dctactive:
                dct = self.dictObj
                dct.deactivate()
                self.dctactive = 0
            prog, title, topchild, hndle = unimacroutils.getProgInfo(moduleInfo)
            print('changing app to: "%s", %s'% (prog, hndle))
            self.app, self.ctrl = None, None
            if prog in self.WindowsParameters:
                self.getEditControl(prog, hndle)
                if self.ctrl:
                    print('got edit control for "%s": %s'% (prog, self.ctrl))
                    self.app = prog
                else:
                    print('no edit control found for "%s"'% prog)
        if self.ctrl is None:
            return
        if not self.dctactive:
            dct = self.dictObj
            print('activate dictObj to %s'% self.ctrl)
            dct.activate(self.ctrl)
            self.dctactive = 1
            
        self.updateState()
        #            
        #            
        #    
        #if self.activeApp is None:
        #    return
        #
        #
        #dct = self.dictobj
        #dct.getEditControl() # also notices when app has been killed.
        #
        #if self.prevHndle == hndle:
        #    if dct.app and not dct.hasFocus:
        #        dct.updateState()
        #    return   # no change
        #if modInfo[1] == "Spell":
        #    #print "Spell window"
        #    return
        #self.prevHndle = hndle
        #dct.saveFocus() # loosing the focus...
        ## focus changed, so hasFocus state can be changed:
        #if not dct.app:
        #    print 'no dictation application ready: %s'% dct.app
        #    dct.dictObj.deactivate()
        #    self.activateSet(self.outsidefocusrules)
        #    return
        #dct.updateState()
        #hndle = win32gui.GetForegroundWindow()
        #if dct.app == hndle:
        #    if dct.hasFocus != 1:
        #        self.activateSet(self.alwaysrules, exclusive=0)
        #        dct.hasFocus = 1
        #        print 'got focus'
        #        dct.dictObj.deactivate()
        #else:
        #    if dct.hasFocus != 0:
        #        # lost focus now:
        #        print "loosing focus"
        #        self.activateSet(self.outsidefocusrules)
        #        dct.hasFocus = 0
        #        dct.dictObj.activate(0)
        #
        #pass  # gets controlled from CmdsGrammar.gotBegin!
        ##if not self.app:
        ##    self.getEditControl()
        ##if not self.app:
        ##    return
        ###D('win dict, text begin')
        ##self.updateState()

    def getEditControl(self, prog, appHndle):
        """get the control (self.ctrl) of the text window in the foreground
        
        prog = name of application (to be defined in self.WindowsParameters)
        appHndle = hndle of the application
        """
        # get application, if not found, set ctrl to None
        currentSel = None
        if self.ctrl:
            currentSel = mess.getSelection(self.ctrl)
        if currentSel and currentSel != (0,0):
            return
        
        # get controls via messages functions, elaborate here if we need client-server trick:
        W = self.WindowsParameters[prog]
        # test case with fixed handle, set in windowparameters.py:
        if W["controlhandle"]:
            self.ctrl = W["controlhandle"]
            return




        wantedText, wantedClass, selectionFunction = W["edittext"], W["editcontrol"], W["selectionfunction"]
        print('wantedText: "%s", wantedClass: "%s", selectionFunction: %s'% (wantedText, wantedClass, selectionFunction))
        ctrls =  mess.findControls(appHndle, wantedText, wantedClass, selectionFunction) # pass the relevant windows parameters, as dict
        print('ctrls for "%s": %s'% (prog, ctrls))
        # some special triggering in a difficult case:
        if ctrls:
            editHndle = ctrls[0]
            self.ctrl = editHndle
        else:
            self.ctrl = None
            

    def wait(self, waitTime=None):
        waitTime = waitTime or defaultWaitTime
        time.sleep(waitTime)
        

    def onTextChange(self,delStart,delEnd,newText,selStart,selEnd):
        D('onTextChange: %s, %s, |%s|, %s, %s'% ( delStart, delEnd, repr(newText), selStart, selEnd) )
        
        if not self.ctrl:
            D("do not have ctrl control")
            return
        print('onTextChange for %s'% self.ctrl)
        dct = self.dictObj
        dct.setLock(1)
        getFocus = (selEnd - selStart > 1) # at start of call
        if newText:
            if self.lastSel == (delStart, delEnd):    
                dct.setText(self.lastSelText, delStart, selEnd)  # empty now
            else:
                print('window changed, update again')
                self.updateState()
            self.insertText(delStart, delEnd, newText)


        else:
            # loosing scratch that info:
            self.scratchinfo = []
            if delStart < delEnd:
                print('selection to delete: %s, %s'% (delStart, delEnd))
            if selStart < selEnd:
                self.setSelection(selStart,selEnd) # only set the window...
            else:
                self.insertText(selStart, selEnd, newText)
                
                #selStart, selEnd, newText = self.adjustAtEndOfText(selStart, selEnd, "")
                #if newText:
                #else:
                #    self.setSelection(selStart,selEnd) # only set the window...
                    
        dct.setLock(0)
       

    def insertText(self, delStart, delEnd, newText):
        # adjust at start:
        dct = self.dictObj
        newText = newText.replace('\n', '')                         
        delStart, newText = self.adjustAtStartOfText(delStart, newText)
        # make visible cursor of 1 space at the end
        selStart = delStart + len(newText)
        selStart, selEnd, newText = self.adjustAtEndOfText(selStart, delEnd, newText)
        # now go in internal buffer:
        dct.setText(newText, delStart, delEnd)
        dct.setTextSel(selStart, selEnd)

        # now the window buffer (through mess functions):                
        D("setting: |%s| to pos %s, %s"% (newText, delStart, delEnd))
        self.setSelection(delStart, delEnd)
        self.replaceSelection(newText)
        D("setting selection to pos %s, %s"% (selStart, selEnd))
        self.setSelection(selStart,selEnd)
        #if getFocus:
        #    unimacroutils.SetForegroundWindow(self.app)
        if not self.scratchThatCommand:
            self.scratchinfo.append( [(selStart, selEnd), newText,
                                  (delStart, delEnd), self.lastSelText])
        
    def correctForNewlines(self, t):
        """change \n into \r\n or \r\n into \n
        depending on self.linesep
        """
        if t.find('\n') == -1:
            return t
        
        if self.linesep == '\n':
            if t.find('\r') >= 0:
                t = t.replace('\r', '')
        elif self.linesep == '\r\n':
            t = t.replace('\n', '\r\n')
            t = t.replace('\r\r\n', '\r\n')
        print('correctedForNewlines: %s'% repr(t))
        return t

    def updateState(self):
        
        print('do updateState for %s'% self.ctrl)
        dct = self.dictObj
        if self.ctrl:
            text = self.getWindowText()
            #text = text.replace('\r', '')   # only \n for internal buffer
            selStart,selEnd = self.getSelection()
            #D("updateState, ctrl: selStart, selEnd: %s, %s"% (selStart, selEnd))
        visStart,visEnd = self.getVisibleRegion()
        print('visStart, visEnd: %s, %s'% (visStart, visEnd))
        if (visStart, visEnd) == (None, None):
            visStart, visEnd = 0, len(text)
        print('visStart, visEnd: %s, %s'% (visStart, visEnd))
        dct.setLock(1)
        dct.setText(text,0,0x7FFFFFFF)
        dct.setTextSel(selStart,selEnd)
        dct.setVisibleText(visStart, visEnd)
        self.lastSel = (selStart, selEnd)
        self.lastSelText = text[selStart:selEnd]
        D("dictObj set with text: %s (visible: %s, %s)"% (len(text), visStart, visEnd))
        D("part of text (10 left from selStart %s, selEnd: %s): |%s|"% (selStart, selEnd, repr(dct.getText(min(0, selStart-10), 0x7FFFFFFF))))
        dct.setLock(0)
            
       
    def getSelection(self):
        """get the selection of the edit control
        
        return a 2 tuple
        """
        return mess.getSelection(self.ctrl)

    def setSelection(self, start, end):
        """change the selection of the edit control
        """
        mess.setSelection(self.ctrl, start, end)

    def getWindowText(self):
        """get the buffer from the edit control
        
        should go smarter in
        """
        #print 'getting buffer'hallo
        tList = mess.getEditText(self.ctrl)
        return ''.join(tList)
        
    def replaceSelection(self, output):
        """overwrite selection with output
        """
        mess.replaceEditText(self.ctrl, output)
 
        
    def getVisibleRegion(self):
        """Utility subroutine which calculates the visible region of the edit

         control and returns the start and end of the current visible region.
        """
        return None, None
        if self.ctrl:
            buf = self.getWindowText()
            return 0, len(buf)
            
            top,bottom,left,right = self.ctrl.GetClientRect()
            firstLine = self.ctrl.GetFirstVisibleLine()
            visStart = self.ctrl.LineIndex(firstLine)

            lineCount = self.ctrl.GetLineCount()
            lastLine = lineCount
            for line in range(firstLine+1,lineCount):
                charInLine = self.ctrl.LineIndex(line)
                left,top = self.ctrl.GetCharPos(charInLine)
                if top >= bottom:
                    break
                lastLine = line

            visEnd = self.ctrl.LineIndex(lastLine+1)
            if visEnd == -1:
                visEnd = len(self.ctrl.GetWindowText())
            return visStart,visEnd
        else:
            return None, None
    
    # Call this function to cleanup.  We have to reset the callback
    # functions or the object will not be freed.
        
    def terminate(self):
        if self.dictObj:
            self.dictObj.deactivate()
            self.dictObj.setBeginCallback(None)
            self.dictObj.setChangeCallback(None)
            self.__class__.dictObj = None
            self.ctrl = None
            self.app = None

  
    def wait(self, waitTime=None):
        """some short time after each command
        
        waits after actions with messagefunctions are in the wrapper functions
        of the VoiceDictation instance
        """
        self.dictobj.wait(waitTime)
        
         
# debug print, only if testMode is o
testMode = 1
def D(t):
    if testMode:
        print(t)

dictationObject = VoiceDictation()
dictationObject.initialize()

#dictationObject = None
def unload():
    if dictationObject:
        dictationObject.terminate()
        dictationObject = None
