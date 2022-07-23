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
# _control.py, adapted version of_gramutils.py
# Author: Bart Jan van Os, Version: 1.0, nov 1999
# starting new version Quintijn Hoogenboom, August 2003
"""Grammar that controls/shows/traces state of other grammars


"""
import os
import sys
import re
import pickle

import natlink
from natlink.natlinkutils import *
from dtactions.unimacro import unimacroutils
import unimacro.natlinkutilsbj as natbj
from natlinkcore import natlinkutils
from dtactions.unimacro import unimacroutils
import D_

# extra commands for controlling actions module:
try:
    actions = __import__('actions')
except ImportError:
    actions = None
    print('warning: actions module not imported')

tracecount = list(map(str, list(range(1, 10))))



#Words that are 'filtered out' (actually: removed) in Filter Mode
#See below for the different modes
def ReadFilteredWords(Filename):
#reads all words from the Filtered words file    
#does not really belong here
    try:
        File=open(Filename,'r')
    except:
        return []
    Words = File.readlines()
    File.close
    for w in Words:
        Words[Words.index(w)]=w[:-1]
    freq={}        
    for w in Words:
        if w in freq:
            freq[w]=freq[w]+1
        else:
            freq[w]=1
    Words=list(freq.keys())
    return Words

FilteredWords = ['in','the','minimum','to','and','end','a','of','that','it',
                 'if', 'its', 'is', 'this', 'booth', 'on', 'with',"'s"]
#(taken from natlinkmain, to prevent import:)
baseDirectory = unimacroutils.getUnimacroUserDirectory()
FilterFileName=baseDirectory+'\\filtered.txt'
FilteredWords=natbj.Union(FilteredWords, ReadFilteredWords(FilterFileName))


#Constants for the UtilGrammar
Normal=0
Training=1 #obsolete
Command=2 #obsolete
Filter=4
FilterTraining=5
Display=6


showAll = 1  # reset if no echo of exclusive commands is wished
voicecodeHome = None
if 'VCODE_HOME' in os.environ:
    voicecodeHome = os.environ['VCODE_HOME']
    if os.path.isdir(voicecodeHome):
        for subFolder in ('Admin', 'Config', 'Mediator'):
            newFolder = os.path.join(voicecodeHome, subFolder)
            if os.path.isdir(newFolder) and newFolder not in sys.path:
                sys.path.append(newFolder)
                print('appending to sys.path: %s'% newFolder)
    else:
        print('_control: VCODE_HOME points NOT to a directory: %s'% voicecodeHome)
        voicecodeHome = None
        

ancestor = natbj.IniGrammar
class UtilGrammar(ancestor):
    language = unimacroutils.getLanguage()
    iniIgnoreGrammarLists = ['gramnames', 'tracecount', 'message'] # are set in this module

    name = 'control'
##    normalSet = ['show', 'edit', 'trace', 'switch', 'message']
##    exclusiveSet = ['showexclusive', 'message']
    # commands for controlling module actions
    if actions:
        actionName = "| actions"
    else:
        actionName = ""
        
    gramSpec = """
<show> exported = show ('all grammars' | 
                        ([grammar|inifile] {gramnames}) 
                         """+actionName+""");
<edit> exported = edit ([grammar|inifile] {gramnames}"""+actionName+""");
<trace> exported = trace [on|off| {tracecount}]
              ('all grammars' | [grammar] {gramnames}"""+actionName+""") [on|off| {tracecount}] ;
<switch> exported = switch [on|off]
              ('all grammars' | [grammar] {gramnames})[on|off];
<voicecode> exported = 'switch on voicecode';
<showexclusive> exported = show exclusive [grammars];
<resetexclusive> exported = reset exclusive [grammars];
<message> exported = {message};
    """

    Mode = Normal
    LastMode = Normal
    CurrentWord = 0
    Repeat = 0

    def initialize(self):
        global loadedNames
        if not self.load(self.gramSpec, allResults=1):
            return None
        natbj.RegisterControlObject(self)
        self.emptyList('message')
        self.emptyList('gramnames')
        self.setList('tracecount', tracecount)
        self.activateAll()
        self.setMode(Normal)
        self.doMessages = None
        self.startExclusive = self.exclusive # exclusive state at start of recognition!
