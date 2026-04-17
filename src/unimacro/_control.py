"""Unimacro grammar that controls/shows/traces state of other grammars

"""
# This file is part of a SourceForge project called "unimacro" see
# http://unimacro.SourceForge.net and http://qh.antenna.nl/unimacro
# (c) copyright 2003 see http://qh.antenna.nl/unimacro/aboutunimacro.html
#    or the file COPYRIGHT.txt in the natlink\natlink directory 
#
# _control.py, adapted version of_gramutils.py
# Author: Bart Jan van Os, Version: 1.0, nov 1999
# starting new version Quintijn Hoogenboom, August 2003, for python3 2023
#pylint:disable=C0115, C0116, W0702, R0904, R0911, R0912, R0914, R0915, W0201, W0613, W0107, C0209, E0601, W0602, C0112
#pylint:disable=R1735, W0703, W1203
#pylint:disable=E1101

import os
import filecmp
import shutil
import string
from pathlib import Path
#a global logger for unimacro.  perfectly reasonable to access by name instead.
import logging as l
from logging import Logger
import importlib.metadata as meta
import sys

import natlink
from natlinkcore import loader
from natlinkcore import natlinkstatus

from dtactions import unimacroutils
from dtactions import unimacroactions as actions

from unimacro import natlinkutilsbj as natbj
from unimacro import spokenforms 
from unimacro import __version__ as unimacro_version
from icecream import ic

logger = Logger("_control")
#from unimacro import logger
#from unimacro.logger import ulogger


#for some reason, importing amodule which does this doesn't work.  Likely because natlinkmain must be started first for
#this sublogger natlink.unimacro to work correctly.
#import unimacro as unimacro_l   #bring in so we can add a variable ulogger to the namespace.  
#ulogger : l.Logger = l.getLogger(unimacro_l.logname()) 
#Loggers can be created for any module, and they can propogate to the parent  Logger, or not.
#As an example, this module for the control grammar has its own child logger of unimacro.
#Note an entry point has to be defined as well, in pyproject.toml, so Loggers for various natlink components can be discovered.



#unimacro_l.__dict__['ulogger']=ulogger
#ulogger.debug("natlink.unimacro logger available")

status = natlinkstatus.NatlinkStatus()
natlinkmain = loader.NatlinkMain()
thisDir = str(Path(__file__).parent)



tracecount = list(map(str, list(range(1, 10))))

# #Constants for the UtilGrammar
Normal=0
# Training=1 #obsolete
# Command=2 #obsolete
# Filter=4
# FilterTraining=5
# Display=6
# 
# 
showAll = 1  # reset if no echo of exclusive commands is wished


ancestor = natbj.IniGrammar
class UtilGrammar(ancestor):
    language = status.get_language()
    

    iniIgnoreGrammarLists = ['gramnames', 'tracecount', 'message', 'logger_names'] # are set in this module

    name = 'control'
##    normalSet = ['show', 'edit', 'trace', 'switch', 'message']
##    exclusiveSet = ['showexclusive', 'message']
    # commands for controlling module actions
    specialList = []
    specialList.append("actions")

    # if spokenforms:   ## assume spokenforms is imported!!!
    specialList.append("'spoken forms'")
    specialList.append("loggers")
    if specialList:
        specials = "|" + '|'.join(specialList)
        logger.debug('specialList for "show": %s', specials)
    else:
        specials = ""
    
    gramRules = ['show', 'edit', 'switch', 'showexclusive', 'resetexclusive', 'checkalphabet', 'message','setlogging','loglevel']
    gramDict = {}
    gramDict['show'] = """<show> exported = show ((all|active) grammars |
                        {gramnames} | (grammar|inifile) {gramnames}
                         """ + specials + """);"""
    gramDict['edit'] = """<edit> exported = edit ({gramnames}| (grammar|inifile) {gramnames}"""+ specials +""");"""
    gramDict['switch'] = """<switch> exported = switch ((on|off) ((all grammars)|{gramnames}|grammar {gramnames})|
                            ((all grammars)|{gramnames}|grammar {gramnames})(on|off));"""
    gramDict['showexclusive'] = """<showexclusive> exported = show (exclusive |exclusive grammars);"""
    gramDict['resetexclusive'] = """<resetexclusive> exported = reset (exclusive | exclusive grammars);"""
    gramDict['checkalphabet'] = """<checkalphabet> exported = check alphabet;"""
    gramDict['message'] = """<message> exported = {message};"""
    gramDict['setlogging'] = """<setlogging> exported = {logmodulename} loglevel <loglevel>;"""
    gramDict['loglevel'] = "<loglevel> = (debug|info|warning|error|critical);"


    gramSpec = []
    assert set(gramRules) == set(gramDict.keys())

    if language == 'nld':
        gramDict['checkalphabet'] = """<checkalphabet> exported = controleer alfabet;"""

    for rulename in gramRules:
        gramSpec.append(gramDict[rulename])

    Mode = Normal
    LastMode = Normal
    CurrentWord = 0
    Repeat = 0

    def initialize(self):
        self.setLevel(l.DEBUG)
        # temp set allResults to 0, disabling the messages trick:
        if not self.load(self.gramSpec, allResults=showAll):
            return
        
        self.RegisterControlObject(self)
        self.emptyList('message')
        # at post load
        # allGramNames = self.getUnimacroGrammarNames()
        # self.setList('gramnames', allGramNames)
        self.activateAll()
        self.setMode(Normal)
        self.startExclusive = self.exclusive # exclusive state at start of recognition!
