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
# natlinkutilsbj.py
#   This file contains utility classes and functions for grammar files.
#   Author: Bart Jan van Os; november 1999, adapted for
#   unimacro-project.
#   See the class BrowsableGrammar for documentation on the use of
#   the Grammar browser.
#   revised many times by Quintijn Hoogenboom
#pylint:disable=C0302, C0116, W0702, W0201, W0703, R0915, R0913, W0613, R0912, R0914, R0902, C0209, W0602, W0212
#pylint:disable=E1101

"""subclasses classes for natlink grammar files and utility functions

"""
import sys
import os
import os.path
import pickle
import glob
import time
import re
import shutil
import copy
import string
from pathlib import Path
import logging
from logging import Logger
import win32com
import natlink
from natlinkcore import loader
from natlinkcore import gramparser # for translation with GramScannerReverse
from natlinkcore import natlinkstatus
from natlinkcore import natlinkutils
from natlinkcore import readwritefile

# for IniGrammar:
# was natlinkutilsqh:
from dtactions import unimacroutils
from dtactions import unimacroactions as actions
from dtactions.unimacroactions import doAction as action
from dtactions.unimacroactions import doKeystroke as keystroke
from dtactions.unimacroactions import UnimacroBringUp
from dtactions import utilsqh
from dtactions.utilsqh import formatListColumns
from dtactions import inivars
from dtactions.sendkeys import sendsystemkeys

from unimacro import BrowseGrammar
from unimacro import D_

from unimacro import spokenforms # for numbers spoken forms, IniGrammar (and also then DocstringGrammar)
from unimacro import logname
import types
from functools import wraps

status = natlinkstatus.NatlinkStatus()
natlinkmain = loader.NatlinkMain()

# for translating the gramSpec in inigrammars:
reGrammarKeywords = re.compile(r"""
          (?<!{|<)        # not a { or a < before the string
          (\b[a-z]+\b|    # a whole word (only a-z)
          (?P<quote>['"])[a-z -]+(?P=quote))    # or 'more words' or "more words"
          (?!>|})         # not a > or a } after the string
          """, re.IGNORECASE+re.VERBOSE)
reSplitComments = re.compile(r"(#.*$)", re.MULTILINE)   # # through end of line

# boundaries for setList functions below:
grammarListLengthWarning = 150
grammarListLengthMaximum = 300

# difficult recognised counts:
# used in grammar tasks and firefox_browsing:
spokenFormCounts = {'nld': {'12': "twaalf"}}



class UnimacroError(Exception):
    """UnimacroError"""
# # personal use: find out on what machine we are
# def GetID():
#     if 'ID' in os.environ:
#         return os.environ['ID'].lower()
#     else:
#         return ''

# can be switched off:
automaticOpenFile = 1  # leave on!!
notifyIniErrors = 1 

# parameters for DisplayMessage
maxDisplayMessage = 75   # if messages longer, display in msgboxconfirm popup
DisplayMessageForbiddenCharacters = '\n\\~' # newline, backslash, tilde

# If you do not have DragonDictate running alongside, set the next
# constant to zero
DDIsRunning=0
LastMouseX=0
LastMouseY=0
NaturalTextKey='{NumKey/}'
CorrectDlgKey='{NumKey-}'
DragonBarKey='{NumKey*}'   

# for search (in _general and _genericmovement)
lastSearchText = ''
lastSearchDirection = ''
beforeOrAfter = None  # valid values 'for', 'before', 'after'

## this should all go to unimacroactions!!
app = None # special apps for search
appProgram = ''  
sheet = ''  # for excel
doc= ''    # for word
comingFrom = ''

# special for UltraEdit32:
UEdit = None
uepath = r'C:\Program Files\UltraEdit\UEdit32.exe'
if os.path.isfile(uepath):
    UEdit = uepath
    print('use UltraEdit32 for textual files open')# special for UltraEdit32:

def changeInList(L, old, new):
    """change in place"""
    if old in L:
        L.remove(old)
    L.append(new)

def getICAlphabet(language=None):
    """get the radio alphabeth, possibly with language changes
    when inserting "dummy" for old, a extra letter is added

    """
    A = D_.ICAlphabet[:]
    if language == 'nld':
        changeInList(A, 'a\\alpha', 'a\\alfa')
        changeInList(A, 'j\\juliet', 'j\\juliett')
        changeInList(A, 'x\\xray', 'x\\x-ray')
        #A = map(letterUppercase, A)
    return A

def getICAlphabetDict(language=None):
    """get the radio alphabeth, possibly with language changes
    when inserting "dummy" for old, a extra letter is added

    """
    A = getICAlphabet(language=language)
    if language == 'nld':
        changeInList(A, 'a\\alpha', 'a\\alfa')
        changeInList(A, 'j\\juliet', 'j\\juliett')
        changeInList(A, 'x\\xray', 'x\\x-ray')
        #A = map(letterUppercase, A)
    D = {}
    for k in A:
        wr, sp = k.split('\\')
        D[sp.strip()] = wr.strip()
    return D
    
def letterUppercase(l):
    r"""turns a\alpha into a\Alpha"""
    L = l.split('\\')
    written, spoken = L[0], L[1].capitalize()
    return f'{written}\\{spoken}'

dataDirectory = status.getUnimacroDataDirectory()

GrammarFileName = os.path.join(dataDirectory, 'grammar.bin')
for somePath in sys.path:
    files = glob.glob(somePath + '\\pythonwin.exe')
    if files:
        # print("pythonwin.exe: %s"% files)
        PythonwinExe=files[0]
        break
else:
    print('warning: no PythonwinExe found')
    
PythonwinPath, dummy = os.path.split(PythonwinExe)
PythonServerExe=os.path.join(PythonwinPath, 'pserver1')

# returns the union of two lists
def Union(L1,L2) -> list:
    """old fashioned union function of two lists
    """
    return list(set(L1).union(L2))

# returns the intersection of two lists
def Intersect(L1,L2):
    """old fashioned intersection function of two lists
    """
    return set(L1).intersection(L2)

def reverseDict(Dict : dict):
    """reverse a dict, ignoring multiple values of the original
    """
    return {val: key for (key, val) in Dict.items()}

def joinNestedStringLists(l):
    """nested lists of strings are "flattened" into one string
    
    so a sort of super ' '.join(...)
    """
    output = []
    for sub in l:
        if isinstance(sub, list):
            output.append(joinNestedStringLists(sub))
        else:
            output.append(sub)
    return ' '.join(output)

def getAllWords(fullResults):
    """get all words from the fullResults of a recognition
    """
    return list((word for (word, _rule) in fullResults))

def ActivateDragonBarMenu():
    """activate the DragonBar"""
    sendsystemkeys("{NumKey-}")        

def SetMic(state):
    """switch on or off the microphone
    
    we avoid error messages, when turning the mic on while the device
    is still busy.
    """
    #pylint:disable=W0702, E1101
    try:
        natlink.setMicState(state)
    except :
        pass

 



class StaticProperty:
    """A custom descriptor that allows  access as a static property."""
    def __init__(self, func):
        self.func = func

    def __get__(self, instance, owner):
        return self.func()



#avoid copy and pasting methods that delegate to the logger.  
def _delegate_to_logger(method_name):
    """Delegates to {method} of a Logger object from self.logger_name()"""
    def fn(self,*args,**kwargs):
        logger=logging.getLogger(self.logger_name())
        method = getattr(logger,method_name)
        try:
            return method(*args,**kwargs)
        except Exception as e:
            return False
    return fn


