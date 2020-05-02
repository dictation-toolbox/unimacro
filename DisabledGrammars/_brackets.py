__version__ = "$Rev: 571 $ on $Date: 2017-02-13 14:17:09 +0100 (ma, 13 feb 2017) $ by $Author: quintijn $"
# This file is part of a SourceForge project called "unimacro" see
# http://unimacro.SourceForge.net and http://qh.antenna.nl/unimacro
# (c) copyright 2003 see http://qh.antenna.nl/unimacro/aboutunimacro.html
#    or the file COPYRIGHT.txt in the natlink\natlink directory
#
#  _brackets.py
# written by: Quintijn Hoogenboom (QH softwaretraining & advies)
# august 2003, revision october 2011
""" unimacro grammar that puts brackets, braces etc.

import rule
import "dgndictation"
import used.
import Unfortunately
import the
import other
import "imported
import rules"
(dgnletters and dgnwords) do not
work any more in Dragon 11

Notes:
1. If you start or end with space-bar (or other white space),
   this will be put OUTSIDE the brackets.

2. No capitalisation is done unless you call as directive.

3. Dictation errors cannot be corrected with the spell window. Select,
dictate again and
   correct then if needed.

"""
import natlink
import nsformat
natqh = __import__('natlinkutilsqh')
natbj = __import__('natlinkutilsbj')
natut = __import__('natlinkutils')
from actions import doAction as action
from actions import doKeystroke as keystroke

language = natqh.getLanguage()

ancestor = natbj.DocstringGrammar
class BracketsGrammar(ancestor):
    language = natqh.getLanguage()
    name = "brackets"

    def initialize(self):
        if not self.language:
            print("no valid language in grammar "+__name__+" grammar not initialized")
            return
        self.load(self.gramSpec)
        self.switchOnOrOff()

    def gotBegin(self,moduleInfo):
        if self.checkForChanges:
            self.checkInifile()
        if self.mayBeSwitchedOn == 'exclusive':
            self.switchOnOrOff()

    def gotResultsInit(self, words, fullResults):
        self.dictated = ''  # analysis of dgndictation or dgnletters
        self.pleft = self.pright = '' # the left and right parts of the brackets

        if self.mayBeSwitchedOn == 'exclusive':
            print('recog brackets, switch off mic: %s'% words)
            natbj.SetMic('off')

    def importedrule_dgndictation(self, words):
        #do with nsformat functions:
        self.dictated, dummy = nsformat.formatWords(words, state=-1)  # no capping, no spacing
        #print '-result of nsformat: |%s|'% repr(self.dictated)

    def rule_brackets(self, words):
        "<before> {brackets}+ [<dgndictation>]"
        for w in words:

            p = self.getFromInifile(w, 'brackets')
            if not p:
                print('no valid brackets found for word: "%s"'% w)
                continue
            #print 'brackets, found: %s, %s'% (w, p)
            if len(p) > 2 and p.find("|") > 0:
                pList = p.split("|")
                newpleft = pList[0]
                newpright = pList[1]
            else:
                lenph = len(p)/2
                newpleft, newpright = p[:lenph], p[lenph:]
            # make more brackets together, from outer to inner:
            self.pleft = self.pleft + newpleft
            self.pright = newpright + self.pright
        #print 'pleft: "%s", pright: "%s"'% (repr(self.pleft), repr(self.pright))

    def subrule_before(self, words):
        "(here|between|empty)+"
        self.here, self.between = False, False
        for w in words:
            if self.hasCommon(w, 'between'):   # this is the trigger word, ignore
                self.between = True
            if self.hasCommon(w, 'here'):   # this is the trigger word, ignore
                self.here = True
            if self.hasCommon(w, 'empty'):   # this is the trigger word, ignore
                self.between = False


    def gotResults(self, words, fullResults):

        #  see if something selected, leaving the clipboard intact
        #  keystroke('{ctrl+x}')  # try to cut the selection
        if self.between:
            natqh.saveClipboard()
            action('<<cut>>')
            contents = natlink.getClipboard().replace('\r','')
            natqh.restoreClipboard()
        else:
            contents = ""

        if self.here:
            natqh.buttonClick('left', 1)
            natqh.visibleWait()

        leftText = rightText = leftTextDict = rightTextDict = ""
        if contents:
            # strip from clipboard contents:
            contents, leftText, rightText = self.stripFromBothSides(contents)

        if self.dictated.strip():
            contents, leftTextDict, rightTextDict = self.stripFromBothSides(self.dictated)
        elif self.dictated:
            # the case of only a space-bar:
            leftTextDict = self.dictated


        lSpacing = leftText + leftTextDict
        rSpacing = rightTextDict + rightText

        if lSpacing:
            keystroke(lSpacing)

        action(self.pleft)
        natqh.visibleWait()
        if contents:
            #print 'contents: |%s|'% repr(contents)
            keystroke(contents)
        natqh.visibleWait()
        action(self.pright)
        natqh.visibleWait()

        if rSpacing:
            keystroke(rSpacing)

        if not contents:
            # go back so you stand inside the brackets:
            nLeft = len(self.pright) + len(rSpacing)
            keystroke('{ExtLeft %s}'% nLeft)


    def stripFromBothSides(self, text):
        """strip whitespace from left side and from right side and return
the three parts

        input: text
        output: stripped, leftSpacing, rightSpacing
        """
        leftText = rightText = ""
        lSpaces = len(text) - len(text.lstrip())
        leftText = rightText = ""
        if lSpaces:
            leftText = text[:lSpaces]
        text = text.lstrip()
        rSpaces = len(text) - len(text.rstrip())
        if rSpaces:
            rightText = text[-rSpaces:]
        text = text.rstrip()
        return text, leftText, rightText


    def fillDefaultInifile(self, ini):
        """filling entries for default ini file

        """
        if self.language == 'nld':
            ini.set('brackets', 'aanhalingstekens', '""')
            ini.set('brackets', 'kwoots', "''")
            ini.set('brackets', 'brekkits', '[]')
            ini.set('brackets', 'haakjes', '()')
            ini.set('brackets', 'punt haakjes', '<>')
            ini.set('brackets', 'driedubbele aanhalingstekens', '""""""')
            ini.set('brackets', 'accolades', '{}')
            ini.set('brackets', 'html punt haakjes', "&lt;|>")
            ini.set('brackets', 'html brekkits', "&#091;|]")
        else:
            ini.set('brackets', 'double quotes', '""')
            ini.set('brackets', 'quotes', "''")
            ini.set('brackets', 'single quotes', "''")
            ini.set('brackets', 'square brackets', '[]')
            ini.set('brackets', 'brackets', '()')
            ini.set('brackets', 'parenthesis', '()')
            ini.set('brackets', 'backticks', '``')
            ini.set('brackets', 'parens', '()')
            ini.set('brackets', 'angle brackets', '<>')
            ini.set('brackets', 'triple quotes', '""""""')
            ini.set('brackets', 'html angle brackets', "&lt;|>")
            ini.set('brackets', 'html square brackets', "&#091;|]")
            ini.set('brackets', 'braces', '{}')

# standard stuff Joel (adapted for possible empty gramSpec, QH, unimacro)
bracketsGrammar = BracketsGrammar()
if bracketsGrammar.gramSpec:
    bracketsGrammar.initialize()
else:
    bracketsGrammar = None


def unload():
    global bracketsGrammar
    if bracketsGrammar: bracketsGrammar.unload()
    bracketsGrammar = None