##        if unimacroutils.getUser() == 'martijn':
##            print 'martijn, set exclusive %s'% self.name
##            self.setExclusive(1)
        self.info('---now starting other Unimacro grammars:')



    def unload(self):
        self.UnregisterControlObject()
        ancestor.unload(self)

    def gotBegin(self, moduleInfo):
        #Now is the time to get the names of the grammar objects and
        # activate the list for the <ShowTrainGrammar> rule
        if self.GetGrammarsChangedFlag():
            prevSet = set(self.Lists['gramnames'])
            newSet = set(self.getUnimacroGrammars().keys())
            if prevSet != newSet:
                # debug lines:
                # if newSet - prevSet:
                #     print '_control, added Unimacro grammar(s): %s'% list(newSet - prevSet)
                # if prevSet - newSet:
                #     print '_control, removed Unimacro grammar(s): %s'% list(prevSet - newSet)
                self.setList('gramnames', list(newSet))
            self.ClearGrammarsChangedFlag()
        if self.checkForChanges:
            self.checkInifile()
            
        self.startExclusive = self.exclusive # exclusive state at start of recognition!

    def resetExclusiveMode(self):
        """no activateAll, do nothing, this grammar follows the last unexclusive grammar
        """
        pass
    
    def setExclusiveMode(self):
        """no nothing, control follows other exclusive grammars
        """
        pass
    
    def gotResultsObject(self,recogType,resObj):
        """probably obsolete, mechanism was too complicated
        """
        return

    #Utilities for Filter Modes and other special modes
    def setMode(self,NewMode):
        self.LastMode = self.Mode
        self.Mode = NewMode

    def restoreMode(self):
        self.Mode = self.LastMode
        
    def gotResults_checkalphabet(self,words,fullResults):
        """check the exact spoken versions of the alphabet in spokenforms
        """
        version = status.getDNSVersion()
        _spok = spokenforms.SpokenForms(self.language, version)
        alph = 'alphabet'
        ini = spokenforms.ini
        for letter in string.ascii_lowercase:
            spoken = ini.get(alph, letter, '')
            if not spoken:
                self.info('fill in in "%s_spokenform.ini", [alphabet] spoken for: "%s"'% (self.language, letter))
                continue
            if version < 11:
                normalform = '%s\\%s'% (letter.upper(), spoken)
            else:
                normalform = '%s\\letter\\%s'% (letter.upper(), spoken)
            try:
                natlink.recognitionMimic([normalform])
            except natlink.MimicFailed:
                self.info('invalid spoken form "%s" for "%s"'% (spoken, letter))
                if spoken == spoken.lower():
                    spoken = spoken.capitalize()
                    trying = 'try capitalized variant'
                elif spoken == spoken.capitalize():
                    spoken = spoken.lower()
                    trying = 'try lowercase variant'
                else:
                    continue
                if version < 11:
                    normalform = '%s\\%s'% (letter.upper(), spoken)
                else:
                    normalform = '%s\\letter\\%s'% (letter.upper(), spoken)
                try:
                    natlink.recognitionMimic([normalform])
                except natlink.MimicFailed:
                    self.info('%s fails also: "%s" for "%s"'% (trying, spoken, letter))
                else:
                    self.info('alphabet section is corrected with: "%s = %s"'% (letter, spoken))
                    ini.set(alph, letter, spoken)
        ini.writeIfChanged()
           
    def gotResults_switch(self,words,fullResults):
        #print 'control, switch: %s'% words
        if self.hasCommon(words, 'on'):
            switchOn = True
        elif self.hasCommon(words, 'off'):
            switchOn = False
        else:
            try:
                t = {'nld': '<%s: ongeldig schakel-commando>'% self.GetName()}[self.language]
            except:            
                t = '<%s: invalid switch command>'% self.GetName()
            self.DisplayMessage(t)
            return
        G = self.getUnimacroGrammars()
        Gkeys = list(G.keys())
        if self.hasCommon(words, 'all grammars'):
            for gname, gram in G.items():
                if gram == self:
                    continue
                gram.checkForChanges = 1
                self.switch(gram, gname, switchOn)
        else:
            gname = self.hasCommon(words, Gkeys)
            if gname:
                gram = G[gname]
                if gram != self:
                    self.switch(gram, gname, switchOn)
                    # self never needs switching on
            else:
                self.info('_control switch, no valid grammar found, command: %s'% words)

    def switch(self, gram, gname, switchOn):
        """switch on or off grammar, and set in inifile,
        gram is the grammar object
        gname is the grammar name
        switchOn is True or False
        """
        if gram == self:
            self.error(f'should not be here, do not switch on of off _control {gram}')
            return None
        if switchOn:
            if gram.ini:
                gram.checkInifile()
                gram.ini.set('general', 'initial on', 1)
                gram.ini.write()
                unimacroutils.Wait(0.1)
            else:
                self.error(f'--- ini file of grammar {gname} is invalid, please try "edit {gname}"...')
            gramName = gram.getName()
            unimacro_grammars_paths = self.getUnimacroGrammarNamesPaths()
            try:
                filepath = Path(unimacro_grammars_paths[gramName])
            except KeyError:
                self.error(f'_control, grammar not in unimacro_grammars_paths dict: {gramName}, cannot switchOn')
                return None
            # now reload with force option.
            self.info(f'_control, now reload grammar "{gramName}":')
            natlinkmain.seen.clear()
            natlinkmain.load_or_reload_module(filepath, force_load=True)

            return 1

        # switch off:        
        gram.ini.set('general', 'initial on', 0)
        gram.ini.writeIfChanged()
        gram.cancelMode()  
        gram.deactivateAll()
        # gram.unload()
        self.info('grammar "%s" switched off'% gram.getName())
        return 1

    def gotResults_setlogging(self,words, fullresults):
        """Sets a logger (name in first word) to a new loglevel
        """
        self.debug(f"unimacro logger gotResults_logging_level words: {words} fullResults: {fullresults}")

        loglevel_for = words[0]   # something like natlink, unimacro,... 
        new_level_str_mc,_ = fullresults[-1]
        new_log_level_str = new_level_str_mc.upper()
        #the string should be in the 
        logger_name = self.loggers[loglevel_for]
        new_log_level = l.__dict__[new_log_level_str]

        self.info(f"New Log Level {new_log_level_str} for logger {logger_name}")
        t_logger=l.getLogger(logger_name)
        t_logger.setLevel(new_log_level)

    # def gotResults_loglevel(self,words,fullresults):
    #     """
    #     """
    #     self.debug(f"gotResults_loglevel words: {words} fullResults: {fullresults}")
        
    
    def gotResults_showexclusive(self,words,fullResults):

        All = 0
        name = 'exclusive grammars'
        if len(name)>0:                
            Start=(' '.join(name),[])
        else:
            Start=()
        # fix state at this moment (in case of Active grammars popup)
        self.info(f'_control, showexclusive, exclusiveGrammars: {natbj.exclusiveGrammars}')
        if natbj.exclusiveGrammars:
            Exclusive = 1
            self.BrowsePrepare(Start, All, Exclusive)
            T = ['exclusive grammars:']
            for e in natbj.exclusiveGrammars:
                T.append('\t'+e)
            T.append('\t'+self.name)
            T.append('')
            T.append('')
            T.append("Note: exclusive mode is still on, so the buttons of this dialog cannot be clicked by voice.")
            T.append('')
            T.append("Reset the exclusive mode by toggling the microphone")
            T.append('or by calling the command "reset exclusive mode"')
            T.append('')
            T.append("Show details of exclusive Unimacro grammars?")
            msg = '\n'.join(T)
            if actions.YesNo(msg, "Exclusive grammars", icon="information", defaultToSecondButton=1):
                self.BrowseShow()
        else:
            self.DisplayMessage('no exclusive grammars')
            

    def gotResults_resetexclusive(self,words,fullResults):
        self.info('reset exclusive')
        exclGrammars = natbj.getExclusiveGrammars()
        if exclGrammars:
            T = ['exclusive grammars:']
            for name, gram in exclGrammars.items():
                T.append(name)
                gram.cancelMode()
            T.append(self.name)
            T.append('... reset exclusive mode')
            self.DisplayMessage(' '.join(T))
            self.DisplayMessage('reset exclusive mode OK')
        else:
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
        self.debug(f"gotResults_show words: {words} full results: {fullResults}")
        # special case for actions:
        if self.hasCommon(words, 'actions'):
            actions.showActions(comingFrom=self, name="show actions")
            return
        if self.hasCommon(words, 'spoken forms'):
            spokenforms.showSpokenForms(comingFrom=self, name="show spoken forms", language=self.language)
            return
        if self.hasCommon(words, 'exclusive'):
            G = self.getExclusiveGrammars()
            exclNames = [gname for gname, gram in G.items() if gram.isExclusive()]
            self.info(f'exclusive grammars (+ control) are: {exclNames}')
            self.gotResults_showexclusive(words, fullResults)
            return
        if self.hasCommon(words,"loggers"):
            self.debug("has common words Loggers")
            grammars = self.getUnimacroGrammars()

            msg="\n".join([f'-- {g.getName()}: {g.logger_name()}, loglevel: {l.getLevelName(l.getLogger(g.logger_name()).getEffectiveLevel())}' 
                           for _,g in grammars.items()])
            self.message(msg)
            return


        grammars = self.getUnimacroGrammars()
        gramNames = list(grammars.keys())
        self.info("gramNames")
        self.info(f'{gramNames}')
        self.debug(f'_control, gramNames: {gramNames}')
        gramName = self.hasCommon(words, gramNames)
        if gramName:
            grammar = grammars[gramName]
            if not grammar.isActive():
                # off, show message:
                self.offInfo(grammar)
                return
            if not self.hasCommon(words, 'grammar'):
                grammar.showInifile()
                return
        
        # now show the grammar in the browser application:      
        if gramName:
            name = [gramName]
        else:
            name = words[1:-1]   # 'all' or 'active'
        
        All=1
        if len(name)>0:
            All=self.hasCommon(words, 'all')
            if All:
                All = 1
        Active = self.hasCommon(words, 'active')
        if Active:
            All = 0
        elif All:
            All = 1
        
        if len(name)>0:                
            Start=(' '.join(name),[])
        else:
            Start=()
        # fix state at this moment (in case of Active grammars popup)
        Exclusive = 0
        self.BrowsePrepare(Start, All, Exclusive)
        if All or Active:
            #print 'collect and show active, non-active and non-Unimacro grammars'
            G = self.getUnimacroGrammars()
            # print(f'allGrammars (Unimacro): {G}')
            allGramNames = G.keys()
            self.setList('gramnames', allGramNames)
            activeGrammars = [g for g in G if G[g].isActive()]
            inactiveGrammars = [g for g in G if G[g].isLoaded() and not G[g].isActive()]
            switchedOffGrammars = [g for g in G if not G[g].isLoaded()]
            self.info(f'activeGrammars: {activeGrammars}')
            self.info(f'inactiveGrammars: {inactiveGrammars}')
            self.info(f'switchedOffGrammars: {switchedOffGrammars}')
            # for grammar_name, gram in G.items():
            #     print(f'grammar_name: {grammar_name}, gram: {gram}')
            
                # gram = natbj.allUnimacroGrammars[g]
                # print(f'{grammar_name}, isLoaded: {gram.isLoaded()}, isActive: {gram.isActive()}')
                # 
                # result = getattr(gram, 'isActive')
                # mod_name = gram.__module__
                # # print(f'gram: {grammar_name}, module: {mod_name}')
                # if result:
                #     activeGrammars.append(grammar_name)
                #     if mod_name in otherGrammars:
                #         otherGrammars.remove(mod_name)
                #     else:
                #         print(f'cannot remove from otherGrammars: {mod_name}')
                # elif result == 0:
                #     inactiveGrammars.append(grammar_name)
                #     if mod_name in otherGrammars:
                #         otherGrammars.remove(mod_name)
                #     else:
                #         print(f'cannot remove from otherGrammars: {mod_name}')
            if not activeGrammars:
                msg = 'No Unimacro grammars are active'
            elif activeGrammars == [self.name]:
                msg = f'No grammars are active (apart from "{self.name}")'
            elif inactiveGrammars or switchedOffGrammars:
                msg = 'Active Unimacro grammars:\n' + ', '.join(activeGrammars)
            else:
                msg = 'All Unimacro grammars are active:\n' + ', '.join(activeGrammars)
        
            if inactiveGrammars:
                inactive = 'Inactive (but "Switched on") grammars:\n' + ', '.join(inactiveGrammars)
                msg += '\n\n' + inactive
                
            if switchedOffGrammars:
                switchedoff = '"Switched off" grammars:\n' + ', '.join(switchedOffGrammars)
                msg += '\n\n' + switchedoff
        
            # if otherGrammars:
            #     other = 'Other grammars (outside Unimacro):\n' + ', '.join(otherGrammars)
            #     msg = msg + '\n\n' + other
            if activeGrammars and activeGrammars != [self.name]:
                msg = msg + '\n\n' + "Show details of active Unimacro grammars?"
                if not actions.YesNo(msg, "Active grammars", icon="information", defaultToSecondButton=1):
                    return
            else:
                msg = msg + '\n\n' + 'Activate with\n\t"switch on <grammar name>" or \n\t"switch on all grammars".'
                actions.Message(msg, "No active Unimacro grammars", icon="information")
                return
        
        self.BrowseShow()
        

    def gotResults_edit(self,words,fullResults):
        # special case for actions:
        if self.hasCommon(words, 'actions'):
            actions.editActions(comingFrom=self, name="edit actions")
            return
        if self.hasCommon(words, 'spoken forms'):
            actions.Message('Warning: spoken forms lists do NOT refresh automatically.\n\nA restart of NatSpeak is required after you edited the "spokenforms.ini" file')
            spokenforms.editSpokenForms(comingFrom=self, name="edit spoken forms", language=self.language)
            return

        grammars = self.getUnimacroGrammars()
        gramNames = list(grammars.keys())
        gramName = self.hasCommon(words[-1:], gramNames)
        
        try:
            grammar = grammars[gramName]
        except KeyError:
            self.error(f'grammar {words[-1:]} not found in list of gramNames:\n{gramNames}')
            return
        # print(f'grammar: {gramName}: {grammar}')
        if self.hasCommon(words, 'grammar'):
            unimacro_grammars_paths = self.getUnimacroGrammarNamesPaths()
            # print(f'unimacro_grammars_paths:\n{unimacro_grammars_paths}\n')
            try:
                filepath = unimacro_grammars_paths[gramName]
            except KeyError:
                self.error(f'grammar not in unimacro_grammars_paths dict: {gramName}')
                return
            self.info(f'open for edit file: "{filepath}"')
            self.openFileDefault(filepath, mode="edit", name=f'edit grammar {gramName}')
        else:
            # edit the inifile
            try:
                grammar.switchOn()
                grammar.editInifile()
            except AttributeError:
                self.DisplayMessage(f'grammar "{gramName}" has no method "editInifile"')

    def switchOff(self, **kw):
        """overload, this grammar never switches off

        """        
        self.info('remains switched on: %s' % self)

    def switchOn(self, **kw):
        """overload, just switch on

        """
        self.activateAll()
        return 1


    def offInfo(self, grammar):
        """gives a nice message that the grammar is switched off

        Gives also information on how to switch on.

        """        
        name = grammar.getName()
        try:
            t = {'nld': ['Grammatica "%s" is uitgeschakeld'% name,
                         '', 
                         'Zeg: "schakel in [grammatica] %s" om te activeren'% name]}[self.language]
            # title = {'nld': 'Grammatica %s'% name}[self.language]
        except KeyError:
            t = ['Grammar "%s" is switched off'% name,
                 'Say: "switch on [grammar] %s" to activate'% name]
            # title = 'Grammar %s'% name
            t = ';  '.join(t)
            t = t.replace('; ', '\n')
            actions.Message(t)

    def UnimacroControlPostLoad(self):
        prevSet = set(self.Lists['gramnames'])
        newSet = set(self.getRegisteredGrammarNames())
        if prevSet != newSet:
            # print(f'UnimacroControlPostLoad, setting new grammar names list: {list(newSet)}')
            self.setList('gramnames', list(newSet))
            self.setList('logmodulename', list(newSet))
            
    def getUnimacroGrammarNamesPaths(self):
        """get the names of active or inactive, but loaded Unimacro grammars
        
        (wrong grammars are not "recorded" here, regrettably)
        
        """
        registered = self.getUnimacroGrammars()
        
        assert isinstance(registered, dict)
        # loaded_modules = copy.deepcopy(natlinkmain.loaded_modules)   # dict
        # bad_modules = copy.deepcopy(natlinkmain.bad_modules)   # set of paths

        unimacro_modules = {}
        natlink_modules = natlinkmain.get_loaded_modules()
        natlink_modules_files = [str(f) for f in natlink_modules.keys()]
        for name, gramobj in registered.items():
            # print(f'grammar name: {name}, gramobj: {gramobj}, module_name: {gramobj.module_name}')
            mod_name = gramobj.module_name
            for try_file in natlink_modules_files:
                if try_file.find(mod_name) > 0:
                    unimacro_modules[name] = try_file
                    break
            else:
                self.info(f'not found in natlink_modules_files: {name}')
                unimacro_modules[name] = name   # not found
            
        return unimacro_modules
    
