# Python Macro Language for Dragon NaturallySpeaking
#   (c) Copyright 1999 by Joel Gould
#   Portions (c) Copyright 1999 by Dragon Systems, Inc.
#
# This is an adaptation of the _sample1.py of Joel Goulds original release
# to be found in natlink/SampleMacros
#
# _first_sample_docstring.py
#
# This is a sample macro file with a single command  
# When some window/control which can "receive" text (keystrokes) is in focus,
# say "first sample docstring".
# It should recognize the command and type:
#   Heard  macro "start" (words: "first sample docstring"){enter}
#
# This file represents the simplest possible example of a NatLink macro,
# with definition in docstring format.
# See http://qh.antenna.nl/unimacro/features/grammarclasses/docstringgrammar/index.html
# (March 2010, Quintijn Hoogenboom)
#
import natlinkcore.natlink as natlink
import natlinkcore.natlinkutils as natut
import unimacro.natlinkutilsqh as natqh
import unimacro.natlinkutilsbj as natbj
from actions import doKeystroke as keystroke
from actions import doAction as action

class ThisGrammar(natbj.DocstringGrammar):
    """simple example of a NatLink grammar with the rule definition in docstring
    """
    def initialize(self):
        self.load(self.gramSpec)
        self.activateAll()
        
    def rule_start(self, words):
        "first sample docstring"
        keystroke('Heard macro "start" (words "first sample docstring"){enter}')

thisGrammar = ThisGrammar()
thisGrammar.initialize()

def unload():
    global thisGrammar
    if thisGrammar: thisGrammar.unload()
    thisGrammar = None
