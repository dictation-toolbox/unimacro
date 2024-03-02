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
#pylint:disable=E1101

import os
import filecmp
import shutil
import string
from pathlib import Path
import natlink
from natlinkcore import loader
from natlinkcore import natlinkstatus

from dtactions.unimacro import unimacroutils
from dtactions.unimacro import unimacroactions as actions

from unimacro import natlinkutilsbj as natbj
from unimacro import spokenforms 
import importlib.metadata as meta
import sys

#from unimacro.logger import ulogger
status = natlinkstatus.NatlinkStatus()
natlinkmain = loader.NatlinkMain()

#a global logger for unimacro.  perfectly reasonable to access by name instead.
import logging as l

#for some reason, importing amodule which does this doesn't work.  Likely because natlinkmain must be started first for
#this sublogger natlink.unimacro to work correctly.
import unimacro as unimacro_l   #bring in so we can add a variable ulogger to the namespace.  
ulogger : l.Logger = l.getLogger("natlink.unimacro") 

unimacro_l.__dict__['ulogger']=ulogger
ulogger.debug("natlink.unimacro logger available")

#Loggers can be created for any module, and they can propogate to the parent  Logger, or not.
#As an example, this module for the control grammar has its own child logger of unimacro.
#Note an entry point has to be defined as well, in pyproject.toml, so Loggers for various natlink components can be discovered.




control_logger=l.getLogger(unimacro_l.control_logger_name())






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

def natlink_loggers() ->dict:
    """ 
        returns dictionary, keys are the names of the module to show to users (or for them to use in dication), 
        values are the string names of the loggers.
        For example, {'unimacro':'natlink.unimacro'}.
        Any python module/package/etc. can enable their own logger by defining an entry point in group 'natlink.loggers'.  
        The entry point must be a function that returns a logger name.  Is the Python 'logging' module.

    """


    discovered_eps=meta.entry_points(group='dt.loggers')
    ulogger.debug(f"Entry Points for natlink.loggers:  {discovered_eps}")
    loggers=dict()
    for ep in discovered_eps:
        try:
            (name,_)=ep
            module=ep.module
            module_loaded=module in sys.modules

            ulogger.debug(f"Entry Point {ep} module: {module}  is loaded:  {module_loaded}.  {'' if module_loaded else 'Not adding to list of available loggers.'} ")

            #only add the logger to the list of available loggers if the module is already loaded.
            if module_loaded:              
                f=ep.load()
                logname=f()
                loggers[name]=logname
        except Exception as e:
            ulogger.error(f"Attempting to load EntryPoint {ep},error\n {e}")
    return loggers

ancestor = natbj.IniGrammar
class UtilGrammar(ancestor):
    language = status.get_language()
    
    loggers=natlink_loggers()
    ulogger.debug(f"Control:  Available Loggers  {loggers}")
    loggers_names=sorted(loggers.keys())
    iniIgnoreGrammarLists = ['gramnames', 'tracecount', 'message'] # are set in this module

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
    gramDict['setlogging'] = """<setlogging> exported = {logmodulename}  loglevel <loglevel>;"""
    gramDict['loglevel'] = "<loglevel> = (debug|info|warning|error|critical);"


    gramSpec = []
    assert set(gramRules) == set(gramDict.keys())

    if language == 'nld':
        gramDict['checkalphabet'] = """<checkalphabet> exported = controleer alfabet;"""

    for rulename in gramRules:
        gramSpec.append(gramDict[rulename])
    
    
    ## extra: the trace rule:
    ## TODO QH, switchoff for the moment, febr24
    if specials:
        specials2 = specials[1:]  # remove initial "|" (at show it is  "| actions | 'spoken forms'", here it is
                                  #     "actions | 'spoken forms'" only, because gramnames etc are not implemented
                                  #     for tracing)
        traceSpecial = """<trace> exported = trace (("""+ specials2 +""") |
                              ((on|off| {tracecount})("""+ specials2 +""")) |
                              (("""+ specials2 +""") (on|off|{tracecount}))) ;"""
        # gramSpec.append(traceSpecial) # add trace for actions of spoken forms (latter not implemented)
    ulogger.info('check, correct _control?????')

    Mode = Normal
    LastMode = Normal
    CurrentWord = 0
    Repeat = 0

    def initialize(self):
        # temp set allResults to 0, disabling the messages trick:
        if not self.load(self.gramSpec, allResults=showAll):
            return
        self.setList('logmodulename',self.loggers_names)
        self.RegisterControlObject(self)
        self.emptyList('message')
        # at post load
        # allGramNames = self.getUnimacroGrammarNames()
        # self.setList('gramnames', allGramNames)
        ## TODO QH switch on again if tracing is activated again
        # self.setNumbersList('tracecount', tracecount)
        
        self.activateAll()
        self.setMode(Normal)
        self.startExclusive = self.exclusive # exclusive state at start of recognition!
