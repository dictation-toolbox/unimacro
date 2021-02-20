#
# Python Macro Language for Dragon NaturallySpeaking
#   (c) Copyright 1999 by Joel Gould
#   Portions (c) Copyright 1999 by Dragon Systems, Inc.
#
# This grammar is meant as a minimum example
# for a variable number of words grammar
# Quintijn, June 28, 2009

import natlinkcore.natlink as natlink
import natlinkcore.natlinkutils as natut


ancestor = natut.GrammarBase
class ThisGrammar(ancestor):

    gramSpec = """
<pasthistory> exported = past history {phwords}+;
    """

    def initialize(self):
        self.load(self.gramSpec)
        self.prevInfo = None
        self.phwords = ['asthma',
                        'hypertension',
                        'thyroid',
                        'cancer',
                        'respiratory']
        self.setList('phwords', self.phwords)

    def gotBegin(self,moduleInfo):
        if self.prevInfo == moduleInfo:
            return

        self.prevInfo = moduleInfo

        winHandle = natut.matchWindow(moduleInfo,'winword','Microsoft Word')
        if winHandle:
            if not self.isActive():
                self.activateAll()
        elif self.isActive():
            self.deactivateAll()

    def gotResults_pasthistory(self, words, fullResults):
        """possibility to "manually" update the styles list"""
        L = ['']
        for w in words:
##            print 'got phword: %s'% w   # including the trigger words!
            L.append(w)
        natut.playString(' '.join(L))
            
# standard stuff:
thisGrammar = ThisGrammar()
thisGrammar.initialize()

def unload():
    global thisGrammar
    if thisGrammar:
        thisGrammar.unload()
        
    thisGrammar = None
