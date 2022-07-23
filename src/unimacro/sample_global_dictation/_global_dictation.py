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
# _sample_global_dictation.py

# dictate from any window with result in 1 application
# commands also go through the messaging mechanism, so
# the window is not targeted at all
# 
#  written by: Quintijn Hoogenboom (QH softwaretraining & advies)
#  October 2009-September 2010.
#  This is the "pre version" of the Kaiser Dictation project, in this hospital
#  in Hawai the radiologists use the augmented version of this module for
#  all their reports.
# 
"""universal dictation, targeted to 1 window...

two classes are needed here, the VoiceDictation class, which intercepts the
VDct of NatSpeak,
and the CmdGrammar class, which holds global and application specific commands.

The initialisation of the VoiceDictation instance is done in the CmdGrammar, so
they have a link to each other and there is no need for a special file for the
VoiceDictation class.

When speech starts, the gotBegin of the cmdGrammar is called AND the
onTextBegin of the dictobj instance (of VoiceDictation) which is self.dictobj
inside the cmdGrammar instance.

Likewise the normal callbacks for a command are in the gotResult... functions of
cmdGrammar, and onTextChange is called when dictation has been recognised (of self.dictobj)

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
try:
    # this is a little module for easy changing of test application
    # the file testermod.py (NOT included in svn) holds something like:
    ## different testings of unittestMessagefunctions:
    ##tester = "wordpad"
    ##tester = "dragonpad"
    # one of the lines should be uncommented.
    # testermod is also used by unittestMessagefunctions, which can be used
    # to test the communication with the (off focus) application.
    import testermod
    tester = testermod.tester
except ImportError:
    tester = "aligen"   # this is the window of the Kaiser Permanente application.

import windowparameters

testMode = 1
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
    dictObj = None
    ctrl = None
    # Initialization.  Create a DictObj instance 
    # activate if outside the special text window

    def initialize(self):
        if self.dictObj != None:
            D("dictObj already initialized")
            return
        self.__class__.dictObj = natlink.DictObj()
        self.__class__.app = None
        self.__class__.ctrl = None  # to be filled in getEditControl
        self.dictObj.setBeginCallback(self.onTextBegin)
        self.dictObj.setChangeCallback(self.onTextChange)
        # copy the W variables, taken from "windowparameters.py"
        W = windowparameters.PROGS[tester]
        if W:
            print('get windowsparamters from tester: %s'% tester)
            for k,v in list(W.items()):
                #print 'W: %s: %s'% (k, v)
                setattr(self, k, v)
        else:
            raise ValueError("Cannot get windowsparameters dict for tester: %s"% tester)
        self.getEditControl()
        self.inOnTextChange = 0
        # updated in updateState:
        self.lastSel = (0,0)
        self.lastSelText = ""
        self.scratchinfo = [] # lists of undo info, [(selStart, selEnd), newText, (delStart, delEnd), oldText]
        self.scratchThatCommand = 0
        self.nonFocusHndles = []  # for loosing focus
        self.hasFocus = -1  # is controlled from CmdsGrammar instance

        #self.fieldIsSelected = 0 # only set when a field is extended [x] (first only x after [x])
        
    def getAppWindow(self):
        """get application, try quick if application still exists
        
        if not, try to find (again)
        if cannot be found: try to start (if "shouldstartauto" is on)
        """
        if self.app:
            wtext = win32gui.GetWindowText(self.app)
            if wtext: return # app still active
        self.__class__.app = None # lost the appl
        appWindows = mess.findTopWindows(wantedClass=self.windowclass, wantedText=self.windowcaption)
        if len(appWindows):
            if len(appWindows) > 1:
                print('warning, more appWindows active! %s'% appWindows)
            appHndle = appWindows[0]
            self.__class__.app = appHndle
            return
        
        # not found app:
        if not self.shouldstartauto:
            return
        
        D('starting the application %s'% self.apppath)
        meHndle = win32gui.GetForegroundWindow()
        result = os.startfile(self.apppath)
        if self.testcloseapp:  # quick easy to start app probably
            sleepTime = 0.1
        else:
            sleepTime = 0.5    # maybe a slow starting app
        for iTry in range(20):
            time.sleep(sleepTime)
            appWindows = mess.findTopWindows(wantedClass=self.windowclass, wantedText=self.windowcaption)
            if appWindows: break
        else:
            print('starting %s failed, dumping apps'% self.apppath) 
            pprint.pprint(dumpTopWindows())
            return

        if meHndle:
            # try to get focus back to originating window
            try:
                unimacroutils.SetForegroundWindow(meHndle)
            except: pass
            appHndle = appWindows[0]
        self.__class__.app = appHndle
    
    def getEditControl(self):
        # get application, if not found, set ctrl to None
        self.getAppWindow()
        if not self.app:
            self.__class__.ctrl = None
            return
        currentSel = None
        if self.ctrl:
            currentSel = mess.getSelection(self.ctrl)
        if currentSel and currentSel != (0,0):
            return
        ctrls =  mess.findControls(self.app,wantedClass=self.editcontrol)
        if len(ctrls):
            editHndle = ctrls[0]
            #print 'editHndle set to: %s'% editHndle
            if len(ctrls) > 1:
                for hndle in ctrls:
                    id = win32gui.GetDlgCtrlID(hndle)
                    if id == 0xd6:
                        editHndle = hndle
                        break
                else:
                    print('did not get valid id for aligen window')
                    return
        else:
            raise ValueError("could not find the editHndle of the control: %s in application: %s"%
                          (self.editcontrol, self.apppath))
        self.__class__.ctrl = editHndle

    def wait(self, waitTime=None):
        waitTime = waitTime or defaultWaitTime
        time.sleep(waitTime)

    def saveFocus(self):
        """remember focus of current window, append to focus list
        """
        hndle = win32gui.GetForegroundWindow()
        if hndle == self.app:
            return
        if self.nonFocusHndles and self.nonFocusHndles[-1] == hndle:
            return
        title = win32gui.GetWindowText(hndle).lower()
        if (title.find("notepad") >= 0 or
            title.find("kladblok") >= 0 or
            title.find("outlook") >= 0 or
            title.find("komode") >= 0):
            print('saveWindow, ignore window of title: %s'% title)
            return
        print('adding: %s to list: %s'% (hndle, self.nonFocusHndles))
        self.nonFocusHndles.append(hndle)

    def acquireFocus(self):
        """get focus of special app, return previous handle
        
        if focus was already there, return None
        """
        if not self.app:
            raise Exception('no application for aquiring focus')
        hndle = win32gui.GetForegroundWindow()
        if hndle == self.app:
            return
        self.saveFocus()  # for next occurrence, mostly already done from gotBegin
        unimacroutils.SetForegroundWindow(self.app)
        for i in range(10):
            controlHndle = win32gui.GetForegroundWindow()
            if controlHndle == self.app: return hndle
            time.sleep(0.1)
        raise OSError('could not aquire focus for %s'% self.app)

    def looseFocus(self, hndle=None):
        """return the focus to window with hndle, or saved handle
        """
        controlHndle = win32gui.GetForegroundWindow()
        if hndle and hndle == self.app:
            raise ValueError("hndle to loose focus to IS the application handle: %s"% hndle)
        
        if controlHndle == self.app:
            if hndle and hellonot (self.nonFocusHndles and self.nonFocusHndles[-1] == hndle):
                self.nonFocusHndles.append(hndle)
        else:
            if hndle:
                if hndle == controlHndle:
                    return  # OK
                if not(self.nonFocusHndles and self.nonFocusHndles[-1] == hndle):
                    self.nonFocusHndles.append(hndle)
                    
        print('loosing focus, hndle: %s'% self.app)     
        # now do the work:
        if not self.nonFocusHndles:
            print('cannot loose focus, no stack')
            #if controlHndle == self.app:
            #    action("SSK {alt+tab}")
            #    self.wait(0.3)
            return
        while self.nonFocusHndles:
            hndle = self.nonFocusHndles.pop()
            try:
                print('loosing focus, to:%s (rest: %s)'% (hndle, self.nonFocusHndles))          
                unimacroutils.SetForegroundWindow(hndle)
                self.wait()
                self.nonFocusHndles.append(hndle)
                return
            except:
                print('exception loosing focus to %s, try previous on list'% hndle)
                continue
            raise Exception('could not loose focus an favour of %s'% hndle)
        else:
            if controlHndle == self.app:
                print('cannot loose focus, stack exhausted')
                #action("SSK {alt+tab}")
                #self.wait(0.3)
            
            
    def activateMenuItem(self, menuItem):
        """do menu time through mess
        """
        if not self.app:
            print('activeMenuItem %s, no control active: %s'% (menuItem,self.app))
        menuToDo = getattr(self, menuItem, None)
        if menuToDo:
            mess.activateMenuItem(self.app, menuToDo)
            self.wait()
        else:
            print('no valid menu item in this application: %s'% menuItem)
            
    def sendKey(self, keyOrKeys):
        """send key(s) through messagefunctions to control
        """
        if not self.ctrl:
            print('sendKey %s, no control active: %s'% (menuItem,self.ctrl))
        if keyOrKeys:
            mess.sendKey(self.ctrl, keyOrKeys)
            self.wait()
        else:
            print('sendKey, no keys specified')
    
    def sendEnterKey(self, numTimes=1):
        t = self.aftertext*numTimes
        t = self.correctForNewlines(t)
        delStart, delEnd = self.getSelection()
        selStart = selEnd = delStart + len(t)
        self.onTextChange(delStart,delEnd,t,selStart,selEnd)
        self.updateState()
        
    def onTextBegin(self,moduleInfo):
        """at start of each utterance,
        
        The control of the started application is done from the CmdsGrammar
        in each gotBegin callback.
        """
        pass  # gets controlled from CmdsGrammar.gotBegin!
        #if not self.app:
        #    self.getEditControl()
        #if not self.app:
        #    return
        ##D('win dict, text begin')
        #self.updateState()
        
    #def selectField(self):
    #    """if field ([x] is selected), do all three of the characters
    #    """
    #    self.fieldIsSelected = 0
    #    dct = self.dictObj
    #    sel = dct.getTextSel()
    #    if sel[0] == 0: return
    #    t = dct.getText(sel[0], sel[1])
    #    print 'selection: %s, %s, selected text: |%s|'% (sel[0], sel[1], t)
    #    if not t:
    #        print 'return from select field, result: %s'% self.fieldIsSelected
    #        return
    #    if len(t) > 1 and t[0] == '[' and t[-1] == ']':
    #        self.fieldIsSelected = 1
    #        print 'return from select field (got a field), result: %s'% self.fieldIsSelected
    #        return
    #    print 'selected now: |%s|'% t
    #    tBefore = dct.getText(sel[0]-1, sel[0])
    #    tAfter = dct.getText(sel[1], sel[1]+1)
    #    if tBefore[0] == '[' and tAfter[-1] == ']':
    #        newSel = (sel[0]-1, sel[1]+1)
    #        dct.setTextSel(newSel[0], newSel[1])
    #        self.setSelection(newSel[0], newSel[1])
    #        time.sleep(0.3)
    #        self.looseFocus()
    #        self.fieldIsSelected = 1
    #    print 'end of select field, result: %s'% self.fieldIsSelected
    # We get this callback when something in the dictation object changes
    # like text is added or something is selected by voice.  We then update
    # the edit control to match the dictation object.

    def onTextChange(self,delStart,delEnd,newText,selStart,selEnd):
        if self.inOnTextChange:
            return
        self.inOnTextChange = 1
        D('onTextChange: %s, %s, |%s|, %s, %s'% ( delStart, delEnd, repr(newText), selStart, selEnd) )
        
        if not self.ctrl:
            D("do not have ctrl control")
            return
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
        self.inOnTextChange = 0
        if getFocus:
            unimacroutils.SetForegroundWindow(self.app)
        

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
        
    def scratchThat(self):
        if self.lastSel:
            selStart, selEnd = self.lastSel
            if selStart < selEnd and self.lastSelText != " ":
                self.scratchinfo = []
                self.insertText(selStart, selEnd, "")                
                return
                
        if self.scratchinfo:
            info = self.scratchinfo.pop()
        else:
            print('scratch that buffer empty')
            return            
        (selStart, selEnd), newText, (delStart, delEnd), prevText = info
                              
        D('scratch that: selStart, selEnd: %s, %s, latest text: %s'% (selStart, selEnd, newText))
        D('to replace with delStart, delEnd: %s, %s, previous text: %s'% (delStart, delEnd, prevText))
        myDelStart = selEnd - len(newText)
        myDelEnd = selEnd
        myNewText = prevText
        mySelEnd = myDelStart + len(prevText)
        mySelStart = mySelEnd - selEnd + selStart
        dct = self.dictObj
        dct.setLock(1)
        dct.setText(myNewText, myDelStart, myDelEnd)
        dct.setTextSel(mySelStart, mySelEnd)
        self.setSelection(myDelStart, myDelEnd)
        self.replaceSelection(myNewText)
        self.setSelection(mySelStart, mySelEnd)
        dct.setLock(0)
            
    #def undoDctBuffer(self, delStart, delEnd, newText, selStart, selEnd):
    #    """go back to previous situation in internal buffer
    #    """
    #    dct = self.dictobj
    #    dct.setText("", delStart, selEnd)
        
    def adjustAtStartOfText(self, delStart,newText):
        """insert space at start, possibly change delStart,
        
        return delStart and the new newText
        """
        dct = self.dictObj
        if self.lastSelText == '[x]':
            print('field found1')
            newText = self.capitalizeNoSpace(newText)
            return delStart, newText
        elif self.lastSelText.lstrip() == '[x]':
            print('field found2')
            newText = ' ' + self.capitalizeNoSpace(newText)
            return delStart, newText
        
        textBefore = dct.getText(max(0, delStart-20), delStart)
        textBefore = textBefore.split('\n')[-1]
        textBeforeStripped = textBefore.rstrip(' ')
        nSpacesBefore = len(textBefore) - len(textBeforeStripped)
        if nSpacesBefore:
            D("spaces before: %s, text before stripped: |%s|"%
                         (nSpacesBefore, repr(textBeforeStripped[-2:])))
        elif textBefore:
            D("text before: |%s|"% textBefore[-2:])
        else:
            D("no relevant text before cursor")

        if not textBeforeStripped:
            # start of buffer of start of line:
            newText = self.capitalizeNoSpace(newText)
            return delStart, newText

        # first sort out capitalization:
        newText = newText.lstrip(' ')
        if textBeforeStripped[-1] == ".":
            if textBefore[-2] in string.letters:
                # capitalize next
                newText = self.capitalizeNoSpace(newText)
        elif textBeforeStripped[-1] in "!?":
            newText = self.capitalizeNoSpace(newText)
        # next sort out spacing:
        if nSpacesBefore == 0:
            if textBefore[-1] in string.letters:
                if newText and newText[0] in string.letters:
                    newText = " " + newText
            elif textBefore[-1] in string.punctuation:
                if newText and newText[0] in string.letters:
                    newText = " " + newText
        elif newText and newText[0] in string.punctuation:
            delStart -= nSpacesBefore
        return delStart, newText
    
    def adjustAtEndOfText(self, selStart, delEnd, newText):
        """adjust at end of buffer
        remove spaces and select one extra space for visibility

        return selStart, selEnd, newText
        """
        dct = self.dictObj
        textAfter = dct.getText(delEnd, delEnd+20)

        newTextStripped = newText.rstrip(' ')
        nSpaces = len(newText) - len(newTextStripped)
        if nSpaces:
            selEnd = selStart
            selStart = selStart - nSpaces
            return selStart, selEnd, newText
        else:
            if not (textAfter and textAfter[0] == " "):
                newText = newText + " "
            selEnd = selStart + 1
            return selStart, selEnd, newText

    def capitalizeNoSpace(self, newText):
        """remove spaces at start, capitalize first character
        """
        D("capitalize no space before |%s|"% newText)
        while newText and newText[0] == ' ':
            newText = newText[1:]
        if newText:
            newText = newText[0].upper() + newText[1:]
        D("capitalize no space result |%s|"% newText)
        return newText


    def getInfoBeforeCursor(self, bufferBefore):
        """return the last non space character  and the number of spaces at the end
        
        if at beginning of line or buffer, (None, numSpaces) is returned
        """
        bufferStripped = bufferBefore.rstrip(' ')
        nSpaces = len(bufferBefore) - len(bufferStripped)
        if bufferStripped:
            last = bufferStripped[-1]
            if last == '\n':
                last = None
        else:
            last = None
        return last, nSpaces
    def capitaliseFirstCharacter(self, text):
        """leave leading spaces intact, cap first word
        """
        if not text.lstrip(' '):
            return text
        tStripped = text.lstrip(' ')
        if tStripped == text:
            return text[0].upper() + text[1:]
        nSpaces = len(text) - len(tStripped)
        return ' '*nSpaces + tStripped[0].upper() + tStripped[1:]
        
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

    def updateState(self, checkField=1):
        dct = self.dictObj
        if testMode:
            beforeLength = dct.getLength()
            beforeText = dct.getText(0, beforeLength)
        if self.ctrl:
            text = self.getWindowText()
            #text = text.replace('\r', '')   # only \n for internal buffer
            selStart,selEnd = self.getSelection()
            #D("updateState, ctrl: selStart, selEnd: %s, %s"% (selStart, selEnd))
        visStart,visEnd = self.getVisibleRegion()
        if (visStart, visEnd) == (None, None):
            visStart, visEnd = 0, len(text)
        dct.setLock(1)
        dct.setText(text,0,0x7FFFFFFF)
        dct.setTextSel(selStart,selEnd)
        dct.setVisibleText(visStart, visEnd)
        self.lastSel = (selStart, selEnd)
        self.lastSelText = text[selStart:selEnd]
        D("dictObj set with text: %s (visible: %s, %s)"% (len(text), visStart, visEnd))
        D("part of text (10 left from selStart): |%s|"% repr(dct.getText(min(0, selStart-10), 0x7FFFFFFF)))
        if 0:  # testMode:
            afterLength = dct.getLength()
            afterText = dct.getText(0, afterLength)
            if afterLength != beforeLength:
                D("length after updating not the same: before: %s, after: %s"%
                  (beforeLength, afterLength))
            if afterText != beforeText:
                D("textafter updating not the same: before:\n|%s|\nafter:\n|%s|\n"%
                  (repr(beforeText), repr(afterText)))

        if selStart > 0 and self.lastSelText == 'x':
            if text[selStart-1:selStart] == '[' and text[selEnd:selEnd+1] == ']':
                print('extend selection')
                selStart -= 1
                selEnd += 1
                self.setSelection(selStart, selEnd)
                dct.setTextSel(selStart, selEnd)
                self.lastSel = (selStart, selEnd)
                self.lastSelText = text[selStart:selEnd]
        if self.lastSelText.strip() == '[x]':
            print('lastSelText, want to loose focus!!: |%s|'% self.lastSelText)
            
            hndle = win32gui.GetForegroundWindow()
            newHasFocus = (hndle == self.app)
            if newHasFocus != self.hasFocus:
                print('focus changed during updateState/gotBegin, now: %s'% newHasFocus)
                self.hasFocus = newHasFocus
            if newHasFocus:
                print('loosing focus')
                self.looseFocus()
                hndle = win32gui.GetForegroundWindow()
                if hndle == self.app:
                    print('could not loose focus!!')
        dct.setLock(0)
            
       
    def clearBoth(self):
        """for testing, clear dictobj and current window
        """
        if not self.ctrl:
            print("no current control active...")
        mess.setEditText(self.ctrl, "")
        self.updateState()
        

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
        #print 'getting buffer'
        tList = mess.getEditText(self.ctrl)
        #print '\n\ntList one:\n|%s|\n'% repr("||".join(tList))
        ## remove internal (for scrolling purposes) newline characters:
        #tList = [t.replace('\n', '') for t in tList]
        #print 'tList two:\n|%s|\n\n'% repr("||".join(tList))
        #tList = [t.replace('\n', '') for t in tList]
        #print 'tList: '
        #for i, t in enumerate(tList):
        #    print '%s: %s'% (i, repr(t))
        # the \r at end of lines remain and are the real paragraph signs
        # the intermediate \n characters are ignored in the dictobj.
        # apparently only visible for copy paste, not relevant for cursor count.
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
            self.__class__.ctrl = None
            self.__class__.app = None