##        if unimacroutils.getUser() == 'martijn':
##            print 'martijn, set exclusive %s'% self.name
##            self.setExclusive(1)
        control_logger.info('---now starting other Unimacro grammars:')


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
                control_logger.info('fill in in "%s_spokenform.ini", [alphabet] spoken for: "%s"'% (self.language, letter))
                continue
            if version < 11:
                normalform = '%s\\%s'% (letter.upper(), spoken)
            else:
                normalform = '%s\\letter\\%s'% (letter.upper(), spoken)
            try:
                natlink.recognitionMimic([normalform])
            except natlink.MimicFailed:
                control_logger.info('invalid spoken form "%s" for "%s"'% (spoken, letter))
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
                    control_logger.info('%s fails also: "%s" for "%s"'% (trying, spoken, letter))
                else:
                    control_logger.info('alphabet section is corrected with: "%s = %s"'% (letter, spoken))
                    ini.set(alph, letter, spoken)
        ini.writeIfChanged()
           

    def gotResults_trace(self,words,fullResults):
        control_logger.info('control, trace: %s'% words)
        traceNumList = self.getNumbersFromSpoken(words) # returns a string or None
        if traceNumList:
            traceNum = int(traceNumList[0])
        else:
            traceNum = None

        if self.hasCommon(words, 'actions'):
            if self.hasCommon(words, 'show'):
                actions.debugActionsShow()
            elif self.hasCommon(words, 'off'):
                actions.debugActions(0)
            elif self.hasCommon(words, 'on'):
                actions.debugActions(1)
            elif traceNum:
                actions.debugActions(traceNum)
            else:
                actions.debugActions(1)
        elif self.hasCommon(words, 'spoken forms'):
            control_logger.info("no tracing possible for spoken forms")

    #def gotResults_voicecode(self,words,fullResults):
    #    """switch on if requirements are fulfilled
    #
    #    voicecodeHome must exist
    #    emacs must be in foreground
    #    """
    #    wxmed = os.path.join(voicecodeHome, 'mediator', 'wxmediator.py')
    #    if os.path.isfile(wxmed):
    #        commandLine = r"%spython.exe %s > D:\foo1.txt >> D:\foo2.txt"% (sys.prefix, wxmed)
    #        os.system(commandLine)
    #    else:
    #        print 'not a file: %s'% wxmed
            
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
                control_logger.info('_control switch, no valid grammar found, command: %s'% words)

    def switch(self, gram, gname, switchOn):
        """switch on or off grammar, and set in inifile,
        gram is the grammar object
        gname is the grammar name
        switchOn is True or False
        """
        if gram == self:
            control_logger.error(f'should not be here, do not switch on of off _control {gram}')
            return None
        if switchOn:
            if gram.ini:
                gram.checkInifile()
                gram.ini.set('general', 'initial on', 1)
                gram.ini.write()
                unimacroutils.Wait(0.1)
            else:
                control_logger.error(f'--- ini file of grammar {gname} is invalid, please try "edit {gname}"...')
            gramName = gram.getName()
            unimacro_grammars_paths = self.getUnimacroGrammarNamesPaths()
            try:
                filepath = Path(unimacro_grammars_paths[gramName])
            except KeyError:
                control_logger.error(f'_control, grammar not in unimacro_grammars_paths dict: {gramName}, cannot switchOn')
                return None
            # now reload with force option.
            control_logger.info(f'_control, now reload grammar "{gramName}":')
            natlinkmain.seen.clear()
            natlinkmain.load_or_reload_module(filepath, force_load=True)

            return 1

        # switch off:        
        gram.ini.set('general', 'initial on', 0)
        gram.ini.writeIfChanged()
        gram.cancelMode()  
        gram.deactivateAll()
        # gram.unload()
        control_logger.info('grammar "%s" switched off'% gram.getName())
        return 1

    def gotResults_setlogging(self,words, fullresults):
        """
        """
        control_logger.debug(f"unimacro logger gotResults_logging_level words: {words} fullResults: {fullresults}")

        loglevel_for = words[0]   # something like natlink, unimacro,... 
        new_level_str_mc,_=fullresults[-1]
        new_log_level_str=new_level_str_mc.upper()
        #the string should be in the 
        logger_name=self.loggers[loglevel_for]
        new_log_level=l.__dict__[new_log_level_str]

        control_logger.debug(f"New Log Level {new_log_level_str} for logger {logger_name}")
        logger=l.getLogger(logger_name)
        logger.setLevel(new_log_level)

        
    

