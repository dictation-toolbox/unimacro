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
#  _oops.py, can oops the last phrase
#
#  Written by : Quintijn Hoogenboom,QH softwaretraining & advies,
#    July 2002/August 2003
#
"""DragonDictate like "oops" a wrong misunderstood last phrase

The command "Oops" (as was in DragonDictate) is implemented in this
grammar. In the message window the list of alternatives is brought up.
You can choose the item you want. No typing however can be done if the
right choice is not in the list.

This oops command is enhanced with several commands which can be given
in the message window which displays the choice list.
1. Choose # can be followed by the words [middle|strong] to do the
correction and number of times
2. Format #: after that a list of formats is presented from which
the right format can be chosen
3. Delete #: the word is deleted from the active vocabulary

this is a tricky grammar file, because the allResults-flag is
turned on.

 Note: the Oops grammar uses exclusive mode. If my modified
 "natlinkmain.py" is used, this exclusive mode is turned off
 whenever the microphone state with changes.

 

"""


import natlink
import win32gui
from dtactions.unimacro import utilsqh
from natlinkcore import natlinkutils
from dtactions.unimacro import unimacroutils
from dtactions.unimacro import unimacroutils
import unimacro.natlinkutilsbj as natbj
import time
import copy
import sys
import os
import operator
logHour = -1
logFile = ''

language = unimacroutils.getLanguage()
version = unimacroutils.getDNSVersion()
UUDirectory = unimacroutils.getUnimacroUserDirectory()
# print 'language: %s (%s)'% (language, type(language))
# print 'version: %s (%s)'% (version, type(version))
# print 'getUnimacroUserDirectory: %s (%s)'% (UUDirectory, type(UUDirectory))
logFolder = os.path.join(UUDirectory, language + "_log", unimacroutils.getUser())
print('_oops, logfolder: %s'% logFolder)
 
def getLogFileName():
    """get name with date and time, record hour in logHour"""
    global logHour, logFile
    utilsqh.createFolderIfNotExistent(logFolder)
    lTime = time.localtime()
    logFile = time.strftime("%Y-%m-%d %H%M", lTime)  + '.txt'
    logHour = lTime[3]
    logFile = os.path.join(logFolder, logFile)
    #print 'logHour: ', logHour, ' log to file: ', logFile

ChooseList = ['1','2','3','4','5','6','7','8','9','10']

# get language for different language versions:
language = unimacroutils.getLanguage()

#  Number of times the correction is executed when choosing weak
#    (default), middle or strong
choiceWeak = 1
choiceMiddle = 5
choiceStrong = 15


#  The following set of formats can be used in the formatting part of
#    this grammar.  Can be enhanced to your own needs.
#  FORMATS and FormatComments MUST MATCH!
FORMATS = {
    # for letters in advance of a variable:
    1: ( unimacroutils.wf_TurnCapitalizationModeOn |
           unimacroutils.wf_TurnOffSpacingBetweenWords |
           unimacroutils.wf_DoNotApplyFormattingToThisWord
          ),
    # for continuing after a variable:
    2: ( unimacroutils.wf_RestoreNormalCapitalization |
            unimacroutils.wf_RestoreNormalSpacing
          ),
    # for continuing after a variable + extra space:
    3:  ( unimacroutils.wf_RestoreNormalCapitalization |
            unimacroutils.wf_RestoreNormalSpacing |
            unimacroutils.wf_AddAnExtraSpaceFollowingThisWord
          ), 
    # for continuing after a variable, no space before:
    4: ( unimacroutils.wf_RestoreNormalCapitalization |
            unimacroutils.wf_RestoreNormalSpacing |
            unimacroutils.wf_NoSpacePreceedingThisWord
          )
    }

if language == 'nld':
    FormatComments = {
        1: 'letters',
        2: 'herstel',
        3: 'herstel + spatie (als "spatie")',
        4: 'herstel + geen spatie ervoor (als ":")'
    }
    if unimacroutils.getDNSVersion() >= 7:
        ScratchThatCommand = ['schrap', 'dat']
    else:
        ScratchThatCommand = ['Schrap', 'dat']
    WordCommand = 'commando'
    WordDictate = 'dictaat'
else:
    FormatComments = {
        1: 'switch on capitalization and switch off spacing (for prefix letters)',
        2: 'restore capitalization and spacing',
        3: 'restore and add a space (like "space-bar")',
        4: 'restore, but no space before (like ":")'
    }
    if unimacroutils.getDNSVersion() >= 7:
        ScratchThatCommand = ['scratch', 'that']
    else:
        ScratchThatCommand = ['Scratch', 'That']
    WordCommand = 'commando'
    WordDictate = 'dictate'