GrammarXAncestor=natlinkutils.GrammarBase
class GrammarX(GrammarXAncestor):
    """first subclass of GrammarBase

      This is BJ's basic grammar class (Bart Jan van Os).
      
      It redefines some methods such that always self.setExclusive is used to
      change the exclusive state.
      setExclusive is extended to keep track of the current exclusive state.
      It also registers itself and unregisters itself to accomodate the
      CallAllGrammarObjects function.
      It also has the method DisplayMessage to display text in the results box, IF
      the module _control (including a MessageDictationGrammar)
      is available in the User directory of natpython

    """
    #pylint:disable=R0904, C0116
    __inherited=GrammarXAncestor
    allGrammarXObjects = {}
    GrammarsChanged = set()   # take last item just True!
    LoadedControlGrammars = set()


    def __new__(cls):
        
        #delegate some of the logging functions.
    
        #copy and paste do we get hints
        #There may be a better way using decorators.

        obj = super().__new__(cls)


        obj.info=types.MethodType(_delegate_to_logger("info"),obj)  
        obj.setLevel=types.MethodType(_delegate_to_logger("setLevel"),obj)
        obj.debug=types.MethodType(_delegate_to_logger("debug"),obj)
        obj.warning=types.MethodType(_delegate_to_logger("warning"),obj)
        obj.error=types.MethodType(_delegate_to_logger("error"),obj)
        obj.exception=types.MethodType(_delegate_to_logger("exception"),obj)
        obj.critical=types.MethodType(_delegate_to_logger("critical"),obj)
        obj.log=types.MethodType(_delegate_to_logger("log"),obj)
        return obj
    
    def __init__(self):
        

        self.__inherited.__init__(self)
        # set in list of allUnimacroGrammars, also when not loaded into
        self.RegisterGrammarObject()
        self.inGotBegin = 1 # initialise behave like being there
        self.mayBeSwitchedOn = 1
        # self.isActive = 0 # now user isActive() from GrammarBase
        self.language = status.get_language()
        self.version = status.getDNSVersion()
        self.exclusive = 0
        # self.name = ""
        self.want_on_or_off = None   # True: on False: off None: no decision
        self.hypothesis = 0
        self.allResults = 0
   
    def getExclusiveGrammars(self):
        """return the dict of (name, grammarobject) of GrammarX objects that are exclusive
        """
        G = {name: gram for name, gram in self.allGrammarXObjects.items() if gram.isExclusive()}
        return G

    def getUnimacroGrammars(self):
        """get from allGrammarXObjects the name: grammarobj dict of all Unimacro grammars
        """
        return  {grammarobj.getName(): grammarobj for _objname, grammarobj in self.allGrammarXObjects.items()}

    def RegisterGrammarObject(self):
        self.allGrammarXObjects[self.getName()] = self
        self.GrammarsChanged.add(True)

    def UnregisterGrammarObject(self):
        """calling at unload time"""
        if self.LoadedControlGrammars and self in self.LoadedControlGrammars:
            self.LoadedControlGrammars.pop()
        try:
            del self.allGrammarXObjects[self.name]
        except KeyError:
            if self.name == self.module_name:
                print(f'cannot unregister unimacro grammar {self.module_name}')
            else:
                print(f'cannot unregister unimacro grammar {self.module_name}, name: {self.name}')
                
        # self.GrammarsChanged.append(True)

    def SetGrammarsChangedFlag(self):
        self.GrammarsChanged.add(True)
        print(f'GrammarsChanged: {self.GrammarsChanged}')   ## seems not to work TODO QH:
    def GetGrammarsChangedFlag(self):
        if self.GrammarsChanged:
            return self.GrammarsChanged.pop()
        return False
    def ClearGrammarsChangedFlag(self):
        self.GrammarsChanged.clear()

    def CallAllGrammarObjects(self, funcName, args):
        """calls a function through all grammar objects
    
        funcName should be a string with the function name
        args should be a tuple of arguments, can be empty tuple ()
        exits silently if function doesn't exist in a grammar
    
        """    
        if args and len(args) == 1 and isinstance(args[0], tuple):
            args = args[0] # in order to be able to give arguments "loose" in the call instead of
                           # in a explicit tuple: CAGO(func, a, b, c) instead of
                           #                      CAGO(func, (a, b, c))
        for name, grammar in list(self.allGrammarXObjects.items()):
            if not grammar.isLoaded():
                # only loaded grammars...
                continue
            try:
                func = getattr(grammar, funcName)
            except AttributeError:
                print('func not found for %s'% name)
            func(*args)

    def GetGrammarObject(self, grammarName):
        """return the grammar object, if in correct dict, by user name
        """
        if grammarName in self.allGrammarXObjects:
            return self.allGrammarXObjects[grammarName]
        return None

    def ControlResetExclusiveGrammar(self):
        """resets the exclusive flag of the _control grammar
    
        If the exclusive state of a/the last grammar is reset (becoming
        non-exclusive again), the grammar _control.
        """    
        exclGr = self.getExclusiveGrammars()
        if not exclGr:
            return
        if len(exclGr) > 1:
            return
        for gram in exclGr.values():
            if gram in self.LoadedControlGrammars:
                gram.setExclusive(0)
            
    def RegisterControlObject(self, gramobj):
        """keep this (control grammar) in a special variable
        """
        self.LoadedControlGrammars.add(gramobj)

    def UnregisterControlObject(self):
        """clear this (control grammar) in a special variable
        """
        self.LoadedControlGrammars.clear()
                
    def ControlSetExclusiveGrammar(self, value):
        """sets the exclusive flag of the _control grammar if another grammar is also exclusive
        
        In this way, the commands of the _control grammar remain accessible when
        other (Unimacro) grammars are exclusive
        """
        exclGr = self.getExclusiveGrammars()
        if not exclGr:
            return
        if not self.LoadedControlGrammars:
            return
        for control_grammar in self.LoadedControlGrammars:
            control_grammar.setExclusive(value)


    def getRegisteredGrammarNames(self):
        return list(self.allGrammarXObjects.keys())

    def getPrimaryAncestor(self):
        # the default primary ancestor is the first baseclass
        return self.__class__.__bases__[0] 


    def load(self,gramSpec,allResults=0,hypothesis=0, grammarName=None):
        
        if gramSpec:
            success = self.__inherited.load(self,gramSpec,allResults,hypothesis, grammarName=grammarName)
            return success
        return None
    
    def __str__(self):
        return '<grammarx: %s>'% self.GetName()

    def unload(self):
        self.UnregisterGrammarObject()
        if self in self.LoadedControlGrammars:
            self.UnregisterControlObject()
        self.__inherited.unload(self)

    def beginCallback(self, moduleInfo):
        """overload from GrammarBase, does nothing if grammar is switched off

        """
        # intercept here if grammar is switched off, or inside displaying message
        if self.mayBeSwitchedOn:
            # onOrOff = what the user wants
            # onOrOffState = the actual state.
            # if one of both is not False, gotBegin should cope with that
            # otherwise gotBegin can be skipped
            self.inGotBegin = 1
            self.callIfExists("gotBegin", (moduleInfo,) )
            self.inGotBegin = 0
            self.status = 'ready'

    def hypothesisCallback(self, words):
        # intercept here if grammar is switched off, or inside displaying message
        # when is this used?
        if self.mayBeSwitchedOn:
            self.callIfExists( "gotHypothesis", (words,) )

    def resultsCallback(self, wordsAndNums, resObj):
        self.__inherited.resultsCallback(self, wordsAndNums, resObj)

    # This is a utility function.  It calls a member function if and only
    # if that member function is defined.



    def getName(self):
        """ 
        A unimacroGrammar should have a name, returned by getName.  Default is to use a name property.  
        """
        return self.name
    
    def logger_name(self):
        """
            A unimacro grammar should provide a logger name.  The default is the module
            name, override logger_name for other behavior (like a special string or a __class__ etc.)
        """
        return self.__module__  #this will pick up the module the subclass instance was created.

    GetName = getName   # consistency with Bart Jan

    # These methods are adapted to keep track of the exclusive state.
    # They DO NOT intercept setExclusive! Bart Jan, I chose for calling once   QH11082003
    
    # but effectively call setExclusive twice to ensure original behaviour
    # under changing natlinkutils.
    def activate(self, ruleName, window=0, exclusive=None, noError=0):
        self.__inherited.activate(self, ruleName, window, noError=noError)
        if exclusive is not None:
            self.setExclusive(exclusive)

    def deactivate(self, ruleName, noError=0, dpi16trick=True):
        self.__inherited.deactivate(self, ruleName, noError)
        # if not self.activeRules:
        #     self.isActive = 0
            

    def activateSet(self, ruleNames, window=0, exclusive=None):
        self.__inherited.activateSet(self, ruleNames, window)
        # if not ruleNames:
        #     # self.deactivateAll()
        #     self.isActive = 0
        # else:
        #     self.isActive = 1
        if exclusive is not None:
            self.setExclusive(exclusive)

    def activateAll(self, window=0, exclusive=None, exceptlist=None):
        self.__inherited.activateAll(self, window, exceptlist=exceptlist)
        # self.isActive = 1
        if exclusive is not None:
            self.setExclusive(exclusive)

    def deactivateAll(self):
        self.__inherited.deactivateAll(self)
        # self.isActive = 0
        self.setExclusive(0)

    # used by GlobalResetExclusiveMode

    def resetExclusiveMode(self):
        # overload if normalSet is wanted:
        try:
            self.setExclusive(0)
        except natlink.NatError as t:
            print('no resetExclusiveMode for %s: %s'% (self.name, t))

    def setExclusiveMode(self):
        """overload if special sets are wanted"""
        self.setExclusive(1)

    def setExclusive(self,exclusive):
        """let ControlGrammar follow exclusiveness

        state is maintained in self.exclusive
        """
        #pylint:disable=
        if exclusive is None:
            return
        if exclusive == self.exclusive:
            return
        self.__inherited.setExclusive(self,exclusive)
        self.exclusive = exclusive
        
        
        ## check this, QH TODO
        if self.LoadedControlGrammars:
            if self in self.LoadedControlGrammars:
                # no extra setting if self is _control
                return
            self.ControlSetExclusiveGrammar(exclusive)
       

    def cancelMode(self):
        """overload for grammars that can go exclusive"""
        return

    def switchOnOrOff(self, **kw):
        # print(f'{self.name}, switchOnOrOff')
        allResults = kw.get('allResults', 0)
        hypothesis = kw.get('hypothesis', 0)
        grammarName = kw.get('grammarName', self.name)
        if not self.isLoaded():
            may_be_loaded = self.ini.getBool('general', 'initial on', False)
            if may_be_loaded:
                self.load(self.gramSpec, allResults=allResults, hypothesis=hypothesis, grammarName=grammarName)
            else:
                print(f"\t{self.name}: grammar is not loaded (inactive)")    
                return
        if self.want_on_or_off is None:
            if self.mayBeSwitchedOn:
                # print(f'switch on: {self.name}')
                self.switchOn(**kw)
            else:
                if self.isActive():
                    self.switchOff()
        elif self.want_on_or_off is True:
            self.switchOn(**kw)
        elif self.want_on_or_off is False:
            self.switchOff()
        else:
            raise ValueError(f'grammar {self.name}, invalid value for want_on_or_off: {self.want_on_or_off}')
            
    def switchOn(self, **kw):
        """switches grammar on, activates all rules

        must be overloaded if more specific behaviour is wished
        
        For application specific grammars, window should be passed,
        the window handle, coming in as moduleInfo[2] in gotBegin.
        (so: something like
        winHndle = moduleInfo[2]
        (...)
        switchOnOrOff(window=winHndle)
        )
        
        force = 1: set mayBeSwitchedOn
        
        Can pass activateSet for activating a set of rules (list or tuple) or
                 activateRule for activating one rule (string)
        
        """
        #pylint:disable=R0911, R0912
        if 'force' in kw:
            if kw['force']:
                self.mayBeSwitchedOn = 1
            del kw['force']
        if self.mayBeSwitchedOn:
            if not self.is_loaded:
                self.load(self.gramSpec, allResults=self.allResults, hypothesis=self.hypothesis, grammarName=self.name)
        if 'activateSet' in kw:
            activeSet = kw['activateSet']
            if self.mayBeSwitchedOn:
                del kw['activateSet']
                if isinstance(activeSet, list):
                    self.activateSet(activeSet, **kw)
                elif isinstance(activeSet, tuple):
                    self.activateSet(list(activeSet), **kw)
                    return 1
                else:
                    print('natlinkutils, switchOn: invalid type for activateSet %s (%s)'% (activeSet, type(activeSet))) 
                    return None
            else:
                print('mayBeSwitchedOn False (%s), not switched on: %s'% (self.mayBeSwitchedOn, self.getName()))
                return None
        if 'activateRule' in kw:
            rule = kw['activateRule']
            del kw['activateRule']
            if self.mayBeSwitchedOn:
                window = kw.get('window', 0)
                exclusive = kw.get('exclusive', None)
                noError = kw.get('noError', 0)
                self.activate(rule, window=window, exclusive=exclusive, noError=noError)
                return 1
            print('mayBeSwitchedOn False (%s), not switched on: %s'% (self.mayBeSwitchedOn, self.getName()))
            return None
        if self.mayBeSwitchedOn:
            if kw:
                print(f'{self.name}, switch rules, kw: {kw}')
            # else:
            #     print(f'{self.name}, switch on all rules')
            self.activateAll(**kw)
            return 1
        # else:
        print('mayBeSwitchedOn False (%s), not switched on: %s'% (self.mayBeSwitchedOn, self.getName()))
        return None

    def switchOff(self, **kw):
        """switches grammar off, deactivates all rules

        must be overloaded if more specific behaviour is wished
        """
        #pylint:disable=
        force = kw.get('force')
        if force:
            self.mayBeSwitchedOn = 0
        if self.is_loaded:
            self.unload()
        return 1
    
    def DisplayMessage(self, mess):
        """display as a message
        
        This was with the DisplayMessage grammar trick,
        a recognition without effect, but showing in the recognition window.
        Maybe could be restored some time...
        """
        self.message(mess)

    def message(self, mess):
        """only print to Messages window
        """
        print(mess)

    # progress report
    def IProgressReport(self,Case,TotalCases,NPeriods):
        Period=round(TotalCases/NPeriods)
        if (Case%Period==0) or (Case==TotalCases) or (Case==1):
            self.DisplayMessage('%3.0f%% Done' % round(100.0*Case/TotalCases))

    def onTrayIcon(self, message):
        """needs this call when from actions the systemtray is called and clicked on

        see for example in _repeat"""
##        print 'caught onTrayIcon: %s'% repr(message)
        natlink.setTrayIcon()
        self.cancelMode()        

    def Wait(self, Time):
        """wait with the timer callback

        does not work when called from an action...
        
        """
        time.sleep(Time)

    def wait(self, multiple=1):
        """wait a multiple of default times (default 0.1)
        """
        wTime = multiple * 0.1
        if wTime > 0:
            if wTime > 2:
                print('waiting %s seconds'% wTime)
            self.Wait(wTime)
        else:
            print('no real wait, time is: %s'% wTime)
##        # not succeed:::::
##        if Time > 5:
##            raise ValueError("self.Wait too long to respond (should be given in seconds): %s"% time)
##        self.didWait = 0
##        print 'starting with: %s'% Time
##        natlink.setTimerCallback(self.WaitOnce, int(Time*1000.0))
##        times = 0
##        while 0 <= self.didWait < 5 and times < 5:
##            times += 1
##            print 'sleeping, self.didWait: %s'% self.didWait
##        natlink.setTimerCallback(None)
##        print 'end of wait: %s'% getattr(self, 'interrupted', 0)
##            
##        
##    def WaitOnce(self):
##        """stop waiting again"""
##        print 'self.didWait: %s'% self.didWait
##        interrupted = getattr(self, 'interrupted', 0)
##        if self.didWait > 10 or interrupted:
##            print 'stopping: %s, %s'% (self.didWait, interrupted)
##            self.didWait = -1
##            natlink.setTimerCallback(None)
##        self.didWait += 1

#---------------------------------------------------------------------------


BrowsableGrammarAncestor=GrammarX
class BrowsableGrammar(BrowsableGrammarAncestor):
    """BrowsableGrammar

       Class to support grammar browsing.
       It redefines some methods, such that copies of the used lists are
       being made.
       It has additional methods to support grammar browsing.
       It redefines resultsCallback to support an intercept mode:
       the grammar rules are recognized,
       but no callbacks are made, accept a call to gotInterceptedResults.
       That method displays the name of the grammar object and the rules used.
       => now in the browser.
    """
    #pylint:disable=W0201
    __inherited=BrowsableGrammarAncestor
    def __init__(self):
        self.__inherited.__init__(self)

    def load(self,gramSpec,allResults=0,hypothesis=0, grammarName=None):
        success = self.__inherited.load(self,gramSpec,allResults,hypothesis, grammarName=grammarName)
        if success:
            if isinstance(gramSpec, str):
                self.gramSpec=[gramSpec]
            else:
                self.gramSpec = gramSpec
            self.interceptMode = 0
            self.Lists={}
            for l in self.validLists:
                self.Lists[l]=[]
        return success

    def __str__(self):
        return '<browsablegr: %s>'% self.GetName()

    def switchOn(self, **kw):
        return self.__inherited.switchOn(self, **kw)

    def switchOff(self, **kw):
        return self.__inherited.switchOff(self, **kw)

    #The following two methods are redefined to keep a copy of the used lists
    def emptyList(self, listName):
        self.__inherited.emptyList(self,listName)
        self.Lists[listName]=[]

    def appendList(self, listName, words):
        """together with emptyList this is the setList command
        
        also check for long lists, > 150, warning, > 300 forbid
        QH, march 2013/november 2018
        """
        #pylint:disable=R0912
        if listName in self.Lists:
            lenone = len(self.Lists[listName])
        else:
            lenone = 0
        # if type(words) != types.ListType:
        #     print 'appendList %s, type: %s'% (listName, type(words))
        if isinstance(words, str):
            lentwo = 1
            words = [words]
        elif isinstance(words, list):
            lentwo = len(words)
        else:
            # assume list like object:
            words = list(words)
            lentwo = len(words)

        # may become a smaller list if grammarListLengthMaximum is exceeded:
        _wordsToAppend = list(words)
    
        if lenone + lentwo > grammarListLengthMaximum:
            if lenone:
                if lenone < grammarListLengthMaximum:
                    newAllowed = grammarListLengthMaximum - lenone
                    print('appendList: can only append %s items (out of %s) to grammar list: "%s"'% (newAllowed, lentwo, listName))
                    _wordsToAppend = words[:newAllowed]
                else:
                    print('appendList: cannot anymore items (wanted %s) to grammar list: "%s", list already is at maximum size of %s'% \
                            (lentwo, listName, grammarListLengthMaximum))
                    return
            else:
                newAllowed = grammarListLengthMaximum
                print('appendList/setList: can only set %s items (out of %s) to grammar list: "%s"'% (newAllowed, lentwo, listName))
                _wordsToAppend = words[:newAllowed]
        elif lenone + lentwo > grammarListLengthWarning:
            if lenone:
                print('appendList, warning list becoming large: appending %s items to grammar list: "%s", new length: %s'% (lentwo, listName, lenone+lentwo))
            else:
                print('appendList/setList, warning list becoming large: setting %s items to grammar list: "%s"'% (lentwo, listName))

        # for i, w in enumerate(words):
        #     if type(w) == str:
        #         try:
        #             w = str(w)
        #         except UnicodeEncodeError:
        #             w = utilsqh.translatorBinary(w)
        #         words[i] = w
        self.__inherited.appendList(self, listName, words)
        self.Lists.setdefault(listName, []).extend(words)
        # print("listName: %s (%s)"% (listName, type(listName)))
        # print("list words: %s"% self.Lists[listName])
        # print("-----")


    # The next three methods implement the Intercept mode
    # for a 'Find Grammar' functionality.
    # Whenever InterceptMode is active, results are not transferred
    # to descendants, but are used to start the browser localized
    # to the recognized rules. Note that you do not need to set the
    # AllResults flag, because all grammars should be derived from this class.
    def setInterceptMode (self,Status):
        self.interceptMode = Status

    def gotInterceptedResults(self,words, fullResults):
        # Starts the browser with the intercepted results.
        # Note that it would be easy to make the browser only
        # display the CURRENT grammmar, but I prefer seeing all grammar.
        results = natlinkutils.convertResults(fullResults)
        if ' '.join(words) != 'Cancel This': #make sure one global grammar has this active!
            Start=(self.GetName(),list(results.keys()))
            self.Browse(Start,0)
        # probably obsolete:
        # CallAllGrammarObjects('setInterceptMode',[0])
        # if ' '.join(words)=='Cancel This':
        #     self.DisplayMessage('Canceled', alsoPrint=0)

    def resultsCallback(self, wordsAndNums, resObj):
        # see natlinkutils for documentation. This method is changed
        # to implement interceptMode.
        # Uses the original behavior whenever NOT in intercept mode.
        # also intercept when in display mode:
        if not self.interceptMode:
            self.__inherited.resultsCallback(self, wordsAndNums, resObj)
        else:
            # do nothing more if the recog results were not for this grammar
            if not isinstance(wordsAndNums, list):
                return

            # we first convert the passed array of word/ruleNumbers into an
            # array of word/ruleNames and an array of only words
            words = []
            fullResults = []
            for x in wordsAndNums:
                words.append( x[0] )
                fullResults.append( ( x[0], self.ruleMap[x[1]] ) )
            #BJ ADD :
            self.gotInterceptedResults(words, fullResults)
        

    def GetDictionaries(self):
        """Overload to define Dictionaries; used in the grammar browser.
        """
        # Suppose you have a rule with a variable part (List or enumeration
        # of alternatives), and the gotResults function uses a dictionary
        # that defines different actions to be taken, dependent on the variable
        # part: i.e. the variable part is used as the key value of the dictionary.
        # In such cases, it may be informative to display not only the
        # variable parts in the browser, but also the dictionary definitions.
        # You have to define the use of those dictionaries here.
        # The function should return one object, a map of all used dictionaries.
        # The key is either the rule name of the innermost rule
        # that uses the dictionary keys to define a (long) enumeration of
        # alternatives,
        #   <SomeRule> = [<RuleStart>] (""" + Dict.keys(.join()," | ")+""");
        # OR the name of the list used within the rule,
        # associated with the dictionary:
        #   <ListRule> = [<RuleStart>] {Authors};
        #   plus
        #   self.setList('Authors',AuthorDict.keys())
        # The value for each rule/list name is the actual dictionary.
        # For example:
        #Dictionaries = {
        #    'SomeRule': Dict,        
        #    'Authors': AuthorDict,
        #     }
        #The default is empty.
        Dictionaries = {}
        return Dictionaries


    def InsertGrammarData(self,Grammars,All=0, Exclusive=0):
        #Parses the grammar specification and adds results to Grammars
        Name=self.GetName()
        if Name=='UnknownGrammar':
            Name=Name+str(len(Grammars.Included))
        Dicts=self.GetDictionaries()
        try:
            for n in list(Dicts.keys()):
                if not isinstance(Dicts[n], dict):
                    print(Name+', '+n+': is not a dictionary')
        except:
            print(Name+': Error in dictionary definitions')
        # print 'gramSpec: %s'% self.gramSpec
        # print 'Name: %s'% Name
        # print 'Lists: %s'% self.Lists
        # print 'Dicts: %s'% Dicts
        # print 'activeRules: %s'% self.activeRules
        # print 'All: %s'% All
        # print 'Exclusive: %s'% Exclusive
        # print 'exclusive state: %s'% self.exclusive
        
        Elements=BrowseGrammar.ParseGrammarDefinitions(self.gramSpec,Name,self.Lists,
                                                       Dicts,self.activeRules,All,Exclusive,
                                                       self.exclusive)
        if Elements:
            # only if not empty, so leave out empty grammars (non-active if All = 0)
            Grammars.Append(Elements)
        else:
            print('InsertGrammarData, no elements: %s'% Name)

    def Browse(self,Start,All):
        self.DisplayMessage('Processing Grammar')
        self.BrowsePrepare(Start, All)
        self.DisplayMessage('Starting Browser')
        self.BrowseShow()

    def BrowsePrepare(self,Start,All, Exclusive=None):
        """only prepare the current state, should be followed by the BrowseShow
        
        """
        if Exclusive:
            print('browse for exclusive grammars only')
            All = 0
            title = 'Active Rules in Exclusive Grammars'
        elif All:
            title = 'All Grammars'
        else:
            title = 'Active Grammars'
        Grammars=BrowseGrammar.GrammarElement()
        Grammars.Init(BrowseGrammar.RuleCode,title)
        self.CallAllGrammarObjects('InsertGrammarData',[Grammars,All,Exclusive])
        Data=(Grammars,Start,All,Exclusive)
        with  open(GrammarFileName,'wb') as GrammarFile:
            pickle.dump(Data, GrammarFile)