##        if unimacroutils.getUser() == 'martijn':
##            print 'martijn, set exclusive %s'% self.name
##            self.setExclusive(1)

    def unload(self):
        natbj.UnRegisterControlObject(self)
        ancestor.unload(self)

    def gotBegin(self, moduleInfo):
        #Now is the time to get the names of the grammar objects and
        # activate the list for the <ShowTrainGrammar> rule
        if natbj.grammarsChanged:
##            print 'new list for control: %s'% natbj.loadedGrammars.keys()
            self.setList('gramnames', list(natbj.loadedGrammars.keys()))
            natbj.ClearGrammarsChangedFlag()
        if self.checkForChanges:
            self.checkInifile()
            
        self.startExclusive = self.exclusive # exclusive state at start of recognition!

    def gotResultsInit(self,words,fullResults):
        if self.mayBeSwitchedOn == 'exclusive':
            print('recog controle, switch off mic: %s'% words)
            natbj.SetMic('off')
        if self.exclusive and self.doMessages:
            self.DisplayMessage('<%s>'% ' '.join(words))

    def resetExclusiveMode(self):
        """no activateAll, do nothing, this grammar follows the last unexclusive grammar
        """
        pass
    
    def setExclusiveMode(self):
        """no nothing, control follows other exclusive grammars
        """
        pass
    
    def gotResultsObject(self,recogType,resObj):
        if natbj.IsDisplayingMessage:
            return
        if self.doMessages:
            mes = natbj.GetPendingMessage()
            if mes:
                mes = '\n\n'.join(mes)
                natbj.ClearPendingMessage()
                self.DisplayMessage(mes)
                return
            unimacroutils.doPendingBringUps()  # if there were

        if self.startExclusive and self.exclusive and showAll:
            # display recognition results for exclusive grammars
            # with showAll = None (in top of this file), you can disable this feature
            if recogType == 'reject':
                URName = ''
                exclGram = natbj.exclusiveGrammars
                exclGramKeys = list(exclGram.keys())
                if len(exclGramKeys) > 1 and self.name in exclGramKeys:
                    exclGramKeys.remove(self.name)
                if len(exclGramKeys) > 1:
                    URName = ', '.join(exclGramKeys)
                k = exclGramKeys[0]
                v = exclGram[k]
                # UE stands for unrecognised exclusive:
                # if more exclusive grammars,
                # the last one is taken
                URName = URName or v[2]   # combined name or last rule of excl grammar
                if self.doMessages:
                    self.DisplayMessage('<'+URName+': ???>', alsoPrint=0)

    #Utilities for Filter Modes and other special modes
    def setMode(self,NewMode):
        self.LastMode = self.Mode
        self.Mode = NewMode

    def restoreMode(self):
        self.Mode = self.LastMode
        
    def gotResults_trace(self,words,fullResults):
        print('control, trace: %s'% words)
        if self.hasCommon(words, 'actions'):
            if self.hasCommon(words, 'show'):
                actions.debugActionsShow()
            elif self.hasCommon(words, 'off'):
                actions.debugActions(0)
            elif self.hasCommon(words, 'on'):
                actions.debugActions(1)
            elif words[-1] in tracecount:
                actions.debugActions(int(words[-1]))
            else:
                actions.debugActions(1)


    def gotResults_voicecode(self,words,fullResults):
        """switch on if requirements are fulfilled

        voicecodeHome must exist
        emacs must be in foreground
        """
        wxmed = os.path.join(voicecodeHome, 'mediator', 'wxmediator.py')
        if os.path.isfile(wxmed):
            commandLine = r"%spython.exe %s > D:\foo1.txt >> D:\foo2.txt"% (sys.prefix, wxmed)
            os.system(commandLine)
        else:
            print('not a file: %s'% wxmed)
            
        

        
    def gotResults_switch(self,words,fullResults):
        print('control, switch: %s'% words)
        if self.hasCommon(words, 'on'):
            func = 'switchOn'
        elif self.hasCommon(words, 'off'):
            func = 'switchOff'
        else:
            try:
                t = {'nld': '<%s: ongeldig schakel-commando>'% self.GetName()}[self.language]
            except:            
                t = '<%s: invalid switch command>'% self.GetName()
            if self.doMessages:
                self.DisplayMessage(t)
            return
        if self.hasCommon(words, 'all grammars'):
            print('%s all grammars:'% func)
            natbj.CallAllGrammarObjects(func, ())
            print("-"*10)
        else:
            gramname = self.hasCommon(words, list(natbj.loadedGrammars.keys()))
            if gramname:
                gram = natbj.loadedGrammars[gramname]
                gram.callIfExists(func, ())
            else:
                print('no grammar name found: %s'% gramname)
            
    def gotResults_showexclusive(self,words,fullResults):
        if natbj.exclusiveGrammars:
            T = ['exclusive grammars:']
            for e in natbj.exclusiveGrammars:
                T.append(e)
            T.append(self.name)
            if self.doMessages:
                self.DisplayMessage(' '.join(T))
        else:
            if self.doMessages:
                self.DisplayMessage('no exclusive grammars')
            

    def gotResults_resetexclusive(self,words,fullResults):
        print('reset exclusive')
        if natbj.exclusiveGrammars:
            T = ['exclusive grammars:']
            for e in natbj.exclusiveGrammars:
                T.append(e)
            T.append(self.name)
            T.append('... reset exclusive mode')
            if self.doMessages:
                self.DisplayMessage(' '.join(T))
            natbj.GlobalResetExclusiveMode()
            unimacroutils.Wait(1)
            if self.doMessages:
                self.DisplayMessage('reset exclusive mode OK')
        else:
            if self.doMessages:
                self.DisplayMessage('no exclusive grammars')
        