if len(list(FORMATS.keys())) != len(list(FormatComments.keys())):
    print('warning _oops: FORMATS and FormatComments do not match')
    DoFormatting = 0
else:
    DoFormatting = 1

ancestor = natbj.IniGrammar
class ThisGrammar(ancestor):
    iniIgnoreGrammarLists = ['chooselist'] # are set in this module    
    name = "oops"
    gramSpec = """
<oops> exported = Oops;
<inoops> exported = Cancel | OK | <choose>;
<choose> = (Choose|Format|Delete|Properties) {chooselist} | (Choose|Format|Delete|Properties) {chooselist}(Weak|Medium|Strong);
<inoops2> exported = Cancel | OK | (Choose Format (1 | 2 | 3| 4));
        """

    def initialize(self):
        self.load(self.gramSpec, allResults=1)
        self.oopsFlag = 0
        self.lastResObj = None
        self.messageHndle = 0
        self.setList('chooselist', ChooseList)
        if language == 'nld':
            print('Grammatica _oops ge-initialiseerd')
        else:
            print('Grammar _oops initialized')
        self.cancelMode()
        self.prevModinfo = None
        self.switchOnOrOff(activateRule='oops')
        if self.logging:
            print('_oops, logging of utterances to dir:\n\t%s'% logFolder)
        else:
            print('_oops, NO logging of utterances')

    def fillInstanceVariables(self):
        """fills the necessary instance variables

        
        """
        self.logging = self.ini.getBool('general', 'log all utterances')

    def gotBegin(self,moduleInfo):
        """log changed modinfo"""
        if self.checkForChanges:
            self.checkInifile()

        # print('time in gotBegin: %s'% time)
        if self.logging and self.prevModinfo != moduleInfo:
            # print('time: %s'% time)
            lTime = time.localtime()
            if logHour != lTime[3]:
                #print 'get new logfilename'
                getLogFileName()
            prog = os.path.split(moduleInfo[0])[1]
            minutes = time.strftime("%H:%M", time.localtime())

            logToFile('\n%s---%s---%s(%s)'% (minutes, prog, moduleInfo[1], moduleInfo[2]))
            self.prevModinfo = moduleInfo
        #else:
        #    print 'no logging or same moduleInfo: %s, %s, %s'% (self.logging, repr(self.prevModinfo), repr(moduleInfo))
  
##        if self.oopsFlag:
##            self.oopsFlag = self.oopsFlag - 1
##            if self.oopsFlag == 0:
##                print 'Canceling oops mode'
##                self.cancelMode()
    def gotResultsInit(self, words, fullResults):
        self.hadChoice = None
        self.nChoice = choiceMiddle  


    def gotResultsObject(self,recogType,resObj):
        #  If in oops mode, no actions are taken in this function.  If
        #    however the grammar was rejected, which is exclusive whenever the
        #    oops mode is on, the warning message is printed.hello
        if self.logging:
            if natlink.getCallbackDepth() < 3:
                try:
                    words = resObj.getWords(0)
                except (natlink.OutOfRange, IndexError):
                        words = "<???>"

                resCode = -1
                isDictate = -1
                k, rest = -1, -1
                for i in range(10):
                    try:
                        res = resObj.getResults(i)
                        try:
                            lenWave = len(resObj.getWave())
                        except natlink.DataMissing:
                            lenWave = 0
                        k,rest = int(lenWave/1000), lenWave%1000
                        resCode = res[0][1]
                        resCode = resCode & 0x7fffffff
                        if i == 0:
                            isDictate = not resCode
                        if resCode:
                            break
                    except (natlink.OutOfRange, IndexError):
                        break

                if isDictate == -1:
                    line = '  <???> '
                elif isDictate and not resCode:
                    line = '  %s (only dictate alternatives)'% ' '.join(words)
                elif isDictate:
                    line = '  %s (dictate, command alternatives)' % ' '.join(words)
                else:
                    line = '  %s (command %s)'% (words, resCode)
                if k == -1:
                    logToFile(line+'(nowave)')
                elif rest <= 500:
                    logToFile(line+'(%sk+%s)'% (k, rest))
                else:
                    logToFile(line+'(%sk-%s)'% (k+1, 1000-rest))
                    
            
        if recogType == 'other':
            # remember result for repeat grammar:
            if natlink.getCallbackDepth() < 3:
                self.lastResObj = resObj
##            else:
##                print 'callbackdepth" %s, words: %s'%(natlink.getCallbackDepth(), resObj.getWords(0))
                

    def gotResults_oops(self,words,fullResults):
##        t0 = time.time()
##        try:fellow,hellohellohellohello hellohello,fellow hello hello hello
##        try:
##            unimacroutils.SetForegroundWindow(self.messageHndle)
##        except:
        unimacroutils.switchToWindowWithTitle("Messages from Python Macros")