# 
    def BrowseShow(self):
        """show the grammars as prepared in the function BrowsePrepare
        """
        pypath = str(Path(__file__).parent)
        if pypath not in sys.path:
            sys.path.insert(0, pypath) 
        pypath = ';'.join(sys.path)
        os.environ['PYTHONPATH'] = pypath
        unimacroutils.AppBringUp('Browser',Exec=PythonwinExe,Args='/app BrowseGrammarApp.py')
###
##GlobalGrammarBaseAncestor=BrowsableGrammar    
##class GlobalGrammarBase(GlobalGrammarBaseAncestor):
##    __inherited=GlobalGrammarBaseAncestor
##
##
##    def load(self,gramSpec,allResults=0,hypothesis=0):
##        print 'loading from GlobalGrammarBase: %s'% self.__module__
##        success = self.__inherited.load(self,gramSpec,allResults,hypothesis)
##        if success: self.setGlobalGrammarName()
##        return success
##
##
##    def setGlobalGrammarName(self):
##        try:
##            self.setList('GrammarName',self.GetName())
##        except:
##            pass
##
##    def gotResults_OpenThisGrammar(self,words,fullResults):
##        module=self.GetGrammarModuleName()
##        App=getBaseName(getCurrentModule(.lower()[0]))
##        if not (App in ['pythonwin']):        
##            AppBringUp('Pythonw',Exec=PythonwinExe)
##        sendkeys('{Ctrl+l}'+module+'{Enter}')
##  
##LocalGrammarBaseAncestor=BrowsableGrammar    
##class LocalGrammarBase(BrowsableGrammar):
##    __inherited=LocalGrammarBaseAncestor
##    def gotResults_OpenThisGrammar(self,words,fullResults):
##        module=self.GetGrammarModuleName()
##        App=getBaseName(getCurrentModule(.lower()[0]))
##        if not (App in ['pythonwin']):        
##            AppBringUp('Pythonw',Exec=PythonwinExe)
##        sendkeys('{Ctrl+l}'+module+'{Enter}')
##
IniGrammarAncestor=BrowsableGrammar    
class IniGrammar(IniGrammarAncestor):
    """grammar base which has methods for inifile stuff.
    Grammars that derive from this have name set automatically to the module name removing any 
    leading '_' characters.

    """
    #pylint:disable=R0902, R0904
    __inherited=IniGrammarAncestor
    inifile_stem = None
    
    def __init__(self, inifile_stem=None):
        """modname is name of module, for "normal" Unimacro grammars, residing in a module.
        
        Can be overridden for for example test grammars, or when more than one grammar is in a module.
        """
        self.module_name = self.__module__.rsplit('.', maxsplit=1)[-1]
        self.inifile_stem = inifile_stem or self.module_name
        self.language = status.get_language()


        if not hasattr(self, 'ini'):
            self.startInifile()
        self.name = self.checkName()
        if self.ini is None:
            print(f'Serious warning, grammar "{self.name}" has no valid ini file, please correct errors')
        try:
            self.iniIgnoreGrammarLists
        except AttributeError:
            self.iniIgnoreGrammarLists = []
        self.__inherited.__init__(self)
        
        if not self.gramSpec:
            print('Serious error: IniGrammar did not find gramSpec')
            return
        
        try:
            # done before, or coming from DocstringGrammar:
            self.gramSpec = copy.copy(self.originalGramSpec)
        except Exception as exc:
            # first time here, define self.originalGramSpec:
            if self.gramSpec:
                if isinstance(self.gramSpec, list):
                    self.originalGramSpec = copy.copy(self.gramSpec)
                elif isinstance(self.gramSpec, str):
                    self.originalGramSpec = self.gramSpec
                else:
                    raise TypeError(f'IniGrammar "{self.name}", gramSpec should be string or list, not: "{type(self.gramSpec)}"') from exc
        self.gramSpecTranslated = None  # a copy of the resulting translation if any (None otherwise)

        # here the grammar is not loaded yet, but the ini file is present
        # this could have been done in the user grammar already...
        #mod = sys.modules[self.__module__]
##            version = getattr(mod, '__version__', '---')
        self.DNSVersion = status.getDNSVersion()
        self.spokenforms = spokenforms.SpokenForms(self.language, self.DNSVersion) # for spoken forms numbers!!

        #grammarName = grammarName or self.name

        translated = self.translateGrammar(self.originalGramSpec)  # pass original gramSpec...
        if translated:
            self.gramSpec = translated
            try:
                translationText = {'enx': ' (with synonyms)',
                                   'nld': ' (vertaald)'}[self.language]
            except KeyError:
                translationText = ' (translated)'
            self.nameForParser = self.name + translationText
            # print 'translated: %s (%s)'% (self.name, self.gramSpec)
        else:
            # print 'not translated: %s (%s)'% (self.name, self.gramSpec)
            self.gramSpec = self.originalGramSpec
            self.nameForParser = self.name
            
    def __str__(self):
        return '<inigr: %s>'% self.GetName()

    def load(self,gramSpec,allResults=0,hypothesis=0, grammarName=None):
        grammarName = grammarName or self.nameForParser
        success = self.__inherited.load(self,gramSpec,allResults,hypothesis,grammarName)
        if not success:
            print(f'failed to load gramSpec of Unimacro IniGrammar {self}')
        return success

    def checkName(self):
        """get possibly from inifile, if not present, start a inifile entry"""
        try:
            self.name
        except AttributeError:
            pass
        else:
            if not self.name is self.__class__.name:
                return self.name
        try:
            n = self.ini.get('grammar name', 'name')
            if n:
                return n
        except AttributeError:
            pass 

        try:
            n = self.name
        except AttributeError:
            n = self.__module__
            n = n.replace('_', ' ')
            n = n.strip()
        if self.ini:
            print(f'setting grammar name to: {n}')
            self.ini.set('grammar name', 'name', n)
            self.ini.write()
        return n

    def hasCommon(self, one, two, allResults=None, withIndex=None):
        """check if one and two have something in common

        one will often be the "words" list of the recognition

        two can be string or list, in both cases also in gramWords is searched too
        
      ((wish:  **as a special case, one can be a word of the original list, if used in a recursive callback! ))

        with allResults = 1, a list of possibly more hits is returned, always the words in the
        "two" list are returned.

        withIndex: return index of first hit in one (often the words)(not together with Allresults on)      
      
        """
        #pylint:disable=R0912
        L = []
        i = -1
        if isinstance(two, str):
            two = [two]
        if isinstance(one, str):
            one = [one]
        one = [word.lower() for word in one]
        two = [word.lower() for word in two]

            
        for i, a in enumerate(one):
            for b in two:
                if a == b:
                    if allResults:
                        L.append(b)
                    elif withIndex:
                        return b, i
                    else:
                        return b
                elif self.gramWords and b in self.gramWords and a in self.gramWords[b]:
                    if allResults:
                        L.append(b)
                    elif withIndex:
                        return b, i
                    else:
                        return b