# class MessageDictGrammar(natlinkutils.DictGramBase):
#     def __init__(self):
#         natlinkutils.DictGramBase.__init__(self)
# 
#     def initialize(self):
#         print('initializing/loading DictGrammar!!')
#         self.load()
#         natbj.RegisterMessageObject(self)
# 
#     def unload(self):
#         natbj.UnRegisterMessageObject(self)
#         natlinkutils.DictGramBase.unload(self)
#         
#     def gotResults(self, words):
#         pass
#         #print 'messageDictGrammar: heard dictation:  %s '% words


# standard stuff Joel (adapted for possible empty gramSpec, QH, unimacro)
# messageDictGrammar = MessageDictGrammar()
# messageDictGrammar.initialize()
# print('messageDictGrammar initialized')

def unload():
    #pylint:disable=W0603
    global utilGrammar  #, messageDictGrammar
    if utilGrammar:
        natlinkmain.delete_post_load_callback(utilGrammar.UnimacroControlPostLoad)
        utilGrammar.unload()
    utilGrammar = None
    # if messageDictGrammar:
    #     messageDictGrammar.unload()
    # messageDictGrammar = None
    
def changeCallback(type, args):
    #pylint:disable=W0603, W0622
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
            utilGrammar.CallAllGrammarObjects('setInterceptMode',[0])
        
        