##    def setExclusive(self, state):
##        """control grammar, do NOT register, set and maintain state
##
##        special position because of ControlGrammar
##        """
##        print 'control set exclusive: %s'% state
##        if state == None:
##            return
##        if state == self.exclusive:
##            return
##        print 'control, (re)set exclusive: %s'% state
##        self.gramObj.setExclusive(state)
##        self.exclusive = state

    def gotResults_show(self,words,fullResults):
        # special case for actions:
        if self.hasCommon(words, 'actions'):
            actions.showActions()
            return
        
        if natbj.exclusiveGrammars:
            print('exclusive (+ control) are: %s'% ' '.join(list(natbj.exclusiveGrammars.keys())))

        grammars = natbj.loadedGrammars
        gramNames = list(grammars.keys())
        gramName = self.hasCommon(words, gramNames)
        if gramName:
            grammar = grammars[gramName]
            if not grammar.onOrOff:
                # off, show message:
                self.offInfo(grammar)
                return
            if not self.hasCommon(words, 'grammar'):
                try:
                    grammar.showInifile()
                    return
                except AttributeError:
                    try:
                        grammar.showGrammar()
                        return
                    except AttributeError:
                        pass
        
        # now show the grammar in the browser application:      
        if gramName:
            name = [gramName]
        else:
            name = words[1:-1]
        
        if (len(name)>0) and (name[0]=='previous'):  #shortcut: show previously assembled grammar
            pypath = '.'
            for x in sys.path:
                pypath = pypath + ';' + x
            os.environ['PYTHONPATH'] = pypath
            AppBringUp('Browser',Exec=PythonwinExe,Args='/app BrowseGrammarApp.py')
        else:
            All=1
            if len(name)>0:
                All=self.hasCommon(words, 'all grammars')
                if self.hasCommon(words, ['all', 'active']):
                    name=name[1:]
            if len(name)>0:                
                Start=(' '.join(name),[])
            else:
                Start=()
            print('start browsing with: %s'% All)
            self.Browse(Start,All)
        

    def gotResults_edit(self,words,fullResults):
        # special case for actions:
        if self.hasCommon(words, 'actions'):
            actions.editActions()
            return

        grammars = natbj.loadedGrammars
        gramNames = list(grammars.keys())
        gramName = self.hasCommon(words[-1:], gramNames)
        if gramName:
            grammar = grammars[gramName]
            if self.hasCommon(words, 'grammar'):
                module = grammar.__module__
                filename = unimacroutils.getModuleFilename(module)
                #print 'open for edit file: %s'% filename
                self.openFileDefault(filename, mode="edit", name='edit grammar %s'% gramName)
                unimacroutils.setCheckForGrammarChanges(1)
            else:
                # edit the inifile
                try:
                    grammar.switchOn()
                    grammar.editInifile()
                except AttributeError:
                    if self.doMessages:
                        self.DisplayMessage('grammar "%s" has no method "editInifile"'% gramName)
                    return
        else:
            print('no grammar name found')


    def switchOff(self, **kw):
        """overload, this grammar never switches off

        """        
        print('remains switched on: %s' % self)

    def switchOn(self, **kw):
        """overload, just switch on

        """
        self.activateAll()


    def offInfo(self, grammar):
        """gives a nice message that the grammar is switched off

        Gives also information on how to switch on.

        """        
        name = grammar.getName()
        try:
            t = {'nld': ['Grammatica "%s" is uitgeschakeld'% name,
                         '', 
                         '"Schakel grammatica %s in" om te activeren'% name]}[self.language]
            title = {'nld': 'Grammatica %s'% name}[self.language]
        except KeyError:
            t = ['Grammar "%s" is switched off'% name,
                 '"Switch On Grammar %s" to activate'% name]
            title = 'Grammar %s'% name
        if natbj.loadedMessageGrammar:
            t = ';  '.join(t)
            if self.doMessages:
                self.DisplayMessage(t)
        else:
            actions.Message(t)