##        print 'result hasCommon: %s'% L
        if withIndex:
            return None, 0
        return L or None

    def translateGrammar(self, gramSpec):
        """translate all keywords with possible (multiple) words in your language


        translations (also optional or other keywords) can be entered in the section [grammar words]
        of the appropriate grammar file (say "edit name_of_grammar")

        separate wanted extra words (with the same meaning) by semicolons or |

        each keyword is searched for in the inifile                    
        
        """
        #pylint:disable=R0914, R0912, R0915, R1702
        if not self.ini:
            return None
      
        self.gramWords = {} # keys: new grammar words, values mappings to the old grammar words maybe empty if no translateWords
        translateWords = self.getDictOfGrammarWordsTranslations() # from current inifile
        if not translateWords:
            return None # nothing to translate!
        obsoleteTranslateWords = self.getDictOfObsoleteGrammarWords()
        self.ini.writeIfChanged() # marking unnecessary words
        oldTranslateKeys = list(translateWords.keys())
        newTranslateWords = {}

        if isinstance(gramSpec, list):
            self.oldGramSpec = copy.deepcopy(gramSpec)
            # while type(self.oldGramSpec) == types.ListType:
            #     self.oldGramSpec = '\n'.join(self.oldGramSpec)
        elif isinstance(gramSpec, str):
            self.oldGramSpec = gramSpec
        else:
            print('%s:cannot translate gramSpec, wrong type: %s'% (self.name, type(gramSpec)))
            return None
        localGramSpec = self.oldGramSpec
        # gramparser.splitApartLines(localGramSpec)  # in the list splitting, gst gramSpecTranslated!

        # go and get the peek_ahead iterator of the GramScannerReverse:
        gsr = gramparser.GramScannerReverse(localGramSpec)
        gsgen = gsr.gramscannergen()
        it = utilsqh.peek_ahead(gsgen)
        state = 'rule'  # 'rule' or 'expression'
        prevTok = None
        for wh, token, value in it:
            if state == 'rule':
                if token == '=':
                    # move to expression state
                    _wordPrevParen = _wordNextParen = 0
                    state = 'expr'
                gsr.appendToReturnList(wh, token, value)
                prevTok = token
                continue
            # now state == 'expr':
            if token == ';':
                # go back to a rule part:
                gsr.appendToReturnList(wh, token, value)
                state = 'rule'
                prevTok = token
                continue
            
            printedLines = 0
            # now inside a rule:
            if token in ['sqword', 'dqword', 'word']:
                if (not value.lower() in translateWords) and \
                        obsoleteTranslateWords and value.lower() in obsoleteTranslateWords:
                    if not printedLines:
                        print('Make grammar obsolete word (translation/synonyms) current again: "%s": %s (grammar: "%s")'% (value.lower(),
                                                                                                                              obsoleteTranslateWords[value.lower()], self.name))

                    translateWords[value.lower()] = obsoleteTranslateWords[value.lower()]
                    del obsoleteTranslateWords[value.lower()]
                    self.ini.set('grammar words', value.lower(), translateWords[value.lower()])
                    self.ini.delete('grammar obsolete words', value.lower())
                    self.ini.write()
                if value.lower() in translateWords:
                    if value.lower() in oldTranslateKeys:
                        oldTranslateKeys.remove(value.lower())
                    newValue = translateWords[value.lower()]
                    self.addToGramWords(value, newValue)
                    if len(newValue) == 0:
                        # no translation keep as it is
                        pass
                    elif len(newValue) == 1:
                        value = newValue[0]
                    else:
                        nextTok = it.preview[1]
                        parensNeeded = not (prevTok == '(' and nextTok in ['|', ')'] or
                                            prevTok == '[' and nextTok in ['|', ']'] or
                                            prevTok == '|' and nextTok in [']', ')', '|'])
                        #insert between parenthesis:
                        if parensNeeded:
                            gsr.appendToReturnList(wh, '(', None)
                        for w in newValue:
                            gsr.appendToReturnList('', 'word', w)
                            if w != newValue[-1]:
                                gsr.appendToReturnList('', '|', None)
                        if parensNeeded:        
                            gsr.appendToReturnList('', ')', None)
                        prevTok = token
                        continue
                else:
                    # word with value in self.translateWords:
                    newTranslateWords.setdefault(value.lower(), set()).add(value)
            gsr.appendToReturnList(wh, token, value)
            prevTok = token
        self.correctIniFile(translateWords, newTranslateWords, obsoleteTranslateWords, oldTranslateKeys)
        self.stripDefaultTranlations(self.gramWords)
        if not self.gramWords:
            return None # nothing is translated
        
        result = gsr.mergeReturnList()
        return result
            
    def addToGramWords(self, original, ListOfSynonyms):
        """build up the dict of gramWords synonyms/translations
        """
        orgLower = original.lower()
        L = self.gramWords.setdefault(orgLower, [])
        if ListOfSynonyms:
            for syn in ListOfSynonyms:
                if not syn.lower() in L:
                    L.append(syn.lower())
        else:
            L.append(orgLower)  # no translation, keep the original
                
                
    def stripDefaultTranlations(self, D):
        """strip from D (self.gramWords) the synonyms which are equal to the gramWord itself
        """
        for k, v in list(D.items()):
            if len(v) == 1 and v[0] == k:
                del D[k]
        
            
    def correctIniFile(self, translateWords, newTranslateWords, obsoleteTranslateWords,
                       oldTranslateKeys):
        """correct if needed the sections [grammar words] and [grammar obsolete words]
        
        translateWords = dict of actual [grammar words] section, each value is a list of words
        newTranslateWords = dict of words that are NOT YET in the [grammar words] section, each value is a set of words
        obsoleteTranslateWords = dict of current obsolete grammar words, each value is a list of words
        oldTranslateKeys = keys from [grammar words] that are NOT used in the grammar, so have to be moved to the
                [grammar obsolete words] section
                
        """
        if oldTranslateKeys:
            # make words obsolete
            for k in oldTranslateKeys:
                if k == translateWords[k]:
                    self.ini.delete('grammar obsolete words', k)
                else:
                    # remember word translation for possible future use:
                    #print 'set obsolete: %s, %s'% (k, translateWords[k])
                    self.ini.set('grammar obsolete words', k, translateWords[k])
                self.ini.delete('grammar words', k)
            self.ini.write()
        notTransSection = 'grammar non translated words'
        
        if newTranslateWords:
            iniFileNonTranslatedWords = self.ini.getList(notTransSection, 'words')
            if iniFileNonTranslatedWords == newTranslateWords:
                pass
                #print 'correctIniFile, non translated words same as before'
            else:
                self.ini.set(notTransSection, 'words', list(newTranslateWords.keys()))
                if self.language == 'enx':
                    self.ini.set(notTransSection, 'info1', 'These grammar words can be changed if you want synonyms for them.')
                elif self.language == 'nld':
                    self.ini.set(notTransSection, 'info1', 'De volgende grammatica woorden kunnen worden vertaald.')
                else:
                    self.ini.set(notTransSection, 'info1', 'These grammar words can be translated.')
                self.ini.set(notTransSection, 'info2', 'See https://qh.antenna.nl/unimacro/features/translations for more info')
                self.ini.write()
        else:
            if self.ini.get(notTransSection):
                self.ini.delete(notTransSection)
                self.ini.write()
            
    ## for difficult recognised grammar words in counts:
    #def addSpokenFormNumbers(self, taskCounts):
    #    """if present, add spoken forms to the list of tasknumbers"""
    #    if self.language in spokenFormCounts:
    #        spoken = spokenFormCounts[self.language]
    #        for entry in spoken:
    #            if entry in taskCounts:
    #                taskCounts.append("%s\\%s"% (entry, spoken[entry]))
    #
    #def stripSpokenForm(self, text):
    #    return text.split("\\")[0]

    def getDictOfGrammarWordsTranslations(self):
        """return a dict of grammar word translations/synonyms
        
        keys: from inifile, grammar words section
        values: list of words in these values
        so: (in inifile)
        [grammar words]
        hello = hello
        there = there|already
        now = immediate;soon
        
        results in:
        {'there': ['there', 'already'], 'now': ['immediate', 'soon']}
        see unittestIniGrammar for more testing and examples.
        """
        DictFromIni = self.ini.toDict('grammar words')
        if not DictFromIni:
            return {}
        D = {}
        for k, v in DictFromIni.items():
            k = k.lower()
            if isinstance(v, list):
                D[k] = v
            else:
                D[k]  = self.makeWordListFromGrammarWordsEntry(v)

            # ignore identical entries:
            vCheck = D[k]
            if len(vCheck) == 1 and vCheck[0] == k:
                self.ini.delete('grammar words', k)
                del D[k]
        return D

    def getDictOfObsoleteGrammarWords(self):
        """return a dict of grammar words which are marked obsolete in this grammar
        
        Just you can use them in case they are activated again, and they can be written back
        in case translation words (in the section [grammar words]) are not in the grammar any more)
        
        keys: from inifile, grammar words section
        values: list of words in these values
        so: (in inifile)
        [grammar words]
        there = there|already
        now = immediate;soon
        
        results in:
        {'there': ['there', 'already'], 'now': ['immediate', 'soon']}
        see unittestIniGrammar for more testing and examples.
        """
        # print('self.ini: %s, sections: %s'% (self.ini._file, self.ini.get()))
        DictFromIni = self.ini.toDict('grammar obsolete words')
        if not DictFromIni:
            return None
        D = {}
        for k, v in DictFromIni.items():
            k = k.lower()
            if isinstance(v, list):
                D[k] = v
            else:
                D[k]  = self.makeWordListFromGrammarWordsEntry(v)
            
            # ignore identical entries (capitalisation ignored): tot
            V = D[k]
            if len(V) == 1 and V[0] == k:
                self.ini.delete('grammar obsolete words', k)
                del D[k]
        if not D:
            self.ini.delete('grammar obsolete words')
        self.ini.writeIfChanged()
        return D

    def makeWordListFromGrammarWordsEntry(self, value):
        """get a entry from [grammar words] and split into a list
        
        input:  'hello; there'
        output: ['hello', 'there']

        """
        #key = self.cleanGrammarWord(key)
        #line = self.ini.get('grammar words', value)
        for splitchar in (',', ';', '|'):
            if value.find(splitchar) > 0:
                words = value.split(splitchar)
                words = list(map(self.cleanGrammarWord, words))
                break
        else:
            words = [self.cleanGrammarWord(value)]
            
        return [_f for _f in words if _f]

                       

    def removeObsoleteGrammarWords(self):
        """remove from keywords list in ini file obsolete words

        if the grammar is changed, these words are not needed in the ini file any more.

        """
        allKeys = self.ini.get('grammar words')
        print(f'natlinkutilsbj, removeObsoleteGrammarWords allKeys: {allKeys}')
        for k in allKeys:
            print('removeObsoleteGrammarWords, all vars:')
            print(f'{dir(self)}')
            if k not in self.allGrammarKeywordsLower:
                v = self.ini.get('grammar words', k)
                self.ini.delete('grammar words', k)
                if k != v.lower():
                    self.ini.set('grammar obsolete words', k, v)
                self.iniChanged = 1

    def getTranslation(self, Dict):
        """get with self.language as key the text from dict, if invalid, return 'enx' text
        """
        if self.language in Dict:
            return Dict[self.language]
        return Dict['enx']


    def cleanGrammarWord(self, word):
        """strip and remove quotes

        this is from the input grammar into the inifile or self.gramWords, the words are inserted
        without surrounding quotes.

(test from testunimacro (qh))
>>> t = Test()
>>> print t.cleanGrammarWord('aap')
aap
>>> print t.cleanGrammarWord('"note mies"')
note mies
>>> print t.cleanGrammarWord("' noot    mies '")
noot mies

        """
        w = word.strip()
        w = word.strip('"\'')
        w = ' '.join(w.split())
        w = w.strip()
        return w
        
    def checkKeyword(self, t):
        """put quotes around if t has spaces, future: remove unwanted characters

        this is the way from the inifile into the grammar
        
        """
        if t.find(' ') > 0:
            return "'" + t + "'"
        if t.find('-') > 0:
            return "'" + t + "'"  
        return t

    def switchOn(self, **kw):
        """switches grammar on, activates all rules, fills lists

        this version assumes all lists are filled at switching on time.
        must be overloaded if more specific behaviour is wished
        """        
        # if you want rules dynamically activated in gotBegin,
        # the following line should be skipped in the overloaded function,
        # and the variable self.prevModInfo should be set to None
        fillLists = kw.get('fillLists', None)
        if fillLists:
            print(f'{self.name}, switchOn, with fillLists: {fillLists}')
        if not self.__inherited.switchOn(self, **kw):
            print('switching on "%s" failed'% self.name)
            return
            

        # if you want to fill lists dynamically, you should skip
        # next line your overloaded function, and fill your lists
        # inside gotBegin, whenever self.prevModInfo is changed
#         if not fillLists:
#             # is used in grammar commands, see there
# ##            print 'skip filling lists: %s'% self.name
#             return
        
        # try:
        self.fillGrammarLists()
        # print(f'IniGrammar switched on: {self.getName()}')

    def showInifile(self, body=None, grammarLists=None, ini=None,
                    showGramspec=1, prefix=None, commandExplanation=None,
                    postfix=None, lineLen=60, sort=1):

        """gives grammar information and formats this in a file,
        that is opened after that.

        body: main text, can be left off (list or string)
        grammarLists: giving the lists from the inifile (if present),
                      that are used in the grammar
        ini: inivars instance, assumed to be self.ini
        showGramspec: 0 or 1, showing the complete grammar specification
        prefix: if given replaces the standard prefix
        commandExplanation: if given adds extra information (list or string)
        postfix: if given replaces the standard postfix

        beware:
        as I use language dependent grammars, I expect each grammar specification
        to start with 12 spaces!
        """
        #pylint:disable=R0915, R0913, R0914, R0912
        ini = ini or self.ini

        # grammarLists can be given, or taken from the inifile:
        grammarLists = grammarLists or ini.get()
        activeLists = list(self.Lists.keys())
        moduleName = self.__module__
        # language must be used:
        language = status.get_language()
        assert isinstance(grammarLists, list)
        grammarwordsLists = [l for l in grammarLists if l.startswith('grammar ')]
        grammarLists = [l for l in grammarLists if not l.startswith('grammar ')]
        grammarwordsLists.sort()
        grammarLists.sort()
        
        L  = []
        
        if prefix:
            L.append(prefix)
        else:
            try:
                formatLine = {'nld': 'Uitleg voor Unimacro (Natlink) grammatica "%s" (bestand: %s.py)'}[language]
            except:
                formatLine = 'Help for Unimacro (Natlink) grammar "%s" (file: %s.py)'
            L.append(formatLine % (self.name, moduleName))
        L.append('')

        if body:
            if isinstance(body, list):
                L.extend(body)
            else:
                L.append(body)
            L.append('')


        ## the gramspec, was at bottom before, now put at top:
        if showGramspec:
            try:
                L.append({'nld': '\n--- grammatica:'}[language])
            except:
                L.append('\n--- grammar:')
            if self.gramSpecTranslated:
                try:
                    L.append({'nld': ' --- vertaald', 'enx': ' --- with synonyms'}[language])
                except:
                    L.append(' --- translated')
            L.append('')
            if self.gramSpecTranslated:
                t = copy.copy(self.gramSpecTranslated)
            else:
                t = copy.copy(self.gramSpec)

            t = gramparser.splitApartLines(t)
            
            #print 'gramSpec %s %s'% (type(t), repr(t))
            L.extend(t)



        if grammarLists or activeLists:
            # get from ini, using again utilsqh:
            try:
                L.append({'nld': '\n--- lijsten:\n'}[language])
            except:
                L.append('\n--- lists:\n')
            grammarLists.sort()
            activeLists.sort()
            emptyLists = []
            for gList in activeLists:
                listValues = self.Lists[gList]
                if not listValues:
                    emptyLists.append(gList)
                    continue
                nListValues = len(listValues)
                #if gList == 'degrees':
                #    print 'degrees: %s'% listValues
                #    print '----\ns2n: %s'% self.spokenforms.s2n
                #    print '----\nn2s: %s'% self.spokenforms.n2s
                onlyNumbers = self.spokenforms.sortedByNumbersValues(listValues, valueSpokenDict=1)
                if onlyNumbers:
                    #if gList == 'degrees':
                    #    print 'numbersDict: %s'% onlyNumbers
                    formattedTexts = inivars.formatReverseNumbersDict(onlyNumbers)
                    if nListValues > 20:
                        L.append("\n[%s] (%s)\n%s\n"% (gList, nListValues, formattedTexts))
                    else:
                        L.append("\n[%s]\n%s\n"% (gList, formattedTexts))

                elif '%sDict'%gList in dir(self):
                    if gList in grammarLists:
                        grammarLists.remove(gList)
                    dictName = "%sDict"% gList
                    items = getattr(self, dictName).keys()   ## not sorted!!
                    listFromIni = sorted(ini.get(gList))
                    itemsSorted = sorted(items)
                    nListValues = max(len(listFromIni), len(items))
                    if nListValues > 20:
                        if listFromIni != itemsSorted:
                            L.append("\n[%s] (from %s, %s)"% (gList, dictName, nListValues))
                        else:
                            L.append("\n[%s] (%s)"% (gList, nListValues))
                            items = listFromIni
                    else:
                        if listFromIni != itemsSorted:
                            L.append("\n[%s] (from %s)"% (gList, dictName))
                        else:
                            L.append("\n[%s]"% gList)
                            items = listFromIni
                    L.append(formatListColumns(items))
                    itemsFromGrammar = sorted(self.Lists[gList])
                    if itemsFromGrammar != itemsSorted:
                        L.append('\ncomplete list from grammar (different):')
                        L.append(formatListColumns(itemsFromGrammar))
                    L.append('\n')
                
                elif '%sList'%gList in dir(self):
                    if gList in grammarLists:
                        grammarLists.remove(gList)
                    listName = '%sList'%gList
                    items = sorted(getattr(self, listName))
                    listFromIni = sorted(ini.get(gList))
                    if nListValues > 20:
                        if listFromIni != items:
                            L.append("\n[%s] (from %s, %s)"% (gList, listName, nListValues))
                        else:
                            L.append("\n[%s] (%s)"% (gList, nListValues))
                            items = listFromIni
                    else:
                        if listFromIni != items:
                            L.append("\n[%s] (from %s)"% (gList, listName))
                        else:
                            L.append("\n[%s]"% gList)
                            items = listFromIni
                    L.append(formatListColumns(items))
                    itemsFromGrammar = sorted(self.Lists[gList])
                    if itemsFromGrammar != items:
                        L.append('\ncomplete list from grammar (different):')
                        L.append(formatListColumns(itemsFromGrammar))
                    L.append('\n')
                elif gList in grammarLists:
                    grammarLists.remove(gList)
                    L.append(ini.formatKeysOrderedFromSections([gList],
                                                   lineLen=lineLen, sort=sort, giveLength=20))
                else:
                    L.append("\n[%s] (not found in inifile, %s)"% (gList, nListValues))
                    items = sorted(self.Lists[gList])
                    L.append(formatListColumns(items))
                    L.append('')
            restSections = []
            for section in grammarLists:
                if section == 'general':
                    items = sorted(ini.get(section))
                    L.append("\n[%s] (options)"% section)
                    for i in items:
                        v = ini.get(section, i)
                        L.append('%s = %s'% (i, v))
                    #L.append(formatListColumns(items))
                    L.append('')
                else:
                    restSections.append(section)
            if restSections:
                L.append("\nOther sections:")
                L.append(formatListColumns(restSections))
                L.append('')
            if emptyLists:
                emptyLists.sort()
                L.append("\nEmpty lists:")
                L.append(formatListColumns(emptyLists))
                L.append('')
                
                