ancestor = natbj.IniGrammar
class CmdsGrammar(ancestor):
    name = "global dictation"
    alwaysrules = ['insertfragments', 'nextfield', 'selectclearall', 'testrule', 'getloosefocus']
    outsidefocusrules = alwaysrules + ['gotobeginend', 'scratch', 'deletecharswords']
    
    gramSpec = """
<insertfragments> exported = (insert) {fragments};
<gotobeginend> exported = goto (begin|end|top|bottom);
<nextfield> exported = jump | next field;
<selectclearall> exported = (clear|select) all;
<scratch> exported = scratch [that] [{scratchcounts}];
                     
<deletecharswords> exported = (backspace | delete) {backspacedeletecounts};
<getloosefocus> exported = (get|acquire|loose) focus;
<testrule> exported = global dictation test ({global_tests}|all);
"""
    def __init__(self):
        ancestor.__init__(self)
        self.dictobj = None

    def gotBegin(self, modInfo):
        hndle = modInfo[2]
        dct = self.dictobj
        dct.getEditControl() # also notices when app has been killed.
        
        if self.prevHndle == hndle:
            if dct.app and not dct.hasFocus:
                dct.updateState()
            return   # no change
        if modInfo[1] == "Spell":
            #print "Spell window"
            return
        self.prevHndle = hndle
        dct.saveFocus() # loosing the focus...
        # focus changed, so hasFocus state can be changed:
        if not dct.app:
            print('no dictation application ready: %s'% dct.app)
            dct.dictObj.deactivate()
            self.activateSet(self.outsidefocusrules)
            return
        dct.updateState()
        hndle = win32gui.GetForegroundWindow()
        if dct.app == hndle:
            if dct.hasFocus != 1:
                self.activateSet(self.alwaysrules, exclusive=0)
                dct.hasFocus = 1
                print('got focus')
                dct.dictObj.deactivate()
        else:
            if dct.hasFocus != 0:
                # lost focus now:
                print("loosing focus")
                self.activateSet(self.outsidefocusrules)
                dct.hasFocus = 0
                dct.dictObj.activate(0)
  
    def wait(self, waitTime=None):
        """some short time after each command
        
        waits after actions with messagefunctions are in the wrapper functions
        of the VoiceDictation instance
        """
        self.dictobj.wait(waitTime)
        
    def initialize(self):
        self.load(self.gramSpec)
        #print 'cmdGrammar loaded'
        # if switching on fillInstanceVariables also fill number1to9 and number1to99!
        self.switchOnOrOff()

        self.prevHndle = 0
        if not self.dictobj:
            self.dictobj = VoiceDictation()
            self.dictobj.initialize()
        
    def gotResults_insertfragments(self,words,fullResults):
        """special commands"""
        dct = self.dictobj
        #print 'includefragments: %s'% `words`
        for w in words[1:]:
            t = self.getFromInifile(w, 'fragments')
            if w.lower() == "impression":
                self.gotResults_gotobeginend(["goto", "top"], fullResults)
                self.wait()
                dct.sendKey("{end}")
            if w.lower() in ["findings", "impression", "history", "technique", "comparison"]:
                dct.sendEnterKey(2)
                self.wait()
            if t:
                t = dct.correctForNewlines(t)
                delStart, delEnd = dct.getSelection()
                selStart = selEnd = delStart + len(t)
                dct.onTextChange(delStart,delEnd,t,selStart,selEnd)
                dct.updateState()
                
            if w.lower() in ["findings", "impression", "history", "technique", "comparison"]:
                dct.sendKey(" ")
                self.wait()
                dct.updateState()             
                 
    def gotResults_gotobeginend(self,words,fullResults):
        """special commands"""
        dct = self.dictobj
        w = words[-1]
        if w in ("bottom", "end"):
            dct.setSelection(-1,-1)
        elif w in ("top", "begin"):
            dct.setSelection(0,0)
        dct.updateState()

    def gotResults_selectclearall(self,words,fullResults):
        """try to select (and clear) all text through messages menu commands
        
        focus does not have to change
        """
        dct = self.dictobj
        if dct.app:
            #prevFocus = dct.acquireFocus()
            #print 'prevFocus %s , newFocus: %s'% (prevFocus, dct.app)
            #self.wait(1)
            dct.activateMenuItem("commandselectall")
            self.wait()
            if self.hasCommon(words, "clear"):
                print("clear window")
                #keystroke("{del}")
                dct.sendKey("{del}")
            #self.wait(2)
            #dct.looseFocus(prevFocus)
        else:
            D("Not a valid menu command in app %s: %s"% (dct.app, dct.commandselectall))

    def gotResults_nextfield(self,words,fullResults):
        """special commands"""
        dct = self.dictobj
        if dct.app and dct.commandnextfield:
            prevFocus = dct.acquireFocus()
            dct.activateMenuItem("commandnextfield")
            #this is a test.dct.updateState()
            dct.looseFocus(prevFocus)
            hndle = win32gui.GetForegroundWindow()
            if hndle == dct.app:
                print('in target application')
                self.wait(1)
                dct.sendKey("{backspace}")
                self.wait()
                natlink.recognitionMimic(["\\Cap"])
            #dct.selectField()
        else:
            D("Not a valid menu command in app %s: %s"% (dct.app, dct.commandnextfield))

    def gotResults_scratch(self,words,fullResults):
        """undo one or more steps of the undo list"""
        nScratch = 1
        t = self.getFromInifile(words[-1], 'scratchcounts')
        if t:
            nScratch = int(t)
            print('scratch that %s (%s)'% (nScratch, t))
        dct = self.dictobj
        if dct.app:
            for i in range(nScratch):
                dct.scratchThat()
        else:
            D("scratch that invalid, app not active: %s"% dct.app)
              
    def gotResults_deletecharswords(self,words,fullResults):
        """delete one of more characters (later words) 
        to the right or to the left.
        """
        nToDo = 1
        t = self.getFromInifile(words[-1], 'backspacedeletecounts')
        if t:
            nToDo = int(t)
        
        if self.hasCommon(words, 'delete'):
            Key = "{delete}"
        elif self.hasCommon(words, 'backspace'):
            Key = "{backspace}"
        else:
            raise ValueError("invalid keyword for rule deletecharswords: %s"% words[0])
            
        dct = self.dictobj
        if dct.app:
            for i in range(nToDo):
                dct.sendKey(Key)
        else:
            D("deletecharswords invalid, app not active: %s"% dct.app)
              
    def gotResults_getloosefocus(self,words,fullResults):        
        """get or loose focus of the special dictation window
        """
        dct = self.dictobj
        if self.hasCommon(words, 'loose'):
            dct.looseFocus()
        else:
            dct.acquireFocus()


    def gotResults_testrule(self,words,fullResults):        
        """special for testing the synchronisation between dictObj and real window
        
        one: just dictate a few words
        two: dictate on two lines (with empty in between)
        three: select the word "second" on the second line of text
        four:  put a larger text in the window (so it scrolls) and select text.
        
        
        """
        dct = self.dictobj
        dct.clearBoth()
        test = words[-1]
        if test == 'all':
            # get list of keywords in the inifile:
            tests = self.ini.get('global_tests')
            if tests:
                print('testwords: %s'% tests)
                for lastWord in tests:
                    natlink.recognitionMimic(["global", "dictation", "test", lastWord])
                return
            else:
                print('found no "global dictations tests"')
                return 
                
        if test == "one":
            # test just one line of text, to be found in dictobj and in actual window (through messagefunctions)
            natlink.recognitionMimic(["hello", "test", "one"])
            time.sleep(0.5)
            beforeLength = dct.dictObj.getLength()
            beforeText = dct.dictObj.getText(0, beforeLength)
            messText = dct.getWindowText()
            dct.updateState()
            afterLength = dct.dictObj.getLength()
            afterText = dct.dictObj.getText(0, beforeLength)
            expected = ["Hello test one " + dct.aftertext,
                        "Hello test one" + dct.aftertext] # 0: other window, 1: window has focus
            if not self.assert_equal_strings(expected, beforeText, "test %s; beforeText (dctobj) matches expected??"% test):
                return
            if not self.assert_equal_strings(beforeText, messText, "test %s; beforeText, messText equal test"% test):
                return
            if not self.assert_equal_strings(beforeText, afterText, "test %s; beforeText, afterText equal test"% test):
                return
            print('test %s OK--'% test)
            return 1  # OK
        elif test in ('two', 'three'):
            thirdWord = "second"
            if test == 'three': thirdWord = "third"
            # send a three line (two paragraph) text, and test the result:
            natlink.recognitionMimic(["hello", "\\New-Paragraph", thirdWord, "test"])
            time.sleep(0.5)
            beforeLength = dct.dictObj.getLength()
            beforeText = dct.dictObj.getText(0, beforeLength)
            messText = dct.getWindowText()
            dct.updateState()
            if test == ('two', 'three'):
                afterLength = dct.dictObj.getLength()
                afterText = dct.dictObj.getText(0, beforeLength)
                expected = ["Hello\r\%s test %s" (thirdWord.capitalize(), dct.aftertext),
                            "Hello\r\r%s test"% (thirdWord.capitalize(),dct.aftertext)]  # 0: other window, 1: window has focus
                if not self.assert_equal_strings(expected, beforeText, "test %s; beforeText (dctobj) matches expected??"% test):
                    return
                if not self.assert_equal_strings(beforeText, messText, "test %s; beforeText, messText equal test"% test):
                    return
                if not self.assert_equal_strings(beforeText, afterText, "test %s; beforeText, afterText equal test"% test):
                    return
                if test == 'two':
                    print('test %s OK--'% test)
                    return 1
            if test == 'three':
                # select a word on the third line (second paragraph)
                natlink.recognitionMimic(["select", "third"])
                time.sleep(0.5)
                beforeSel = dct.dictObj.getTextSel()
                dctSelection = beforeText[beforeSel[0]:beforeSel[1]]
                messSel = mess.getSelection(dct.ctrl)
                messSelection = messText[messSel[0]:messSel[1]]
                expected = "Third "
                if not self.assert_equal_strings(expected, dctSelection, "test %s; selection from dctobj "% test):
                    return
                if not self.assert_equal_strings(expected, messSelection, "test %s; selection from message window "% test):
                    return
                print('test %s OK--'% test)
                return 1 # OK
        if test == "four":
            natlink.recognitionMimic(["test", "four", "\\New-Paragraph", "there", "we", "go"])
            natlink.recognitionMimic(["insert", "test", "fracture"])
            natlink.recognitionMimic(["hello", "after", "fracture"])
            natlink.recognitionMimic(["select", "hello", "after"])
            time.sleep(0.5)
            
            beforeLength = dct.dictObj.getLength()
            beforeText = dct.dictObj.getText(0, beforeLength)
            beforeSel = dct.dictObj.getTextSel()
            dctSelection = beforeText[beforeSel[0]:beforeSel[1]]
            messText = dct.getWindowText()
            messSel = mess.getSelection(dct.ctrl)
            messSelection = messText[messSel[0]:messSel[1]]
            expected = "Hello after "
            if not self.assert_equal_strings(expected, dctSelection, "test %s; selection from dctobj "% test):
                return
            if not self.assert_equal_strings(expected, messSelection, "test %s; selection from message window "% test):
                return
            print('test %s OK--'% test)
            return 1 # OK
        if test == 'five':
            natlink.recognitionMimic(["test", ",\\comma", "five"])
            natlink.recognitionMimic(["select", "test"])
            natlink.recognitionMimic(["hello", "again", "five"])
            self.wait()
            
            beforeLength = dct.dictObj.getLength()
            beforeText = dct.dictObj.getText(0, beforeLength)
            beforeSel = dct.dictObj.getTextSel()
            messText = dct.getWindowText()
            messSel = mess.getSelection(dct.ctrl)
            expected = "Hello again, five"
            if not self.assert_equal_strings(expected, beforeText, "test %s; text from dctobj "% test):
                return
            if not self.assert_equal_strings(expected, messText, "test %s; text from window "% test):
                return
            print('test %s OK--'% test)
            return 1 # OK
        if test == 'six':
            # try to make a field, and see if next dictate removes the field and caps the first char
            natlink.recognitionMimic(["insert", "impression"])
            dct.sendKey(" ")
            dct.sendKey("[")
            dct.sendKey("x")
            dct.sendKey("]")
            natlink.recognitionMimic(["select", "x\\xray"])
            self.wait()
            beforeLength = dct.dictObj.getLength()
            beforeText = dct.dictObj.getText(0, beforeLength)
            beforeSel = dct.dictObj.getTextSel()
            messText = dct.getWindowText()
            messSel = mess.getSelection(dct.ctrl)
            expected =   '\r\rImpression: [x]\r'
            if not self.assert_equal_strings(expected, beforeText, "test %s; text from dctobj "% test):
                return
            if not self.assert_equal_strings(expected, messText, "test %s; text from window "% test):
                return
            dctSelection = beforeText[beforeSel[0]:beforeSel[1]]
            messSelection = messText[messSel[0]:messSel[1]]
            expected = "[x]"
            if not self.assert_equal_strings(expected, dctSelection, "test %s; selection from dctobj (selected field) "% test):
                return
            if not self.assert_equal_strings(expected, messSelection, "test %s; selection from message window (selected field) "% test):
                return
            
            print('test %s OK--'% test)
            return 1 # OK
            
        if test == 'seven':
            # try to make a field, and see if next dictate removes the field and caps the first char
            natlink.recognitionMimic(["insert", "findings"])
            dct.sendKey(" ")
            dct.sendKey("[")
            dct.sendKey("x")
            dct.sendKey("]")
            natlink.recognitionMimic(["select", "x\\xray"])
            self.wait()
            natlink.recognitionMimic(["insert", "test", "bone"])
            beforeLength = dct.dictObj.getLength()
            beforeText = dct.dictObj.getText(0, beforeLength)
            beforeSel = dct.dictObj.getTextSel()
            messText = dct.getWindowText()
            messSel = mess.getSelection(dct.ctrl)
            expected =  '\r\rImpression:\r\r1. Text in field \r'
            if not self.assert_equal_strings(expected, beforeText, "test %s; text from dctobj "% test):
                return
            if not self.assert_equal_strings(expected, messText, "test %s; text from window "% test):
                return
            print('test %s OK--'% test)
            return 1 # OK
            
            
        
            

    def assert_equal_strings(self, one, two, message):
        """one is expected string or list of strings
        
        if one is a list, 0: focus on, 1: focus elsewhere
        returns 1 if OK, 0 if error.
        """
        dct = self.dictobj
        hndle = win32gui.GetForegroundWindow()
        
        if hndle == dct.app:    
            message = 'testing equal strings, focus ON\n-- %s --'% message
            if type(one) == list:
                one = one[1] # second alternative on list
        else:
            message = 'testing equal strings, focus OFF (extra space often)' + message
            if type(one) == list:
                one = one[0]  # first alternative on list
        if one == two:
            return 1
        print('\nerror at test'+ message) 
        
        if len(one) != len(two):
            print('unequal lengths: %s, %s'% (len(one), len(two)))
        for i, (charOne, charTwo) in enumerate(zip(one, two)):
            if charOne != charTwo:
                print("strings different on pos: %s"% i)
                print("one: %s, two: %s"% (repr(charOne), repr(charTwo)))
                print("command start of string: %s"% repr(one[:i]))
                print("one: %s"% repr(one))
                print("two: %s"% repr(two))
                break
        else:
            # identical start, so tail must be different.
            if len(one) > len(two):
                print('one is longer with: |%s|'% repr(one[len(two):]))
            else:
                print('two is longer with: %s'% repr(two[len(one):]))

    def assert_equal_selection(self, one, two, message):
        print('testing equal selection: %s'% message)
        if len(one) != len(two):
            print('unequal lengths: %s, %s'% (len(one), len(two)))
        if one != two:
            print('unequal selections: %s, %s'% (repr(one), repr(two)))
            return
        print('test OK----------------')
        return 1
        
