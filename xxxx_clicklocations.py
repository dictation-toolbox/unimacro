#-------------------------------------------------------------------------------
# Name:        Click Locations
# Purpose:     Use voice to create commands that remember mouse locations.
#
#
# Author:      Douglas Parent, adapted to Unimacro conventions by Quintijn Hoogenboom (july 2012)
#
# Created:     12/20/2011
# Copyright:   (c) Douglas Parent 2011
# License:     You are free to use and modify this software for your own use.
#------------------------------------------------------------------------------
#

import natlink, nsformat
import wx
# import natlink and unimacro stuff:
natut = __import__('natlinkutils')
natqh = __import__('natlinkutilsqh')
natbj = __import__('natlinkutilsbj')
dialogs = __import__('unimacro_wxpythondialogs')
from actions import doAction as action
from actions import doKeystroke as keystroke

# subclass a Unimacro Grammar Class
ancestor = natbj.IniGrammar
class ThisGrammar(ancestor):
    language = natqh.getLanguage()      
    iniIgnoreGrammarLists = ['locations']  # for lists that are maintained in the class itself
    name = "mouse locations"
    gramSpec = """
        <dgndictation> imported;
        <setlocation> exported = set click location <dgndictation>;
        <clicklocation> exported  = <click> [on][location] {locations};
        <editlocation> exported  = edit click location {locations};
        <deletelocation> exported  = delete click location {locations};
        <click> = click | 'right click' | 'double click';

    """
    def initialize(self):
        self.load(self.gramSpec)
        self.resetAllVars()
        self.switchOnOrOff()  # should activate or deactivate according to inifile settings and
                              # user commands from _control.py
       
    def gotBegin(self, moduleInfo):
        self.currentModule = natqh.getBaseNameLower(moduleInfo[0])
        if self.checkForChanges:
            if self.checkInifile():
                self.resetAllVars()
        if self.prevModule == self.currentModule:
            return
        self.loadMouseClickCommands()
        self.prevModule = self.currentModule

    def resetAllVars(self):
        self.prevModule = None

    def loadMouseClickCommands(self):
        moduleName = self.currentModule
        self.locationsList = self.ini.get(moduleName)
        if self.locationsList:
            print 'list of mouse locations (%s): %s'% (moduleName, self.locationsList)
            self.setList('locations', self.locationsList)
        else:
            self.emptyList('locations')


    def gotResults_dgndictation(self, words, fullResults):
        dictated, dummy = nsformat.formatWords(words, state=-1)  # no capping, no spacing
        clickaction = natqh.getMousePositionActionString(absorrel=0, which=1, position=0)
        # this one kills Dragon/natspeak.exe
        #question = 'Set click location to "%s"'% clickaction
        #prompt = "set click location"
        #dictated = dialogs.InputBox(question, prompt, dictated)
        #if dictated is None:
        #    return
        self.ini.set(self.currentModule, dictated, clickaction)
        self.ini.write()
        self.loadMouseClickCommands()
        print 'set click command: %s to: %s'% (dictated, clickaction)

    def gotResults_clicklocation(self, words, fullResults):
        locationWord = words[-1]
        print 'clicklocation: %s'% locationWord
        clicklocation = self.ini.get(self.currentModule, locationWord, "")
        if not clicklocation:
            print 'oops, no clicklocation found for %s'% locationWord
            return
        action(clicklocation)

    def gotResults_setlocation(self, words, fullResults):
        # the work is done inside gotResults_dgndictation...
        pass

    def gotResults_deletelocation(self, words, fullResults):
        locationWord = words[-1]
        print 'deleting click location: %s for module: %s'% (locationWord, self.currentModule)
        self.ini.delete(self.currentModule, locationWord)
        self.ini.write()
        self.loadMouseClickCommands()

    def gotResults_editlocation(self, words, fullResults):
        locationWord = words[-1]
        clickaction = natqh.getMousePositionActionString(absorrel=0, which=1, position=0)
        self.ini.set(self.currentModule, locationWord, clickaction)
        self.ini.write()
        self.loadMouseClickCommands()
        print 'changed click location: %s for module: %s to: %s'% (locationWord, self.currentModule, clickaction)


thisGrammar = ThisGrammar()
thisGrammar.initialize()

def unload():
    global thisGrammar
   
    if thisGrammar:
        thisGrammar.unload()
        thisGrammar = None
        