def checkOriginalFileWithActualTxtPy(name, org_path, txt_path, py_path):
    """check if grammar has been copied, and changed, with copy of .txt as intermediate
    
    org_path: path to python file in UnimacroGrammars, the original grammars
    txt_path: initially copy of org_path, user area, ActiveGrammars, handled if new release has changes
    py_path:  actual state of active grammar, noted if changes are made
    
    """
    isfile = os.path.isfile
    if not isfile(txt_path):
        shutil.copyfile(org_path, txt_path)
    org_txt_equal = filecmp.cmp(org_path, txt_path)
    
    if not isfile(py_path):
        # print(f'not activated grammar "{name}"')
        return 
    txt_py_equal = filecmp.cmp(txt_path, py_path)
    if txt_py_equal:
        if org_txt_equal:
            # all equal
            return
        # new                 

# standard stuff Joel (adapted for python3, QH, unimacro):
if __name__ == "__main__":
    ## interactive use, for debugging:
    with natlink.natConnect():
        utilGrammar = UtilGrammar(inifile_stem='_control')
        utilGrammar.startInifile()
        utilGrammar.initialize()
        Words = ['edit', 'grammar', 'control']
        FR = {}
        utilGrammar.gotResults_edit(Words, FR)
elif __name__.find('.') == -1:
    # standard startup when Dragon starts:
    print(f'Unimacro {unimacro_version} in directory: {thisDir}')
    utilGrammar = UtilGrammar()
    utilGrammar.initialize()
    # set special function as a callback...
    natlinkmain.set_post_load_callback(utilGrammar.UnimacroControlPostLoad)
    # utilGrammar.checkUnimacroGrammars() 