##        if grammarwordsLists:
##            continue
##            # get from ini, using again utilsqh:
##            # ignore these;;;;;;;;;;
##            try:
##                L.append({'nld': '\n--- grammatica lijsten (voor vertaling of synoniemen):\n'}[language])
##            except:
##                L.append('\n--- grammar lists (for translation or synonyms):\n')
##            L.append(ini.formatKeysOrderedFromSections(grammarwordsLists,
##                                                       lineLen=lineLen, sort=sort))
        active = list(self.activeRules.keys())
        valid = copy.copy(self.validRules)
        active.sort()
        valid.sort()
        if valid and valid == active:
            pass
        elif active:
            L.append('active rules: %s'% ', '.join(active))
        else:
            L.append('no rules are active')


        if commandExplanation:
            if isinstance(commandExplanation, list):
                L.extend(commandExplanation)
            else:
                L.append(commandExplanation)
            L.append('')
                    
     
        if postfix:
            L.append(postfix)
        else:
            try:
                formatLine = {'nld': '\n--- gebruiker: %s, %s'}[language]
            except:
                formatLine = '\n--- user: %s, %s'
            L.append(formatLine %(natlink.getCurrentUser()[0], time.asctime(time.localtime(time.time()))))

        try:
            extension = {'nld': '_uitleg.txt'}[language]
        except:
            extension = '_help.txt'

        
        whatFile = os.path.join(os.environ['TEMP'], language + '__' + moduleName.replace(' ', '_') + extension)
        if os.path.isfile(whatFile):
            #print 'already exist, try to remove: %s'% whatFile
            try:
                os.remove(whatFile)
            except OSError:
                print('Cannot remove previous help (show) file: "%s:"\nProbably this file is still open in Notepad\nPlease close and call your command again'% whatFile)
                return
        if os.path.isfile(whatFile):
            print('Cannot remove previous help (show) file: "%s:"\nProbably this file is still open in Notepad\nPlease close and call your command again'% whatFile)
            return
        
        #print 'writing to and open:\n\t"%s"'% whatFile
        t = '\n'.join(L)
        rwfile = readwritefile.ReadWriteFile()
        rwfile.writeAnything(whatFile, t)
       
        self.openFileDefault(whatFile, mode="edit")

    def editInifile(self):
        """opens the inifile that controls the behaviour of
        the grammar
        
        if inifile is not given, the standard name is expected
        """
        inifile = self.inifile
        self.iniFileDate = unimacroutils.getFileDate(inifile)
        self.checkForChanges = 1
        self.openFileDefault(inifile, mode="edit")

    def fillGrammarLists(self, listOfLists=None):
        """fills the lists of the grammar with data from inifile

        If listOfLists is not provided, all sections from the inifile
        are tried.

        Lists "number1to99" and "number1to9" are taken from this file, unless
        they are provided in inifile
        As well as "n1-9" etc
        
        Numbers are taken from spokenforms, as well as 'character'.

        Also if listName is found in self.iniIgnoreGrammarLists, it is skipped,
        but with a warning

        At the end of the function it is checked if there are no
        remaining lists from the grammar that should be filled.

        """
        #pylint:disable=R0912
        if not self.ini:
            print(f'--- no valid ini file for grammar: "{self.GetName()}", will not fill grammar lists\n\tPlease try to correct via "edit {self.getName()}"')
            return 
        ini = self.ini
        fromGrammar = copy.copy(self.validLists)
        allListsFromIni = ini.get()

        nonemptyListsFromIni = [l for l in allListsFromIni if ini.get(l)] # empty sections ignored
        if self.iniIgnoreGrammarLists:
            self.removeFromList(fromGrammar, self.iniIgnoreGrammarLists)
        if listOfLists:
            for l in listOfLists:
                if l not in fromGrammar:
                    self.error('fillGrammarLists, list name not in grammar: %s'% l)
                    continue
                if l not in allListsFromIni:
                    self.error('fillGrammarLists, list name not in ini file: %s'% l)
                    continue
                if self.fillList(l):
                    fromGrammar.remove(l)
                
        else:
            for l in nonemptyListsFromIni:
                if l not in fromGrammar:
                    continue
                if self.fillList(l):
                    fromGrammar.remove(l)

        if fromGrammar:
            changes = 0
            for l in fromGrammar[:]:
                if l in self.iniIgnoreGrammarLists:
                    continue
                if self.fillList(l):
                    fromGrammar.remove(l)
                elif l in allListsFromIni:
                    pass
                    # print('\t%s: warning, empty section for list "%s" in inifile'% (self.name, l))
                else:
                    changes = 1
                    self.emptyList(l)
                    self.ini.set(l)
            if changes:
                self.ini.write()
                commandText = {'nld': 'bewerk'}
                try:
                    commandWord = commandText[self.language]
                except KeyError:
                    commandWord = "edit"

                self.message('fillGrammarLists in grammar "%s"\n\nNot all lists filled: %s\n\nPlease fill in in inifile by calling the command "%s %s"'%
                                    (self.name, fromGrammar, commandWord, self.name))
                self.checkForChanges = 1
                self.iniFileDate = unimacroutils.getFileDate(self.inifile)
                
                #self.openFileDefault(self.inifile)

    def setNumbersList(self, name, numbers):
        """try to get spoken forms for the numbers
        """
        mixed = self.spokenforms.getMixedList(numbers)
        # print 'mixed list (setNumbersList) of %s: %s'% (name, mixed)
        self.setList(name, mixed)
        return mixed # so true if list is there...

    def setCharactersList(self, name, chars=None):
        """try to get spoken forms for the characters, a-z if chars is None
        """
        if chars is None:
            #now unicode:
            chars = string.ascii_lowercase
            
        spokenList = self.spokenforms.getMixedCharactersList(chars)
        #print 'characters list "%s": %s'% (name, spokenList)
        self.setList(name, spokenList)
        return spokenList
            
    def getCharacterFromSpoken(self, word, originalList=None):
        """returns a character, corresponding with word
        
        if originalList is given ('abcd...') validate the result with this list
        """
        if isinstance(word, str):
            return self.spokenforms.getCharFromSpoken(word, originalList)
        raise ValueError('getCharFromSpoken: input must be a string (normally one of the "words", not: %s'% word)
 
    def setPunctuationList(self, name, puncts=None):
        """try to get spoken forms for the punctuation, all defined in spokenforms if chars is None
        """
        allPunctsSpoken = list(self.spokenforms.spoken2punct.keys())
        if puncts is None:
            spokenList = allPunctsSpoken
        else:
            spokenList = [i for i in puncts if i in allPunctsSpoken]

        # print('characters list "%s": %s'% (name, spokenList))
        self.setList(name, spokenList)
        return spokenList
            
    def getPunctuationFromSpoken(self, word, originalList=None):
        """returns a punctuation character, corresponding with word
        
        if originalList is given (',.:?' or [',', '.', ':', "?"] etc) validate the result with this list
        """
        if isinstance(word, str):
            return self.spokenforms.getPunctuationFromSpoken(word, originalList)
        raise ValueError('getCharFromSpoken: input must be a string (normally one of the "words", not: %s'% word)


    def getNumberFromSpoken(self, word, originalList=None, asStr=None):
        """returns as the number, corresponding with word
        
        if originalList is given (either list of int or str), validate the result with this list
        if asStr = True, return as string, otherwise return as int
        """
        if isinstance(word, str):
            return self.spokenforms.getNumberFromSpoken(word, originalList, asStr)
        for w in word:
            result = self.spokenforms.getNumberFromSpoken(w, originalList, asStr)
            if result:
                return result
        # if no valid result:
        return result
            
    def getNumbersFromSpoken(self, words, originalList=None, asStr=None):
        """returns as list the numbers from wordOrWords
        
        if originalList is given (either list of int or str), validate the result with this list
        if asStr = True, return as string, otherwise return as int
        """
        if isinstance(words, list):
            L = [self.spokenforms.getNumberFromSpoken(w, originalList, asStr) for w in words]
            L = [_f for _f in L if _f]
            return L
        raise ValueError('getNumbersFromSpoken: input must be a list (normally "words", not: %s'% words)

    def fillList(self, listName):
        """fill a list in the grammar from the data of the inifile
        
        numbers lists get special treatment.
        
        special case: iniChangingData (_folders) can set a previous cached list for a future session. ('recentfolders')
        
        """
        #pylint:disable=R0915
        n = listName
        
        if n[:6] == 'number' or \
                  (n[0] == 'n' and '-' in n):
            L = self.spokenforms.getNumberList(n)
            if L:
                #print 'numbers (of %s): %s'% (n, L)
                return self.setNumbersList(n, L)
        if n == 'character':
            print('character list')
            return self.setCharactersList('character')
        # else:
        l = self.ini.get(n)
        if l:
            #print '%s: filling list %s with %s items'% (self.name, listName, len(l))
            self.setList(n, l)
            return 1
        #print '%s: not filling list %s, no items found'% (self.name, listName)
        self.emptyList(n)
        return None

    def fillInstanceVariables(self):
        """fills instance variables with data from inifile

        default: nothing happens, must be supplied by the calling grammar    

        """
        return

    def startInifile(self):
        """loads the inifile for the grammar given.

        Is called at initialisation of this instance.

        In this function the following variables are set,
        checkForChanges, starts normally at 0
            if you perform the "editGrammar" function, this variable is set to 1,
            and the gotBegin function only goes into the function "checkInifile",
            if this variable is set.

        if the commandDir contains a folder "private", AND the specified file
        is in this folder, this inifile is taken. meant only for developers.

        After this function also are set:
        ini, the inivars instance that controls the ini variables
        inifile, the full path of the inifile that is opened
        inifileDate, the date/time the inifile was last modified        

        For debugging purposes, modName can be specified

        """
        # get default inifile name:
        self.checkForChanges = 1
        self.openedInifile = 0
        self.ignore = None
        inifile_stem = self.inifile_stem
        if not inifile_stem:
            raise ValueError(f'startInifile, {self.name}, no inifile_stem found ')
        # baseDir = status.getUnimacroDirectory()
        userDir = status.getUnimacroUserDirectory()
        
        commandDir = os.path.join(userDir,
                                        self.language +"_inifiles")
        inifile_name = inifile_stem + '.ini'
        inifile = os.path.join(commandDir, inifile_name)
        if not os.path.isfile(inifile):
            print(f'\n\tCannot find inifile: {inifile_name}')
            self.lookForExampleInifile(commandDir, inifile_stem + '.ini')
            if not os.path.isfile(inifile):
                print(f'\tcannot find an example inifile for {inifile_stem}')
                self.inifile = inifile
                self.TryToMakeDefaultInifile(commandDir, inifile_stem + '.ini', self.language)
                if not  os.path.isfile(inifile):
                    self.message(f'cannot make a default inifile for: {inifile_stem} ({inifile})')
                    self.inifile = None
                    return
            #self.openFileDefault(inifile)
            commandText = {'nld': 'bewerk'}
            try:
                commandWord = commandText[self.language]
            except KeyError:
                commandWord = "edit"
            name = self.getName()
            self.message(f'\tCreated new inifile: "{inifile}"\n\tYou can inspect and edit this file by calling the command "{commandWord} {name}"\n')
        self.inifile = inifile
        #self.ini = inivars.IniVars(self.inifile, repairErrors=1)

        self.iniFileDate = unimacroutils.getFileDate(self.inifile)
        try:
            # return all Unicode...
            # self.ini = inivars.IniVars(self.inifile, returnStrings=1, repairErrors=1)
            self.ini = inivars.IniVars(self.inifile, repairErrors=1)
        except inivars.IniError:
            mess = str(sys.exc_info()[1])
            self.openFileDefault(self.inifile)
            print('****IniError while initialising: %s' % self.name)
            if notifyIniErrors:
                self.message(mess)
            print('****error message: '+mess)

            self.ini = None
            return


        # starting variable:
        self.prevModInfo = None        
        self.checkForChanges = 0
        
        # control on or off:
        initialOn = self.ini.get('general', 'initial on', '1')
        user = status.get_user()
        initialOnUser = self.ini.get('general', 'initial on %s'% user)
        initialOn = initialOnUser or initialOn
        if initialOn.lower() == 'exclusive':
