#
# Python Macro Language for Dragon NaturallySpeaking
#   (c) Copyright 1999 by Joel Gould
#   Portions (c) Copyright 1999 by Dragon Systems, Inc.
#
# This grammar is integrated into unimacro, offering eg show capabilities
# adapted for word styles by Quintijn Hoogenboom (23/10/2008), for comparison with
# Dragonfly example...
# Also see: http://qh.antenna.nl/unimacro/features/grammarclasses/docstringgrammar/examplewordstyles.html
# implemented as DocstringGrammar example (april 2010)
#

import natlink
natqh = __import__('natlinkutilsqh')
natut = __import__('natlinkutils')
natbj = __import__('natlinkutilsbj')

import win32api
import win32com.client
consts = win32com.client.constants

ancestor = natbj.DocstringGrammar
class ThisGrammar(natbj.DocstringGrammar):

    # list is filled in updateStyles, not by the IniGrammar functions:
    iniIgnoreGrammarLists = ['style']

    name = 'word styles'

    # rules in the docstrings of the rules functions below...
    #gramSpec = """
    #    <showStyles> exported = show styles;
    #    <updateStyles> exported = update styles;
    #    <setStyle> exported = set style {style};
    #"""

    def initialize(self):
        print('init winword_styles_unimacro')
        self.load(self.gramSpec)
        self.application = None
        self.activated = None
        self.styles = []
        self.prevInfo = None

    def gotBegin(self,moduleInfo):
        if self.prevInfo == moduleInfo:
            return

        self.prevInfo = moduleInfo

        winHandle = natut.matchWindow(moduleInfo,'winword','Microsoft Word')
        if winHandle:
            if self.checkForChanges:
                print('word styles (%s), checking the inifile'% self.name)
                self.checkInifile()

            if not self.application:
                self.application=win32com.client.Dispatch('Word.Application')
            if self.activated:
                if winHandle != self.activated:
                    print('DEactivate for previous %s'% self.activated)
                    self.deactivateAll()
                    self.activated = None
            if not self.activated:
                print('activate for %s'% winHandle)
                self.activateAll(window=winHandle)
                self.activated = winHandle
        else:
            winHandle = natut.matchWindow(moduleInfo,'winword','')
            if not winHandle:
                print('other application, release word')
                if self.application:
                    self.application = None
            # outside an interesting window so:
            return
        
        # new modInfo, possibly a new document in front:
        print('update styles')
        self.updateStyles()

    def updateStyles(self):
        """update the styles list, either from gotBegin or from a spoken command"""
        if self.application:
            document = self.application.ActiveDocument
            style_map = [(str(s), s) for s in  document.Styles]
            self.styles = dict(style_map)
            self.setList('style', list(self.styles.keys()))
        else:
            print('no word application loaded... %s'% self.application)

    def rule_updateStyles(self, words):
        "update styles"
        # possibility to "manually" update the styles list
        # not needed in normal use
        self.updateStyles()

    def rule_showStyles(self, words):
        "show styles"
        # print a list of all valid styles in the messages window
        if self.styles:
            print('styles in use: %s'% list(self.styles.keys()))
        else:
            print('no styles in use...')

    def rule_setStyle(self, words):
        "set style {style}"
        #apply a style to the cursor or selection
        style = words[-1]
        if style in self.styles:
            print('setting style %s'% style)
            sel = self.application.Selection
            sel.Style = style
        else:
            print('style not in stylelist: %s'% style)
            
# standard stuff:
thisGrammar = ThisGrammar()
thisGrammar.initialize()

def unload():
    global thisGrammar
    if thisGrammar:
        if thisGrammar.application:
            thisGrammar.application = None
        thisGrammar.unload()
        
    thisGrammar = None
