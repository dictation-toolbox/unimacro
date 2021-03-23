#
# Python Macro Language for Dragon NaturallySpeaking
#   (c) Copyright 1999 by Joel Gould
#   Portions (c) Copyright 1999 by Dragon Systems, Inc.
#
# natspeak_sample_docstring.py
# works only in DragonPad
#
# This is a sample macro file with a few more examples of docstring defined rules.
# start DragonPad and 
# try for example:
#  sample docstring
#  sample chair
#  sample this is a test
#
# say show natspeak sample docstring for the complete grammar in .txt format
# say show all grammars (or show grammar  sample docstring) for
#     presentation of the grammar(s) in an overview window.
# See http://qh.antenna.nl/unimacro (March 2010, Quintijn Hoogenboom)

from natlinkcore import natlink
import natlinkcore.natlinkutils as natut
import unimacro.natlinkutilsqh as natqh
import unimacro.natlinkutilsqh as natqh
import unimacro.natlinkutilsbj as natbj
from unimacro.actions import doKeystroke as keystroke
from unimacro.actions import doAction as action

class ThisGrammar(natbj.DocstringGrammar):
    """more elaborate example of grammar with  docstrings defined rules
    """
    def initialize(self):
        self.load(self.gramSpec)
        self.activateAll()
        self.prevHandle = 0
        
    def gotBegin(self, moduleInfo):
        winHandle = moduleInfo[2]
        if self.prevHandle == winHandle:
            return
        self.prevHandle = winHandle
        if natqh.matchModule('natspeak', wantedTitle='dragonpad',
                                modInfo=moduleInfo):
            print('activate grammar %s'% self.name)
            self.activateAll()
        elif self.isActive():
            print('deactivate grammar %s'% self.name)
            self.deactivateAll()

    def gotResultsInit(self, words, fullResults):
        keystroke('\n---\nAt start of macro go through gotResultsInit, all words: %s\n'% words)
        
    def rule_start1(self, words):
        """# this is a demo rule (exported):
         sample docstring
        """
        keystroke('Heard macro "start1" with words: %s\n'% words)

    def rule_start2(self, words):
        """ sample
               <specification>
        """
        keystroke('Heard macro "start1" with words: %s\n'% words)

    def subrule_specification(self, words):
        """ 
        # this is a subrule:
            table | chair
        """
        keystroke('    Heard subrule "specification" with words: %s\n'% words)
        
    def rule_start3(self, words):
        ' sample <dgndictation>'
        keystroke('Heard rule "start3" with words: %s\n'% words)

    def importedrule_dgndictation(self, words):
        '# imported rule, only comment (docstring may be deleted)'
        keystroke('    Heard imported rule "dgndictation" with words: %s\n'% words)
        
    def gotResults(self, words, fullResults):
        keystroke('At end of macro go through gotResults, '
                  'the fullResults were:\n%s\n---\n'% fullResults)
        
# standard stuff:
thisGrammar = ThisGrammar()
thisGrammar.initialize()

def unload():
    global thisGrammar
    if thisGrammar: thisGrammar.unload()
    thisGrammar = None
