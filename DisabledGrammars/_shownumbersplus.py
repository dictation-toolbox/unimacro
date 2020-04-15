__version__ = "$Rev: 398 $ on $Date: 2011-03-07 14:50:15 +0100 (ma, 07 mrt 2011) $ by $Author: quintijn $"
# This file is part of a SourceForge project called "unimacro" see
# http://unimacro.SourceForge.net and http://qh.antenna.nl/unimacro
# (c) copyright 2003 see http://qh.antenna.nl/unimacro/aboutunimacro.html
#    or the file COPYRIGHT.txt in the natlink\natlink directory 
#
#  _shownumbersplus.py
#
# operate on shownumbersplus, from Max Roth
# written by Quintijn Hoogenboom (QH softwaretraining & advies),
# february 2011
#
"""Do commands on the numbers shown by shownumbersplus
"""
#
#
import natlink
import win32event, pywintypes, win32api

import monitorfunctions # for get_taskbar_position
import time, os, os.path, sys
from actions import doAction as action
natut = __import__('natlinkutils')
natqh = __import__('natlinkutilsqh')
natbj = __import__('natlinkutilsbj')

language = natqh.getLanguage()        
# center mouse after taskswitch (not good with XP and choice boxes in taskbar)
#
ancestor=natbj.DocstringGrammar
class ThisGrammar(ancestor):
    
    language = natqh.getLanguage()        
    name = "show numbers plus"
    prevHndle = None

    if language == 'nld':
        gramSpec = natbj.numberGrammarTill999['nld']
    else:
        gramSpec = natbj.numberGrammarTill999['enx'] # with possible translations for other languages
    
    def initialize(self):
        self.load(self.gramSpec)
        self.prevHndle = None
        self.SNPActive = None
        self.switchOnOrOff() # initialises lists from inifile, and switches on
                         # if all goes well (and variable onOrOff == 1)
        self.mode = None
        self.prevTopHndle = None
        
        
    def switchOn(self, **kw):
        """SNP overload, switches grammar on, activates all reenles
        
        check first if SNP is active, if not, leave the off state
        """
        if self.SNPIsRunning(onlyShow=1):
            self.SNPActive = 1 # just for trying
            ancestor.switchOn(self, **kw)
            self.openMicMode() # giving the tray numbers
            #print '%s switched on'% self.name
        else:
            self.SNPActive = 0
            print 'Show Numbers Plus! is not running, grammar "%s" not activated'% self.name

    def switchOff(self, skipCancelMode=None):
        """SNP overload, switches grammar off, deactivates all rules

        """
        if self.SNPActive and not skipCancelMode:
            self.cancelMode()
        ancestor.switchOff(self)
        
    def cancelMode(self):
        """switch off numbers and continuous mode
        """
        if self.SNPActive and self.SNPIsRunning() and self.prevHndle:
            if self.debug:
                print 'SNP cancelMode'
            self.command('HIDENUMBERS')
            self.command('HIDENUMBERSTASKBAR')
        self.mode = ''

    def openMicMode(self):
        """switch off numbers and continuous mode
        """
        if self.SNPActive and self.prevHndle:
            self.command('SHOWNUMBERSTASKBAR')
        self.mode = ''
        
    def gotBegin(self, moduleInfo):
        if self.checkForChanges:
            self.checkInifile() # refills grammar lists and instance variables
        if self.prevHndle == moduleInfo[2]:
            return
        
        # if module changes, reset mode:
        prog, title, toporchild, hndle = natqh.getProgInfo(moduleInfo)
        if toporchild == 'child':
            self.prevTopHndle = self.prevHndle
        elif self.prevTopHndle != moduleInfo[2]:
            # keep mode when switching from child to top again:
            self.mode = ''
        self.prevHndle = moduleInfo[2]

    def gotResultsInit(self, words, fullResults):
        self.taskbar = self.inwindow = 0
        self.waitForNumber('inwindow')
        self.clicktype = 1
        self.action = ''
      
    def fillInstanceVariables(self):
        """fill eg taskbar posision
        """
        self.centerMouse = self.ini.get('general', 'center mouse after action', '')
        self.debug = self.ini.get('general', 'debug', '')
        self.taskbarPosition = self.ini.get('general', 'taskbar position', 'bottom')
        if self.debug:
            print 'shownumbersplus grammar, taskbar position: %s'% self.taskbarPosition

    def rule_showhidenumbers(self, words):
        """#commands for switching on or off the numbers
        (show|hide) numbers [continuous];
        """
        show = self.hasCommon(words, 'show')
        hide = self.hasCommon(words, 'hide')
        continuous = self.hasCommon(words, 'continuous')
        if self.debug:
            print 'continuous: %s'% continuous
        if show and hide:
            raise ValueError('shownumbersplus, got both show and hide: %s'% words)
        elif not (show or hide):
            raise ValueError('shownumbersplus, got neither show nor hide: %s'% words)
        if show:
            cmd = 'SHOWNUMBERS'
            if continuous:
                self.mode = 'continue'
        else:
            cmd = 'HIDENUMBERS'
            self.mode = ''
        self.command(cmd)

    def rule_showhidetraynumbers(self, words):
        """(show|hide) (tray) [numbers];
        """
        show = self.hasCommon(words, 'show')
        hide = self.hasCommon(words, 'hide')
        
        if show and hide:
            raise ValueError('shownumbersplus, got both show and hide: %s'% words)
        elif not (show or hide):
            raise ValueError('shownumbersplus, got neither show nor hide: %s'% words)
        if show:
            cmd = 'SHOWNUMBERSTASKBAR'
        else:
            cmd = 'HIDENUMBERSTASKBAR'
        self.command(cmd)

    def rule_taskbar(self, words):
        """(tray) {n1-40} [<click>|<action>|<inwindow>]
        """
        self.taskbar = self.getNumbersFromSpoken(words)[0]
        self.clicktype = 1
        # actions in self.gotResults, with self.taskbar set

    def rule_inwindow(self, words):
        """<click> <integer> [continue|stop|{afterclickactions}]
        """
        if self.hasCommon(words[-1], 'continue'):
            self.mode = 'continue'
        elif self.hasCommon(words[-1], 'stop'):
            self.mode = None
        pass # never comes here, ends in gotResults with a number in self.inwindow
        
    
    def subrule_click(self, words):
        '{clicks}'
        self.clicktype = self.getFromInifile(words, 'clicks')

    def subrule_action(self, words):
        '{actions}'
        self.action = self.getFromInifile(words, 'actions')

    def gotResults(self, words, fullResults):
        """perform the resulting actions
        """
        self.collectNumber()
        if self.debug:
            print 'collected: %s'% self.inwindow
        #
        if self.taskbar:
            #asked for a taskbar number...
            cmd = 'DOACTIONTRAY=(%s, %s)'% (self.taskbar, self.clicktype)
            self.command(cmd)
            # see if stacked tray shows up
            className = natqh.getClassName()
            #print 'className: %s'% className
            if className == "TaskListThumbnailWnd":
                if self.debug:
                    print 'stacked taskbar, display numbers again'
                cmd = 'SHOWNUMBERS'
                self.command(cmd)
                natqh.visibleWait()
            self.mode = None

        if self.inwindow:
            # intercept when you are in the stacked explorer (taskbar) windows:
            className = natqh.getClassName()
            #print 'classname: %s'% className
            if className == "TaskListThumbnailWnd":
                self.doAlternativeClick(className, self.inwindow)
            else:
                cmd = 'DOACTIONSHOWNUMBERS=(%s, %s)'% (self.inwindow, self.clicktype)
                if self.debug:
                    print 'inwindow cmd: %s'% cmd
                self.command(cmd)
        if self.action:
            action("VW") # visible wait
            if self.debug:
                print 'shownumbers plus action: %s'% self.action
            action(self.action)

        if self.centerMouse:
            if self.debug:
                print 'center mouse'
            natqh.Wait()
            natqh.doMouse(1, 5, 0.3, 0.3, 0, 0)  # relative in client area, no clicking           
        # must check this:
        if self.mode == 'continue':
            hndle = natlink.getCurrentModule()[2]
            if hndle != self.prevHndle:
                self.mode = '' # new window
                return
            if self.debug:
                print 'continuous, show numbers again'
            action("VW")
            cmd = 'SHOWNUMBERS'
            self.command(cmd)

            
    def command(self, cmd):
        """do a shownumbersplus command
        
        """
        if not self.SNPActive:
            if self.debug:
                print 'SNP not running, call "switch on %s" to restar grammar, after you started SNP! again'% self.name
            return
        
        if self.inGotBegin or self.status == 'new':
            print 'SNP command not executed (initializing or gotbegin): %s'% cmd
            return
        
        
        hndle = self.SNPIsRunning()
        if hndle:
            script = 'DdeExecute "ShowNumbersPlus", "CONTROL", "[%s]"'% cmd
            if self.debug:
                print 'SNP: %s'% cmd
            try:
                natlink.execScript(script)
            except:
                '''Ddeexecute failed for shownumbersplus command: "%s".
    This is strange, because apparently Show Numbers Plus! is running.
    Error message: %s, %s'''% (cmd, sys.exc_info()[0], sys.exc_info()[1])
                self.switchOff(skipCancelMode=1)
                self.SNPActive = 0
            else:
                self.closeMutex()
        else:
            print '''No DdeExecute to shownumbersplus: "%s".
Because SNP seems to be not running.'''% cmd
            self.switchOff()

            
            
    def doAlternativeClick(self, className, num):
        """instead of click perform another (keystrokes) action
        """

        if className == "TaskListThumbnailWnd":
            taskbarPosition = monitorfunctions.get_taskbar_position() # notices changes on the fly!
            # which way to scroll through a stack of taskbar buttons:
            initialKeys = dict(left='{down}', top='{right}',
                               right='{left}{down}', bottom='{right}')
            scrollKeys = dict(left='down', top='right',
                               right='down', bottom='right')
            try:
                initial = initialKeys[taskbarPosition]
                scrollKey = scrollKeys[taskbarPosition]
            except KeyError:
                print 'key not found "taskbarPosition": %s'% taskbarPosition
                return
            # go to first of popup windows (depending on taskbar location)
            action(initial)
            if num and num != '0':
                action('{%s %s}'% (scrollKey, num))
            action('{enter}')
        else:
            print 'should not call doAlternativeClick for className: %s'% className
      
    def SNPIsRunning(self, onlyShow=None):
        MutexName = "ShowNumbersPlusGMUTEX"
        MUTEX_ALL_ACCESS = 0X1F0001
        try:
            SingleAppHandle = win32event.OpenMutex(MUTEX_ALL_ACCESS, 0, MutexName)
        except pywintypes.error, details:
            if details[0] == 2:
                self.MutexHndle = None
                return
        self.MutexHndle = SingleAppHandle
        if onlyShow:
            self.closeMutex()
        return SingleAppHandle
    
    def closeMutex(self):
        if self.MutexHndle:
            win32event.ReleaseMutex(self.MutexHndle)
            self.MutexHndle = None
            
    
            
# standard stuff Joel (adapted for possible empty gramSpec, QH, unimacro)
thisGrammar = ThisGrammar()
if thisGrammar.gramSpec:
    thisGrammar.initialize()
    thisGrammar.status = 'ready'
else:
    thisGrammar = None

def unload():
    global thisGrammar
    if thisGrammar:
        thisGrammar.cancelMode()
        thisGrammar.unload()
    thisGrammar = None

def changeCallback(type,args):
    """calls back here, switches off numbers when microphone sleep or off
    """
    if not thisGrammar:
        return
    if ((type == 'mic') and (args=='on')):
        thisGrammar.openMicMode()
    else:
        thisGrammar.cancelMode()