##            print 'ask for exclusive: %s'% self.name
            self.mayBeSwitchedOn = initialOn.lower()
        else:
            self.mayBeSwitchedOn = (initialOn.lower()  in ['1', 'on'])

        self.prevModInfo = None
        try:
            self.fillInstanceVariables()
        except inivars.IniError:
            mess = str(sys.exc_info()[1])
            self.openFileDefault(self.inifile)
            if notifyIniErrors:
                self.message(mess)
            print('***IniError when filling instance variables: %s' % self.name)
            print('***error message: '+mess)
            self.ini = None
            return

    def lookForExampleInifile(self, commandDir, fileName):
        """must be tested, look for a valid inifile in one of the sample dirs
        """
        baseDir = status.getUnimacroDirectory()
        # userDir = status.getUnimacroUserDirectory()
        # originalUnimacroDir = status.getUnimacroDirectory()
        sampleBases = [baseDir.lower()]
        # if originalUnimacroDir.lower() not in sampleBases:
        #     sampleBases.append(originalUnimacroDir.lower())
        if not os.path.isdir(commandDir):
            try:
                os.mkdir(commandDir)
            except OSError:
                print('cannot make inifiles directory: %s'% commandDir)
                return
        trySampleDirs = [os.path.join(sample, 'sample_ini', self.language +"_inifiles") for
                         sample in sampleBases]
        sampleDirs = [sample for sample in trySampleDirs if os.path.isdir(sample)]
        if self.language != 'enx':
            enxSampleDirs = [os.path.join(sample, 'sample_ini', "enx_inifiles") for
                 sample in sampleBases]
            sampleDirs.extend([sample for sample in enxSampleDirs if os.path.isdir(sample)])

        #print 'sampleDirs: %s'% sampleDirs
        inifile = os.path.join(commandDir, fileName)
        if sampleDirs:
            tryInifilesamples = [os.path.join(sample, fileName) for
                                    sample in sampleDirs]
            inifileSamples = [sample for sample in tryInifilesamples
                              if os.path.isfile(sample)]
        else:
            inifileSamples = None
        if not os.path.isfile(inifile):
            if inifileSamples:
                sample = inifileSamples[0]
                print('\tTake sample inifile: %s'% sample)
                shutil.copyfile(sample, inifile)
            else:
                print('Could not find a valid sample inifile "%s" in directories: %s'%\
                        (fileName, sampleDirs))

    def TryToMakeDefaultInifile(self, commandDir, inifileName, language):
        """must be checked"""
        ## TODOQH
        userDir = status.getUnimacroUserDirectory()
        modName = self.__module__

        if self.language != 'enx':
            enxFolder =  os.path.normpath(os.path.join(userDir, "enx_inifiles"))
            if os.path.isdir(enxFolder):
                enxVersion = os.path.join(enxFolder, modName + '.ini')
                if os.path.isfile(enxVersion):
                    self.makeDefaultInifile(enxVersion=enxVersion)
                else:
                    self.makeDefaultInifile()
        else:
            self.makeDefaultInifile()
                
    def checkInifile(self):
        """checking the inifile for changes

        Initialisation is supposed to have been done in the routine
        startInifile.
        """
        newDate = unimacroutils.getFileDate(self.inifile)

        if newDate == 0:
            return None # error, no inifile active

        if newDate > self.iniFileDate:
            # oldName = self.ini.get('grammar name', 'name')
            #print 'newDate of %s'% self.inifile
            self.iniFileDate = newDate
            print('---(re)loading inifile: %s'% self.inifile) ##, self.iniFileDate)
            try:
                self.ini = inivars.IniVars(self.inifile, repairErrors=1)
                self.fillInstanceVariables()
                self.switchOn()
                self.openedInifile = 0
                # newName = self.ini.get('grammar name', 'name')
                #
                # NOTE: here we rely on the definition of the grammar specification as gramSpec class variable!
                #
                previousGramSpec = copy.copy(self.gramSpec)
                if isinstance(self.gramSpec, str):
                    previousGramSpec = self.gramSpec
                elif isinstance(self.gramSpec, list):
                    previousGramSpec = '\n'.join(self.gramSpec)
                else:
                    raise TypeError('At reload inifile of IniGrammar "%s", gramSpec should be a string or a list, not: %s'% (self.name, type(self.gramSpec)))
                translated = self.translateGrammar(self.originalGramSpec)  # pass originalGramSpec...
                if translated and translated != previousGramSpec:
                    print('translated: %s'% translated)
                    print('previous: %s'% previousGramSpec)
                    self.gramSpec = translated
                    # fullPath = natlinkmain.loadedFiles[self.__module__][0]
                    natlinkmain.set_load_on_begin_utterance(2)
                    print(f'going to reload grammar {self.name})')
                    # os.utime(fullPath, None)
                    self.DisplayMessage('grammar %s will be reloaded at next utterance'% self.name)
                self.iniFileDate = unimacroutils.getFileDate(self.inifile)  # just in case it has been changed during translate
                #elif translated:
                #    print 'translation identical, no reload necessary for %s'% self.name

            except inivars.IniError:
                mess = str(sys.exc_info()[1])
                if not self.openedInifile:
                    self.openFileDefault(self.inifile)
                self.openedInifile = 1

                if notifyIniErrors:
                    self.message(mess)
                print('****error inifile: '+mess)
                return None
            return 1  # signalling things changed
        return None # no changes needed
    
    def openFolderDefault(self, foldername, mode=None, windowStyle=None, openWith=None):
        """open the folder in the default window
        
        is only used for top windows, calling from a dialog window should be handled otherwise
        
        mode and windowStyle and openWith are (currently) not used any more, could be re-implemented
        
        """
        # mode = mode or 'open'
        if not os.path.isdir(foldername):
            self.DisplayMessage('the folder you want to open does not exist: %s'% foldername)
            return None
        return UnimacroBringUp(app=None, filepath=foldername)
        #
        #
        #print 'open with AppBringup: %s'% foldername
        #natlink.execScript('AppBringup "%s"'% foldername)
        ##win32api.ShellExecute(0, mode, foldername, '', '', windowStyle or win32con.SW_SHOWNORMAL)
        ##int = ShellExecute(hwnd, op , file , params , dir , bShow )
        ##unimacroutils.AppBringUp('folder', foldername, windowStyle=windowStyle)



    def openWebsiteDefault(self, website, openWith=None):
        """open the website in the default window or specific openWith program

        
        """
        print('openWebsiteDefault: %s (openWith: %s)'% (website, openWith))
        # appname = "website %s"% website
        if openWith:
            return UnimacroBringUp(openWith, website)
        return UnimacroBringUp(None, website)

    def openFileDefault(self, filename, mode=None, windowStyle=None, name=None, openWith=None):
        """open the file in the default window

        if the file is opened with AppBringUp ( not one of the exceptions), the optional
        name is given, which can be used with to switch to command! (to be investigated)
        In the messages window the name of the AppBringUp command is given.
        
        windowStyle and name are not used at the moment.

        if OpenWith is a valid program, this is used.
        otherwise if mode is valid, take it,
        otherwise 'open' is passed.
        
        """
        if mode or openWith:
            print('openFileDefault: %s (mode: %s, openWith: %s)'% (filename, mode, openWith))
        else:
            print('openFileDefault: %s'% filename)
        
        # appname = "file %s"% filename
        mode = mode or 'open'
        
        if not os.path.isfile(str(filename)):
            self.DisplayMessage('the file you want to open does not exist: %s'% filename)
            return None
        if openWith:
            return UnimacroBringUp(openWith, filename)
        if mode and mode in ['open', 'edit']:
            return UnimacroBringUp(mode, filename)
        return UnimacroBringUp(None, filename)

    def getFromInifile(self, words, section, noWarning=0):
        """extract value from inifile, with words as possible keys


        If "words" is a string (single word from the list of words),
        only this word is looked up, returns '' if not found

        If "words" is a list, the first hit is returned.        
        """
        #pylint:disable=
        if self.ini is None:
            self.error('no valid inifile')
        if isinstance(words, str):
            v = self.ini.get(section, words, None)
            if v is None and not noWarning:
                print('warning getFromInifile: no value found, ' \
                      'word: %s, section: %s, module: %s' % \
                              (words, section, self.__module__))
            return v

        # list of words, normal case:
        for w in words:
            v = self.ini.get(section, w, None)
            if v is not None:
                return v  # maybe empty string, if no value for keyword given.
        if not noWarning:
            print('warning getFromInifile: no value found, ' \
                  'words: %s, section: %s, module: %s' % \
                          (words, section, self.__module__))
        return None # if keyword not found


    def setInInifile(self, section, key, value):
        """set new value in inifile
        """
        if self.ini is None:
            self.error('no valid inifile')
        self.ini.set(section, key, value)
        self.ini.writeIfChanged()
        

    def getName(self):
        if "name" in dir(self):
            name = self.name
            if name:
                return self.name
        
        n = self.__module__
        if n[0] == "_":
            n = n[1:]
        if n.find("_") > 0:
            n = n.replace("_", " ")
        return n
    GetName = getName   # consistency with Bart Jan

    def GetDictionaries(self):
        inisections = self.ini.get()
        d = {}
        for listname in self.validLists:
            dictname = '%sDict'% listname
            if dictname in dir(self):
                D = getattr(self, dictname)
                if isinstance(D, dict):
                    d[listname] = D.copy()
            elif listname in inisections:
                D = {}
                for key in self.ini.get(listname):
                    D[key] = self.ini.get(listname, key)
                d[listname] = D.copy()
        return d

    def makeDefaultInifile(self, inifile=None, enxVersion=None):
        """initialize as a starting example the inifile

        This default only sets in the section "general"  the key
        "initial on" to 0 or off (so grammar is initial off)         

        """       
        inifile = inifile or self.inifile
        print('----------making new default inifile %s'% inifile)
        rwfile = readwritefile.ReadWriteFile()
        if enxVersion:
            t = rwfile.readAnything(enxVersion)
            # t = open(enxVersion, 'r').read()
            rwfile.writeAnything(inifile, t)
            # open(inifile, 'w').write(t)
            
            self.ini = inivars.IniVars(inifile, repairErrors=1)
            self.ini.delete('grammar name')
            self.ini.delete('grammar words')
            self.ini.set('grammar name', 'name', '')
            self.ini.set('an instruction', 'intro', 'The english inifile is taken as example for this new language inifile for "%s"'% self.language)
            self.ini.set('an instruction', 'note 1', 'Translate [grammar name] and [grammar words] (right side of =)')
            self.ini.set('an instruction', 'note 2', 'Prevent quotes in names')
            self.ini.set('an instruction', 'note 3', 'Translate words in other sections as appropriate, see also Unimacro website...')
            self.ini.set('an instruction', 'note 4', 'If this is a new language for existing grammar files,')
            self.ini.set('an instruction', 'note 5', 'please contact the Unimacro developers to publish your translation in future versions!')
            self.ini.set('an instruction', 'note 6', 'This section can be deleted after reading')
        else:
            rwfile.writeAnything(inifile, '\n')
            # open(inifile, 'w').write('\n')
            self.ini = inivars.IniVars(inifile, repairErrors=1)
            self.ini.set('general', 'initial on', '1')
            self.ini.set('an instruction', 'intro', 'There was no sample/example inifile for this grammar.')
            self.ini.set('an instruction', 'note 1', 'Please fill in your own sections if relevant')
            if self.language == 'enx':
                self.ini.set('an instruction', 'note 2', 'If this is a grammar useful to others, please consider publishing it in the Unimacro area,')
                self.ini.set('an instruction', 'note 3', 'you can ontact the Unimacro developers through the Unimacro website for this.')
                self.ini.set('an instruction', 'note 4', 'This section can be deleted after reading')
            else:
                self.ini.set('an instruction', 'note 2', 'Please consider to write your grammar in English first and then make a translation to "%s"'% self.language)
                self.ini.set('an instruction', 'note 3', 'This section can be deleted after reading')
        
        self.fillDefaultInifile(self.ini)
        self.ini.writeIfChanged()
        self.ini.close()
        name = self.getName()
        print(f'Please edit this new inifile: {self.ini._file}, possibly by calling "edit {name}')

    def fillDefaultInifile(self, ini):
        """set initial settings for ini file, overload!

        """
        print('----------standard filling of default ini file for module: %s'% self.__module__)
        ini.set('general', 'initial on', '1')
        name = self.__module__.strip('_')
        name = name.replace("_", " ")
        ini.set('grammar name', 'name', name)
        
        if hasattr(self, "validLists") and hasattr(self, 'iniIgnoreGrammarLists'):
            for l in self.validLists:
                if not l in self.iniIgnoreGrammarLists:
                    ini.set(l)
        ini.write()
                
    def error(self, message):
        """gives an error message, and leaves variable Error

        currently prints a message, and switches off the grammar
        """
        print('---- error in module %s: %s'% (self, message))
        raise UnimacroError('error %s in module %s: %s'% \
                            (sys.exc_info()[0], self.GetName(), message))
                            

        
    def removeFromList(self, L, toRemove):
        """removes in place items from list, calls error routine if missing things

        if item to remove is not in L, pass, raise no error.
        
        returns nothing!, list L list changed in place
             """
        if not isinstance(L, list):
            self.error(f'not a list in "removeFromList": "{L}", type: {type(L)}')
            return

        if not L:
            if not toRemove:
                return
            print(f'{self.name}, removedFromList: list is empty, but toRemove is not empty: {toRemove}')
            return
        if not toRemove:
            return
        if isinstance(toRemove, str):
            try:
                L.remove(toRemove)
            except:
                pass
                # self.error('removeFromList, item to remove is not in list: %s'% toRemove)
                # return
        elif isinstance(toRemove, (list, tuple)):
            for r in toRemove:
                try:
                    L.remove(r)
                except:
                    pass
                    # self.error('removeFromList, item to remove is not in list: %s'% r)
                    # return
        else:
            self.error('removeFromList, invalid type for variable "toRemove": %s'% toRemove)
            return
        

    ## Here are the grammar rules, that interpret a given number:
    def gotResults___1to9(self,words,fullResults):
        numWords = self.getNumbersFromSpoken(words, asStr=1)
        self._sofar = self._sofar + ''.join(numWords)
    gotResults___0to9 = gotResults___1to9        

    def gotResults___1to99(self,words,fullResults):
        numWords = self.getNumbersFromSpoken(words, asStr=1)
        #print '1to99, words: %s, sofar: %s, add: %s'% (words, self._sofar, numWords)
        if self.language != 'nld':
            # make '40 3' -->> '43' etc:
            L = []
            # lenWords = len(numWords)
            for w in numWords:
                if len(w) == 1:
                    if L and int(L[-1]) and L[-1][-1] == '0':
                        # print('scratch away one 0, before: %s'% L)
                        L[-1] = L[-1][:-1]  ## scratch away one 0, 40 3 must become 43, so list element '40' becomes '4'
                        # print('scratch away one 0, after: %s'% L)
                L.append(w)
            numWords = L

        # if self.prevRule == "__hundreds":
        #     print '1to99, numWords: %s, prev==hundreds, self._hundreds: %s, sofar: %s'% (numWords, self._hundreds, self._sofar)
        #     num = numWords[0]
        #     # do numWords with last word so 100 + 3 becomes 103, and finish hundreds.
        #     num = int(self._hundreds) + int(numWords[0])
        #     numStr = '%3d'% num
        #     self._sofar += numStr
        #     self._hundreds = ''
        #     
        # 
                
                
        self._sofar = self._sofar + ''.join(numWords)
        #print 'sofar after rule: %s'% self._sofar

    gotResults___0to99 = gotResults___1to99
    gotResults___10to99 = gotResults___1to99


    def gotResults___hundreds(self,words,fullResults):
        if self._hundreds:
            print('hundreds already: hundreds: %s, sofar: %s, words: %s'% (self._hundreds,self._sofar, words))
        assert not self._hundreds
        if self._sofar:
            self._hundreds = int(self._sofar)*100
        else:
            self._hundreds = 100
        self._sofar = ''

    def gotResults___thousands(self,words,fullResults):
        assert not self._thousands
        if self._sofar:
            sofar = int(self._sofar)
            if self._hundreds:
                sofar = self._hundreds + sofar
            
            self._thousands = sofar*1000
        elif self._hundreds:
            self._thousands = self._hundreds*1000
        else:
            self._thousands = 1000
        self._sofar = ''
        self._hundreds = 0
        

    def gotResults___millions(self,words,fullResults):
        assert not self._millions
        if self._sofar:
            sofar = int(self._sofar)
            if self._hundreds:
                sofar = self._hundreds + sofar
            elif self._thousands:
                sofar = self._thousands + sofar
                
            self._millions = sofar*1000000
        else:
            self._millions = 1000000
        self._sofar = ''
        self._hundreds = self._thousands = 0

    def gotResults_float(self,words,fullResults):
        
        if self.hasCommon(words, ['comma', 'komma']):
            self._decimal = ','
        elif self.hasCommon(words, ['point', 'dot', 'punt']):
            self._decimal = '.'
        else:
            raise UnimacroError('no valid word for float separator found: %s'% words)
        self.collectNumber(part=1) # before the , or .


    def gotResults_integer(self,words,fullResults):
        pass  # only having subrules... Edit, number

    def waitForNumber(self, name, length=None):
        """set up variable name "name", to be filled with a number

        optional the wanted length

        also initialise the necesarry instance variables
        """        
        self._waitForNum = name
        self.wantedLength = length
        self._integerPart = self._millions = self._thousands = self._hundreds = 0
        self._sofar = ''
        self._decimal = ''
        self.message = '' # error messages can be stored here...
        # just in case it is called in the grammar logic:
        setattr(self, name, '')
        
        
    def collectNumber(self, part=0, asNumber=0):
        """if you're waiting for a number get it, and reset the parts
        """
        if '_waitForNum' in dir(self) and self._waitForNum:
            N = self._millions
            N += self._thousands
            N += self._hundreds
            if N:
                if self._sofar:
                    N += int(self._sofar)
                # losing leading zeros
                Nstr = str(N)
            elif self._sofar:
                N = int(self._sofar)
                Nstr = self._sofar
            else:
                return  # nothing to be done (yet)

            if part:
                # collect the first part of the number:
                self._integerPart = N
            else:
                if '_integerPart' in dir(self) and self._integerPart:
                    # floatingpoint numbers always return in string:
                    result = '%s%s%s'% (self._integerPart, self._decimal, Nstr)
                    setattr(self, self._waitForNum, result)
                    if self.wantedLength and len(result) != self.wantedLength:
                        self.message = 'length of result (%s) does not match wanted length (%s), number: "%s"'% \
                                        (len(result), self.wantedLength, result)
                else:
                    # do the integer number:
                    if self.wantedLength and len(Nstr) != self.wantedLength:
                        self.message = 'length of result (%s) does not match wanted length (%s), number: "%s"'% \
                                        (len(Nstr), self.wantedLength, Nstr)
                    if asNumber:
                        setattr(self, self._waitForNum, N)
                    else:
                        setattr(self, self._waitForNum, Nstr)
                        
                self._integerPart = 0
                self._waitForNum = ''
                
            # reset the whole bunch:
            self._millions = self._thousands = self._hundreds = 0
            self._sofar = ''
        return
        #### end of number things        

    #### search things:==============================================

    def stopSearch(self, progInfo=None):
        """action after the search"""
        if not progInfo:
            progInfo = unimacroutils.getProgInfo()
        if beforeOrAfter == 'before':
            if lastSearchDirection == 'up':
                s = '<<leftafterbacksearch %s>>'% len(lastSearchText)
            else:
                s = '<<leftafterforwardsearch %s>>'% len(lastSearchText)
        elif beforeOrAfter == 'after':
            if lastSearchDirection == 'up':
                s = '<<rightafterbacksearch %s>>'% len(lastSearchText)
            else:
                s = '<<rightafterforwardsearch %s>>'% len(lastSearchText)
        else:
            return
        print('doing action in stop search')
        action(s, progInfo=progInfo)
            
    def getLastSearchDirection(self):
        """get global var lastSearchDirection"""
        return lastSearchDirection

    def setLastSearchDirection(self, direc):
        """set global var lastSearchDirection"""
        #pylint:disable=W0603
        global lastSearchDirection
        if direc not in ['up', 'down']:
            raise UnimacroError('invalid search direction: "%s"'% direc)
        lastSearchDirection = direc
    

    def searchForText(self, direction, text=None, progInfo=None, modInfo=None,
                      beforeafter=None, insert=None, extend=None):
        """search up or down to text, invoke actions, for program differences

        if text is None, previous text is searched for
        beforeafter: None == ignore,  before1, after=2, leave after the selection.
        """
        #pylint:disable=W0603
        global lastSearchText, lastSearchDirection, beforeOrAfter
        # pass progInfo to the actions, to keep them from changing inside the stuff:
        if progInfo is None:
            progInfo = unimacroutils.getProgInfo(modInfo)
        _progpath, prog, _title, _topchild, _classname, _hndle = progInfo
        if prog == 'excel':
            connectExcel(progInfo)
        elif prog == 'winword':
            connectWinword(progInfo)
        else:
            disconnectExcelOrWord()

        if text:
            if extend:
                lastSearchText = lastSearchText + text
            elif insert:
                lastSearchText = text + lastSearchText
            else:
                lastSearchText = text
                
        elif not lastSearchText:
            res = action("<<searchalwayscontinue>>", progInfo=progInfo)
            if not res:
                self.DisplayMessage('search command, but no search text yet')
                # if call came from generic_movement, in exclusive mode, cancel now:
                self.cancelMode()
                return None
        if beforeafter:
            if beforeafter == 'for':
                beforeOrAfter = None
            elif beforeafter in ('before', 'after'):
                beforeOrAfter = beforeafter
            else:
                self.DisplayMessage('search command, beforeafter has invalid value: %s'% beforeafter)
                # if call came from generic_movement, in exclusive mode, cancel now:
                self.cancelMode()
                return None
                

        # remember the last direction:    
        lastSearchDirection = direction
        if text:
            if appProgram == 'excel':
                if direction == 'up':
                    sdir = 2
                else:
                    sdir = 1
                ac = app.ActiveCell
                sheet.Cells.Find(What=lastSearchText,After=ac, SearchDirection=sdir).Activate()
               
            # search with new text:
            elif direction == 'up':
                lastSearchDirection = direction
                res = action("<<startbacksearch>>", progInfo=progInfo)
                if res:
                    # back search implemented in this program:
                    keystroke(text)
                    action("<<searchgo>>", progInfo=progInfo)
                else:
                    # 
                    self.DisplayMessage('search from top for "%s"'% text)
                    action("<<documenthome>>", progInfo=progInfo)
                    self.searchForText('down', text)
                    return -1  # changed direction
            else:
                action("<<startsearch>>", progInfo=progInfo)
                keystroke(lastSearchText, progInfo=progInfo)
                action("<<searchgo>>", progInfo=progInfo)
        else:
            # continue search with previous text:
            if appProgram == 'excel' and lastSearchText:
                if direction == 'up':
                    sdir = 2
                else:
                    sdir = 1
                ac = app.ActiveCell
                sheet.Cells.Find(What=lastSearchText,After=ac, SearchDirection=sdir).Activate()
            elif direction == 'up':
                if beforeOrAfter == 'after':
                    action("<<leftbeforebacksearch %s>>"% len(lastSearchText), progInfo=progInfo)
                res = action("<<searchback>>", progInfo=progInfo)
                if not res:
                    # back search failed, do forward search from top
                    self.DisplayMessage('search from top')
                    print('start in top instead of back search')
                    action("<<documenthome>>", progInfo=progInfo)
                    self.searchForText('down', progInfo=progInfo)
                    return -1
            else:
                if beforeOrAfter == 'before':
                    action("<<rightbeforeforwardsearch %s>>"% len(lastSearchText), progInfo=progInfo)
                res = action("<<searchforward>>", progInfo=progInfo)

        # should return 0 if all was well, -2 if fail (-1 is for change direction)
        fail = self.searchFailed(progInfo=progInfo)
        if fail == -2:
            self.cancelMode()
            action("<<searchfailed>>", progInfo=progInfo)
        return fail            

    def searchFailed(self, progInfo=None):
        """signal if search was fail, invalid string or end of document"""
        if not progInfo:
            return None # no information
        # old info:
        _progpath, prog, title, toporchild, _classname, _hndle = progInfo
        nprogInfo = unimacroutils.getProgInfo() # for checking if window or title changed
        if (prog == 'natspeak' and title.find('dragonpad') >= 0) or \
           (prog == 'notepad' and title.find('notepad') >= 0) or \
           (prog == 'iexplore'):
            # hit if title changes, notepad 
            if progInfo != nprogInfo:
                print('%s: window changed, cancel search'% prog)
                return -2 # cancelMode, because window title changed
        elif (prog == 'winword' and toporchild == 'top' and nprogInfo[2] == 'child'):
            print('%s: search failed, cancel search'% prog)
            return -2 # cancelMode, because window title changed
        return None

    def searchMarkSpot(self, progInfo=None):
        """Mark the place where you can return with searchGoBack"""
        #pylint:disable=W0603
        global comingFrom
        if progInfo is None:
            progInfo = unimacroutils.getProgInfo()
        _progpath, prog, _title, _topchild, _classname, _hndle = progInfo
        if prog == 'excel':
            connectExcel(progInfo)
            ac = app.ActiveCell
            comingFrom = ac.Address
        elif prog == 'winword':
            connectWinword(progInfo)
            if appProgram == 'winword':
                doc.Bookmarks.Add("unimacrosearch")
                print('search grammar, word bookmark set')

    def searchGoBack(self, progInfo=None):
        """go back to previous place, excel or word"""
        if progInfo is None:
            progInfo = unimacroutils.getProgInfo()
        _progpath, prog, _title, _topchild, _classname, _hndle = progInfo
        if prog == 'excel':
            connectExcel(progInfo)
        elif prog == 'winword':
            connectWinword(progInfo)
        else:
            # eg ultraedit knows this:
            action("<<searchgoback>>")
        
        if appProgram == 'excel':
            print('search go back to: "%s"'% comingFrom)
            sheet.Range(comingFrom).Select()
        elif appProgram == 'winword':
            # What -1 = wdGotoBookmark:
##            print 'doc: %s'% doc
##            print 'doc.range: %s'% doc.Range
##            doc.Range().GoTo(-1,Name="unimacrosearch")
            print('search go back does not work yet')
            
    def getTopOrChild(self, progInfo=None, childClass=None):
        """return true if top window or child behaves like top
        and False if child window or top behaves like child
        
        complicated function, which depends on the unimacroactions.ini settings. 

        As a shortcut: childClass can be set to "#32770" (file open etc dialogs),
        and then always return False, child, except even when rule in actions.ini says different...
        
        """
        if progInfo is None:
            progInfo = unimacroutils.getProgInfo()
        
        assert len(progInfo) == 6
        
        istop = progInfo.toporchild == 'top'
        if istop:
            if actions.topWindowBehavesLikeChild( progInfo ):
                istop = False
            elif childClass and progInfo.classname == childClass:
                if actions.childWindowBehavesLikeTop( progInfo ):
                    self.debug('getTopOrChild: top mode, altough of class "%s", but because of "child behaves like top" in "actions.ini"'% childClass)
                    istop = True
                else:                
                    self.debug('getTopOrChild: child mode, because of className "%s"'% childClass)
                    istop = False
        else:
            if actions.childWindowBehavesLikeTop( progInfo ):
                self.debug('getTopOrChild: top mode, because but because of "child behaves like top" in "actions.ini"')
                istop = True
        return istop

    def doWaitForMouseToStop(self):
        """wait for mouse to stop moving (before a click can be performed)
        
        used at click command in several grammars (excel, keystrokes) and in _lines.
        """
        if actions.do_MOUSEISMOVING():
            if actions.do_WAITMOUSESTOP():
                return 1
            print("Mouse is not steady, so cannot click")
            return 0
        ## was not moving at all:
        return 1