class MessageDictGrammar(natlinkutils.DictGramBase):
    def __init__(self):
        natlinkutils.DictGramBase.__init__(self)

    def initialize(self):
        print('initializing/loading DictGrammar!!')
        self.load()
        natbj.RegisterMessageObject(self)

    def unload(self):
        natbj.UnRegisterMessageObject(self)
        natlinkutils.DictGramBase.unload(self)
        
    def gotResults(self, words):
##        pass
        print('messageDictGrammar: heard dictation:  %s '% words)


# standard stuff Joel (adapted for possible empty gramSpec, QH, unimacro)
messageDictGrammar = MessageDictGrammar()
messageDictGrammar.initialize()
print('messageDictGrammar initialized')


# standard stuff Joel (adapted for possible empty gramSpec, QH, unimacro)
utilGrammar = UtilGrammar()
if utilGrammar.gramSpec:
    utilGrammar.initialize()
else:
    print('grammar _control has no specification for this language---------')
    utilGrammar = None

def unload():
    global utilGrammar, messageDictGrammar
    if utilGrammar: utilGrammar.unload()
    utilGrammar = None
    if messageDictGrammar:
        messageDictGrammar.unload()
    messageDictGrammar = None
    
def changeCallback(type,args):
    global utilGrammar
    # Whenever the mic is turned off, the intercept mode is turned off.
    # and any special modes, except training
    if ((type == 'mic') and (args=='on')):
        return   # check WAS in natlinkmain...
    natbj.GlobalResetExclusiveMode()
    if utilGrammar:    
        utilGrammar.setMode(Normal)
        #This could be done anywhere, but not within natlinkutilsbj
        #Because that module is 'imported from'.
        if utilGrammar.interceptMode:
            CallAllGrammarObjects('setInterceptMode',[0])
        
        
    