# debug print, only if testMode is o
def D(t):
    if testMode:
        print(t)

# standard stuff Joel:
cmdsGrammar = CmdsGrammar()
if cmdsGrammar.gramSpec:
    cmdsGrammar.initialize()
else:
    cmdsGrammar = None

#dictObj = VoiceDictation() # now called from commands grammar... may have to change this
#dictObj.initalize()

#dictObj = None
def unload():
    global cmdsGrammar, dictObj
    if cmdsGrammar:
        cmdsGrammar.dictobj.terminate()
        cmdsGrammar.unload()
    cmdsGrammar = None
    #if dictObj:
    #    dictObj.terminate()
    #    dictObj = None
        
messWindow = None
messTitle = "Messages from Python Macros"
def changeCallback(type,args):
    global messWindow
    # not active without special version of natlinkmain,
    # call the cancelMode, to switch off exclusive mode when mic toggles:
    # try to find the messages window at each mic on and minimize if found:
    if type == 'mic' and args == 'on':
        if testMode: return # only in production mode...
        #print 'mic on, messWindow: %s'% messWindow
        if messWindow:
            try:
                title = win32gui.GetWindowText(messWindow)
                if title != messTitle:
                    print('title does not match: actual: |%s|, wanted: |%s|'% (title, messTitle))
                    messWindow = None
            except:
                messWindow = None
        if not messWindow:
            messWindows = mess.findTopWindows(wantedText="Messages from Python Macros")
            if messWindows:
                messWindow = messWindows[0]
        if not messWindow:
            print('didnt find messages window')
            return
        #toMin = win32con.SW_MINIMIZE
        toMin = win32con.SW_SHOWMINIMIZED
        info = list( win32gui.GetWindowPlacement(messWindow) )
        #print 'info1: %s, SW_SHOWMINIMIZED: %s'% (info[1], toMin)
        info[1] = toMin
        win32gui.SetWindowPlacement(messWindow, tuple(info) )
            
        