#Hide numbers    def gotResults_loglevel(self,words,fullresults):
        """
        """
        control_logger.debug(f"gotResults_logging_level words: {words} fullResults: {fullresults}")
        return
        
    
    def gotResults_showexclusive(self,words,fullResults):

        All = 0
        name = 'exclusive grammars'
        if len(name)>0:                
            Start=(' '.join(name),[])
        else:
            Start=()
        # fix state at this moment (in case of Active grammars popup)
        control_logger.info(f'_control, showexclusive, exclusiveGrammars: {natbj.exclusiveGrammars}')
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
        control_logger.info('reset exclusive')
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
            control_logger.info(f'exclusive grammars (+ control) are: {exclNames}')
            self.gotResults_showexclusive(words, fullResults)
            return
        if self.hasCommon(words,"loggers"):
            control_logger.info(f"Available Loggers: {self.loggers}")
            return


        grammars = self.getUnimacroGrammars()
        gramNames = list(grammars.keys())
        control_logger.debug(f'_control, gramNames: {gramNames}')
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
            control_logger.info(f'activeGrammars: {activeGrammars}')
            control_logger.info(f'inactiveGrammars: {inactiveGrammars}')
            control_logger.info(f'switchedOffGrammars: {switchedOffGrammars}')
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
            control_logger.error(f'grammar {words[-1:]} not found in list of gramNames:\n{gramNames}')
            return
        # print(f'grammar: {gramName}: {grammar}')
        if self.hasCommon(words, 'grammar'):
            unimacro_grammars_paths = self.getUnimacroGrammarNamesPaths()
            # print(f'unimacro_grammars_paths:\n{unimacro_grammars_paths}\n')
            try:
                filepath = unimacro_grammars_paths[gramName]
            except KeyError:
                control_logger.error(f'grammar not in unimacro_grammars_paths dict: {gramName}')
                return
            control_logger.info(f'open for edit file: "{filepath}"')
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
        control_logger.info('remains switched on: %s' % self)

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
                control_logger.info(f'not found in natlink_modules_files: {name}')
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
    natlink.natConnect()
    try:
        utilGrammar = UtilGrammar(inifile_stem='_control')
        utilGrammar.startInifile()
        utilGrammar.initialize()
        Words = ['edit', 'grammar', 'control']
        FR = {}
        utilGrammar.gotResults_edit(Words, FR)
    finally:
        natlink.natDisconnect()
elif __name__.find('.') == -1:
    # standard startup when Dragon starts:
    utilGrammar = UtilGrammar()
    utilGrammar.initialize()
    # set special function as a callback...
    natlinkmain.set_post_load_callback(utilGrammar.UnimacroControlPostLoad)
    # utilGrammar.checkUnimacroGrammars() 