##            self.messageHndle = natlink.getCurrentModule()[2]
##            print 'new handle for message window: %s'% self.messageHndle
##        print 'time to switch:', time.time() - t0
        if not self.lastResObj:
            print('no object to Oops')
            unimacroutils.Wait(0.1)
            unimacroutils.returnFromMessagesWindow()
            return
        #  Go through the alternatives in the results object
        SingleWord = 0  # so formatting can be done
        self.FirstIsDictate = 0
        #waveText = self.lastResObj.getWave()
        #print 'gesproken: %s' % len(waveText)
        for i in range(10):
            try:
                res = self.lastResObj.getResults(i)
                words = self.lastResObj.getWords(i)
                resCode = res[0][1]
                resCode = resCode & 0x7fffffff
                wordInfo = self.lastResObj.getWordInfo(i)
##                pron = []
##                if wordInfo:
##                    pron = map(lambda x: x[6].join(wordInfo))
                if resCode:
                    print("%s:\t[%s]  (%s %s)" % (i+1,  repr(words), WordCommand,resCode))
                else:
                    print("%s:\t%s  (%s)" % (i+1, repr(words), WordDictate))
                    if i == 0:
                        self.FirstIsDictate = 1
                    if len(words) == 1:
                        SingleWord = 1

                    
            except (natlink.OutOfRange, IndexError):
                break
        else:
            i = 10
        if language == 'nld':
            print("OK, Annuleren, of Kies 1, ..., Kies %s [middel|sterk]" % i)
            if SingleWord:
                print("of Format #, Verwijder # of Eigenschappen #  (# = 1, ..., %s)" % i)
        else:
            print("OK, Cancel, or Choose 1, ..., Choose %s [Medium|Strong]" % i)
            if SingleWord:
                print("or Format #, Delete # or Properties # (# = 1, ..., %s)" %i)

        self.oopsFlag = 3
        self.activateSet(['inoops'],exclusive=1)
        self.setList('chooselist', ChooseList[:i])
        unimacroutils.switchToWindowWithTitle("Messages from Python Macros")

    def gotResults_inoops(self,words,fullResults):
        nCorr = choiceWeak
        choice = 0
        if not self.lastResObj:
            self.cancelMode()
            unimacroutils.returnFromMessagesWindow()
            
        if self.hasCommon(words, 'Cancel'):
            texts = dict(nld='oeps geannuleerd')
            t = texts.get(self.language, 'oops canceled')
            self.DisplayMessage(t)
            print('cancelling exclusive oops mode')
            unimacroutils.Wait()
            self.cancelMode()
            unimacroutils.returnFromMessagesWindow()
            return
        choice = 0
        if self.hasCommon(words, 'OK'):
            print('OK')
            self.hadChoice = 1
            #ww = []
            
    def gotResults_choose(self, words, fullResults):
        self.nChoice = None
        if self.hasCommon(words[-1], 'Medium'):
            self.nChoice = choiceMiddle
        elif self.hasCommon(words[-1], 'Strong'):
            self.nChoice = choiceStrong
        elif self.hasCommon(words[-1], 'Weak'):
            self.nChoice = choiceWeak
        if self.nChoice:
            del words[-1]
        else:
            self.nChoice = choiceMiddle


        if words[-1] in ChooseList:
            choice = int(words[-1])
        if not choice:
            print('no valid choice given')
            unimacroutils.Wait(0.2)
            self.cancelMode()
            unimacroutils.returnFromMessagesWindow()
            return
        try:
            newWords = self.lastResObj.getWords(choice-1)
        except natlink.OutOfRange:
            i = choice-1
            print('_oops, choose %s, no result number %s'% (i,i))
            return
        res = self.lastResObj.getResults(choice-1)
        resCode = res[0][1]
        resCode = resCode & 0x7fffffff
        # formatting:===========================================
        if 'Format' in words:
            if not DoFormatting:
                print('formatting options invalid!')
                return
            
            if resCode:
                print('no formatting can be done on a command!')
                time.sleep(1.5)
            elif len(newWords) > 1:
                print('no formatting can be done on a list of words')
                time.sleep(1.5)
            else:
                self.newWord = newWords[0]
                fKeys = list(FORMATS.keys())
                fKeys.sort()
                fcKeys = list(FormatComments.keys())
                fcKeys.sort()
                if fKeys != fcKeys:
                    print('keys of FORMATS and FormatComments do not match')
                    return
                numChoices = len(fKeys)
                if language == 'nld':
                    print('Formatteren van: %s'% self.newWord)
                    print('Kies Format 1, ..., %i of zeg "Annuleren"' %numChoices)
                elif language == 'enx':
                    print('Formating: %s'% self.newWord)
                    print('Choose Format 1, ..., %i, or say "Cancel"' % numChoices)
                else:
                    print('invalid language, skip this')
                    self.cancelMode()
                    return
                for n in range(numChoices):
                    print('%s:\t%s'%(n+1, FormatComments[n+1]))
                    
                #  Entered the new exclusive grammar rules, for the right
                #    format to be chosen
                self.oopsFlag = 3
                self.activateSet(['inoops2'],exclusive=1)
                return
        # deleting:===========================================
        elif self.hasCommon(words, ['Delete',  'Verwijder']):
            if resCode:
                print('no delete of a command!')
                time.sleep(1.5)
            elif len(newWords) > 1:
                print('no delete on a list of words')
                time.sleep(1.5)
            else:
                natlink.deleteWord(newWords[0])
                print('deleted: %s' % newWords[0])
        elif self.hasCommon(words, ['Properties','Eigenschappen']):
            if resCode:
                print('no properties on a command!')
                time.sleep(1.0)
            elif len(newWords) > 1:
                print('no properties of a list of words')
                time.sleep(1.0)
            else:
                self.newWord = newWords[0]
                props = natlink.getWordInfo(self.newWord)
                print('properties of %s: %x' % (self.newWord, props))
                p = unimacroutils.ListOfProperties(props)
                if p:
                    for pp in p:
                        print(pp)
                    time.sleep(4.0)
        elif self.hasCommon(words, ['Choose', 'Kies', 'OK']):
            hadChoose = 1
            print('correcting: %s (%s times)'%(newWords,self.nChoice))
            for i in range(self.nChoice):
                result = self.lastResObj.correction(newWords)
                if not result:
                    print('correction failed')
                    break
            else:
                print('corrected %s times'% self.nChoice)
        else:
            print('invalid word in command: %s' % repr(words))
            time.sleep(2.0)
        time.sleep(1.0)
        self.cancelMode()
        unimacroutils.returnFromMessagesWindow()
        #  Like in DragonDictate, when the word was not a command but a
        #    dictate word, the last phrase is scratched and replaced by the new
        #    text or the new command.
        if hadChoose and self.FirstIsDictate:
            print('mimic first: %s'% ScratchThatCommand)
            natlink.recognitionMimic(ScratchThatCommand)
            print('now mimic: %s'% newWords)
            natlink.recognitionMimic(newWords)

    def gotResults_inoops2(self,words,fullResults):
        if self.lastResObj:
            fstring = ''
            if self.hasCommon(words, 'Cancel'):
                unimacroutils.Wait()
                self.cancelMode()
                unimacroutils.returnFromMessagesWindow()
                return
            try:
                fNum = int(words[-1])
            except ValuerError:
                fNum = ''
            # fNum = int(words[-1])
            if fNum in list(FORMATS.keys()):
                fstring = FORMATS[fNum]
            else:
                print('invalid paramter choosen: %s' % repr(words))
                fstring = ''
            if fstring and self.newWord:
                oldFormat = natlink.getWordInfo(self.newWord)
                if fstring == oldFormat:
                    print('format of %s is already: %x' % (self.newWord, fstring))
                else:
                    print('formatting word: %s from hex %x to hex: %x'%(self.newWord, oldFormat, fstring))
                    natlink.setWordInfo(self.newWord, fstring)
            self.newWord = ""
        time.sleep(1.0)
        self.cancelMode()
        unimacroutils.returnFromMessagesWindow()

    def cancelMode(self):
        #print "end of oops exclusive mode", also called when microphone is toggled.
##        print 'resetting oops grammar'
        # isActive = self.isActive()
        if self.isExclusive():
            print('oops, cancel exclusive mode')
            self.activateSet(['oops'], exclusive = 0)
        self.newWord = ''

# standard stuff Joel (adapted for possible empty gramSpec, QH, unimacro)
thisGrammar = ThisGrammar()
if thisGrammar.gramSpec:
    thisGrammar.initialize()
else:
    thisGrammar = None

def logToFile(line):
    """logging !
    """
    if not logFile:
        getLogFileName()
    if not logFile:
        print('_oops, logging: cannot find valid name for logFile')
        return
    sock = open(logFile, 'a')
    if not line.endswith('\n'):
        line += '\n'
    sock.write(line)
    sock.close()

def changeCallback(type,args):
    # not active without special version of natlinkmain:
    if ((type == 'mic') and (args=='on')):
        return   # check WAS in natlinkmain...
    if thisGrammar:
        thisGrammar.cancelMode()

def unload():
    #pylint:disable=W0603
    global thisGrammar
    if thisGrammar:
        thisGrammar.unload()
    thisGrammar = None