DocstringGrammarAncestor=IniGrammar    
class DocstringGrammar(DocstringGrammarAncestor):
    """grammar base which reads the rules from the docstrings of the
    rule functions
    """
    __inherited=DocstringGrammarAncestor
    nIndentSubrule = 4
    giveFullResults = 0
    
    def __init__(self, **kw):
        self.ruleFuncsDict = {} # records the functions corresponding to rules
        gramSpecFromDocstring = self.buildGramSpecFromDocstrings() or ""
        try:
            classGramSpec = copy.copy(self.gramSpec)
            if not isinstance(classGramSpec, str):
                classGramSpec = '\n'.join(classGramSpec)
        except AttributeError:
            classGramSpec = ""

        totalgramSpec = gramSpecFromDocstring + '\n' + classGramSpec
        self.gramSpec = totalgramSpec.strip()
        self.originalGramSpec = self.gramSpec
        self.__inherited.__init__(self, **kw)

    def buildGramSpecFromDocstrings(self):
        L = []
        posfunc = []
        for item in dir(self):
            parts = item.split("_", 1)
            if len(parts) == 2 and parts[0] in ( 'rule', 'subrule', 'importedrule'):
                func = getattr(self, item)
                #prin   t 'item: %s, type: %s'% (item, type(func))
                if callable(func):
                    docstring = func.__doc__
                    if docstring is None or not docstring.strip():
                        if parts[0] in ('rule', 'subrule'):
                            raise ValueError('(sub)rule %s must have a docstring'% item)
                    lineno = func.__code__.co_firstlineno
                    posfunc.append( (lineno, item) )
        #print 'posfunc: %s'% posfunc
        if not posfunc:
            return ''
        posfunc.sort()
        #print 'posfunc: %s'% posfunc
        for dummy, item in posfunc:
            parts = item.split("_", 1)
            rulename = parts[1]
            func = getattr(self, item)
            docstring = func.__doc__ or ''
            ruledef = self.getRuleDefFromDocstring(docstring, rulename, parts[0])
            self.ruleFuncsDict[rulename] = func
            L.append(ruledef)
        #print 'ruleFuncsDict: %s'% self.ruleFuncsDict.keys()
        return '\n'.join(L)

    def getRuleDefFromDocstring(self, doc, rulename, typeOfRule):
        #pylint:disable=W0621
        L = []
        
        exported = typeOfRule == 'rule'
        imported = typeOfRule == 'importedrule'
        doclines = doc.split('\n')
        doclines = self.adjustSpacingOfDocList(doclines)
        hadStart = 0
        lastLine = None
        rulePart = ''
        lenRulePart = 0
        for i, line in enumerate(doclines):
            spaces = ' '*(len(line) - len(line.lstrip()))
            line = line.strip()
            if line == '' or line.startswith('#'):
                L.append(line)
                continue
            if hadStart:
                L.append(' '*lenRulePart + spaces + line)
                lastLine = i
            else:
                if exported:
                    rulePart = '<%s> exported = '% rulename
                    lenRulePart = len(rulePart)
                    rule = spaces + rulePart + line
                else:
                    rulePart = '<%s> = '% rulename
                    lenRulePart = len(rulePart)
                    rule = spaces + rulePart + line
                hadStart = 1
                lastLine = i
                #print 'item:', rulename, ' rule: ', rule
                L.append(rule)
        if lastLine is None:
            if imported:
                rule = '<%s> imported;'% rulename
                L.append(rule)
            else:
                raise ValueError('no ruledefinition found for rule: %s'% rulename)
        else:
            if imported:
                raise ValueError('imported rule may have no ruledefinition: %s'% rulename)
            L[lastLine] = self.addSemicolonToRule(L[lastLine])
            
        if typeOfRule == 'subrule' and self.nIndentSubrule:
            spaces = ' '*self.nIndentSubrule
            L = [spaces+l for l in L]
        return '\n'.join(L)

    def addSemicolonToRule(self, line):
        """add a semicolon after the line, before comments
        """
        parts = line.split("#", 1)
        if len(parts) == 1:
            line = line.rstrip()
            if line.endswith(';'):
                return line
            return line + ';'
        # else:
        rulePart = parts[0].rstrip()
        nSpaces = len(parts[0]) - len(rulePart)
        if rulePart.endswith(';'):
            return line
        spaces = ' '*(nSpaces)
        return rulePart + ";" + spaces + "#" + parts[1]
                
    def adjustSpacingOfDocList(self, docList):
        """remove consistent leading spaces from subsequent lines
        also remove empty first and/or empty last line
        """
        lenLeader = 11
        if not docList:
            return docList
        nSpaces = [len(d) - len(d.lstrip()) for d in docList]
        nSpacesLineOne = nSpaces[0]
        del nSpaces[0]
        if not nSpaces:
            return [docList[0].strip()]
        if len(nSpaces) > 0 and not docList[-1].strip():
            del nSpaces[-1]
            del docList[-1]
        if not nSpaces:
            return [docList[0].strip()]
           
        minSpaces = min(nSpaces)
        
        if minSpaces >= nSpacesLineOne + lenLeader:
            # only strip the leader part for nice presentation:
            D = []
            nToStrip = nSpacesLineOne + lenLeader
            for i, d in enumerate(docList):
                if i:
                    D.append(d[nToStrip:])
                else:
                    D.append(d)
        else:
            # strip according to minSpaces, strip also item 0
            D = []
            for i, d in enumerate(docList):
                if i:
                    d = d[minSpaces:]
                    D.append(d)
                else:
                    D.append(d.lstrip())
        return D
    
    def callRuleResultsFunctions(self, seqsAndRules, fullResults):
        """call the rule functions, can be overloaded (eg in DocstringGrammar)
        
        Also give self.nextRule (the name) self.nextWords, self.prevRule, self.prevWords
        so the result of the adjacent rules are known
        
        the new style functions prevail over the gotResults_ functions, ie
        the latter are only visited if the former fail.
        """
        ruleName, ruleWords = None, None
        # print(f'seqsAndRules = {seqsAndRules}')

        for i, x in enumerate(seqsAndRules):
            if i == 0:
                ruleName, self.nextRule = None, x[1]
                ruleWords, self.nextWords = [], x[0]
            else:
                self.prevRule, ruleName, self.nextRule = ruleName, self.nextRule, x[1]
                self.prevWords, ruleWords, self.nextWords = ruleWords, self.nextWords, x[0]
                # print(f'ruleName: {ruleName}, words: {ruleWords}, FR: {fullResults}')
                self.doRuleIfExists( ruleName, ruleWords, fullResults)

        self.prevRule, ruleName, self.nextRule = ruleName, self.nextRule, None
        self.prevWords, ruleWords, self.nextWords = ruleWords, self.nextWords, []
        # print(f'ruleName: {ruleName}, words: {ruleWords}, FR: {fullResults}')
        self.doRuleIfExists(ruleName, ruleWords, fullResults)

    def doRuleIfExists(self, ruleName, ruleWords, fullResults):
        """overload from natlinkutils, calls for rule_ or gotResults_
        """
        if ruleName in self.ruleFuncsDict:
            # docstring style:
            func = self.ruleFuncsDict[ruleName]
            func(ruleWords)
        else:
            # classic (gotResults) style:                
            self.callIfExists( 'gotResults_'+ruleName, (ruleWords, fullResults) )
        
    def __str__(self):
        return '<docstringgr: %s>'% self.GetName()

        
#number things, to be called from IniGrammar and from a user grammar, gives an integer:
numberGrammar = {}
numberGrammar['nld'] = """
<__1to99> = {n1-99};
<__0to99> = {n0-99};
<__0to9> = {n0-9};
<__10to99> = {n10-99};
<__hundreds> = honderd | <__1to99> honderd | honderd <__1to99> | <__1to99> honderd <__1to99> ;
<__thousands> = duizend | (<__1to99>|<__hundreds>) duizend | duizend (<__1to99>|<__hundreds>) |
                   (<__1to99>|<__hundreds>) duizend  (<__1to99>|<__hundreds>);
<__millions> = miljoen | miljoen (<__thousands>|<__hundreds>|<__1to99>) | (<__hundreds>|<__1to99>) miljoen |
                (<__hundreds>|<__1to99>) miljoen (<__thousands>|<__hundreds>|<__1to99>) ;
<integer> =  <__0to9>+ |  <__10to99>|
             <__0to9><__10to99>[<__0to99>+] |
             <__hundreds> | <__thousands> | <__millions>;
<float> = <integer> (punt|komma) (<__10to99>|<__0to9>+);
"""

numberGrammar['enx'] = """
<__0to99> = {n0-19} | {n20-90} | {n20-90}{n1-9};
<__1to99> = {n1-19} | {n20-90} | {n20-90}{n1-9};

<__hundreds> = hundred | <__1to99> hundred | hundred <__1to99> | <__1to99> hundred <__1to99> ;
<__thousands> = thousand | (<__1to99>|<__hundreds>) thousand | thousand (<__1to99>|<__hundreds>) |
                   (<__1to99>|<__hundreds>) thousand  (<__1to99>|<__hundreds>);
<__millions> = million | million (<__thousands>|<__hundreds>|<__1to99>) | (<__hundreds>|<__1to99>) million |
                (<__hundreds>|<__1to99>) million (<__thousands>|<__hundreds>|<__1to99>) ;
<integer> = <__0to99>+ | <__hundreds> | <__thousands> | <__millions>;
<float> = <integer> (point|dot) <__0to99>+;
"""
numberGrammar['ita'] = numberGrammar['deu'] = numberGrammar['nld']

numberGrammarTill999 = {}
numberGrammarTill999['nld'] = """
<__1to99> = {number1to99};
<__0to99> = {number0to99};
<__0to9> = {n0-9};
<__1to9> = {n1-9};
<__10to99> = {n10-99};
<__hundreds> = honderd | <__1to9> honderd | honderd <__1to99> | <__1to9> honderd <__1to99> ;
<integer> = <__0to9>+ | <__10to99> | 
             <__1to9> <__10to99> | <__hundreds> ;
<float> = <integer> (punt|komma) (<__10to99>|<__0to9>+);"""
numberGrammarTill999['enx'] = """
<__0to99> = {n0-19} | {n20-90} | {n20-90}{n1-9};
<__1to99> = {n1-19} | {n20-90} | {n20-90}{n1-9};
<__10to99> = {n10-19} | {n20-90} | {n20-90}{n1-9};
<__1to9> = {n1-9};
<__0to9> = {n0-9};
<__hundreds> = hundred | <__1to9> hundred | hundred <__1to99> | <__1to9> hundred <__1to99> ;
<integer> = <__0to9>+ | <__10to99> | <__1to9> <__1to99> | <__hundreds>;
<float> = <integer> (point|dot) <__0to99>+;
"""
numberGrammarTill999['ita'] =numberGrammarTill999['deu'] = numberGrammarTill999['nld']

numberGrammarTill999999 = {}
numberGrammarTill999999['nld'] = """
<__1to99> = {n1-99};
<__0to99> = {n0-99};
<__0to9> = {n0-9};
<__10to99> = {n10-99};
<__hundreds> = honderd | <__1to99> honderd | honderd <__1to99> | <__1to99> honderd <__1to99> ;
<__thousands> = duizend | (<__1to99>|<__hundreds>) duizend | duizend (<__1to99>|<__hundreds>) |
                   (<__1to99>|<__hundreds>) duizend  (<__1to99>|<__hundreds>);
<integer> = <__0to9>+ | <__10to99>|
             <__0to9><__10to99>[<__0to99>]  | <__hundreds> | <__thousands>;
<float> = <integer> (punt|komma) (<__10to99>|<__0to9>+);
"""

numberGrammarTill999999['enx'] = """
<__0to99> = {n0-19} | {n20-90} | {n20-90}{n1-9};
<__1to99> = {n1-19} | {n20-90} | {n20-90}{n1-9};
<__hundreds> = hundred | <__1to99> hundred | hundred <__1to99> | <__1to99> hundred <__1to99> ;
<__thousands> = thousand | (<__1to99>|<__hundreds>) thousand | thousand (<__1to99>|<__hundreds>) |
                   (<__1to99>|<__hundreds>) thousand  (<__1to99>|<__hundreds>);
<integer> = <__0to99>+ | <__hundreds> | <__thousands>;
<float> = <integer> (point|dot)  <__0to99>+;
"""
numberGrammarTill999999['ita'] = numberGrammarTill999999['deu'] = numberGrammarTill999999['nld']

# to make exact number of digits (Dutch, for Amsterdam Stadsdeel Zuid)
numberGrammarFixedDigits = {}
numberGrammarFixedDigits['nld'] = """
<numbertwodigits> = {n0-9}+ | {n10-99};
<numberthreedigits> = {n0-9}+ | <__hundreds> | {n0-9} <numbertwodigits>;
"""
numberGrammarThreeDigits = {}

numberGrammarFourDigits = {}

#connect to programs:
def connectExcel(progInfo):
    """connect to excel and leave parameters in global vars"""
    #pylint:disable=W0603
    global app, appProgram, sheet
    prog = progInfo.prog
    
    if prog == 'excel':
        if appProgram != 'excel' or not app:
            app = win32com.client.Dispatch('Excel.Application')
        if app:
            sheet=app.ActiveSheet
            appProgram = 'excel'
            print('excel application collected')
        else:
            print('excel not connected')
            app = None
    else:
        app = None
        appProgram = ''
    return app

def connectWinword(progInfo):
    """connect to word and leave parameters in global vars"""
    #pylint:disable=W0603
    global app, appProgram, doc
    prog = progInfo.prog
    
    if prog == 'winword':
        if appProgram != 'winword' or not app:
            app = win32com.client.Dispatch('Word.Application')
        if app:
            doc = app.ActiveDocument
            appProgram = 'winword'
            print('winword application collected')
        else:
            print('winword not connected')
            app = None
            appProgram = ''
    else:
        app = None
        appProgram = ''
    return app
       
def disconnectExcelOrWord():
    """release connection with one of these"""
    #pylint:disable=W0603
    global app, appProgram, doc, sheet
    if app:
        app = None
        appProgram = ''
        sheet = None
        doc = None
 
# def formatListColumns(List, lineLen = 70, sort = 0):
#     """formats a list in columns
# 
#     taken from utilsqh, 2011/1/4 QH
# 
#     Uses a generator function "splitList", that gives a sequence of
#     sub lists of length n.
# 
#     The items are separated by at least two spaces, if the list
#     can be placed on one line, the list is comma separated
# 
#     >>> formatListColumns([''])
#     ''
#     >>> formatListColumns(['a','b'])
#     'a, b'
#     >>> formatListColumns(['foo', 'bar', 'longer entry'], lineLen=5)
#     'foo\\nbar\\nlonger entry'
#     >>> formatListColumns(['foo', 'bar', 'longer entry'], lineLen=5, sort=1)
#     'bar\\nfoo\\nlonger entry'
#     >>> print formatListColumns(['afoo', 'bar', 'clonger', 'dmore', 'else', 'ftest'], lineLen=20, sort=1)
#     afoo      dmore
#     bar       else
#     clonger   ftest
#     >>> print formatListColumns(['foo', 'bar', 'longer entry'], lineLen=20)
#     foo   longer entry
#     bar
# 
#     """
#     if sort:
#         List.sort(caseIndependentSort)
#     s = ', '.join(List)
# 
#     # short list, simply join with comma space:
#     if len(s) <= lineLen:
#         return s
# 
#     maxLen = max(list(map(len, List)))
# 
#     # too long elements in list, return "\n" separated string:
#     if maxLen > lineLen:
#         return '\n'.join(List)
# 
# 
#     nRow = len(s)/lineLen + 1
#     lenList = len(List)
# 
#     # try for successive number of rows:
#     while nRow < lenList//2 + 2:
#         lines = []
#         for i in range(nRow):
#             lines.append([])
#         maxLenTotal = 0
#         for parts in splitList(List, nRow):
#             maxLenParts = max(list(map(len, parts))) + 2
#             maxLenTotal += maxLenParts
#             for i in range(len(parts)):
#                 lines[i].append(parts[i].ljust(maxLenParts))
#         if maxLenTotal > lineLen:
#             nRow += 1
#         else:
#             
#             # return '\n'.join(map(string.strip, map(string.join, lines)))
#             return '\n'.join([t.strip() for t in [''.join(l) for l in lines]])
#     else:
#         # unexpected long list:
#         return '\n'.join(List)


def splitList(L, n):
    """generator function that splits a list in sublists of length n

    taken from utilsqh, 2011/1/4 QH

    """
    O = []
    for l in L:
        O.append(l)
        if len(O) == n:
            yield O
            O = []
    if O:
        yield O
        