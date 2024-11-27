# This file is part of a SourceForge project called "unimacro" see
# http://unimacro.SourceForge.net and http://qh.antenna.nl/unimacro
# (c) copyright 2003 see http://qh.antenna.nl/unimacro/aboutunimacro.html
#    or the file COPYRIGHT.txt in the natlink\natlink directory
#
#  _brackets.py
# written by: Quintijn Hoogenboom (QH softwaretraining & advies)
# august 2003, revision october 2011, python3: september 2021
""" unimacro grammar that puts brackets, braces etc.

Basically two ways are implemented:

1. Say: "between brackets hello comma this is a test"
2. select text, and say "between brackets"
3. say "empty braces"
4. say "here parens"

Notes:
======
1. If you start or end with space-bar (or other white space),
   this will be put OUTSIDE the brackets.

2. No capitalisation is done unless you call as directive.

3. Dictation errors cannot be corrected with the spell window. Select, 
dictate again and then correct then if needed.

Note: the natlinkclipboard module from dtactions is not ready for use. Use
the unimacroutils module of unimacro.


"""
#pylint:disable=C0115, C0116, W0201, W0613
from natlinkcore import nsformat
from dtactions import unimacroutils
from dtactions.unimacroactions import doAction as action
from dtactions.unimacroactions import doKeystroke as keystroke
# from dtactions.natlinkclipboard import Clipboard
import unimacro.natlinkutilsbj as natbj
import natlink

language = unimacroutils.getLanguage()

ancestor = natbj.DocstringGrammar
class BracketsGrammar(ancestor):
    language = unimacroutils.getLanguage()
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
        self.here, self.between, self.empty = False, False, False
        if self.mayBeSwitchedOn == 'exclusive':
            print(f'recog brackets, switch off mic: {words}')
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
                print(f'no valid brackets found for word: "{w}"')
                continue
            #print 'brackets, found: %s, %s'% (w, p)
            if len(p) > 2 and p.find("|") > 0:
                pList = p.split("|")
                newpleft = pList[0]
                newpright = pList[1]
            else:
                lenph = len(p)//2
                newpleft, newpright = p[:lenph], p[lenph:]
            # make more brackets together, from outer to inner:
            self.pleft = self.pleft + newpleft
            self.pright = newpright + self.pright
        # print(f'result rule_brackets: |{self.pleft}|, pright: |{self.pright}|')

    def subrule_before(self, words):
        "(here|between|empty)+"

        for w in words:
            if self.hasCommon(w, 'between'):   # this is the trigger word, ignore
                self.between = True
            if self.hasCommon(w, 'here'):   # this is the trigger word, ignore
                self.here = True
            if self.hasCommon(w, 'empty'):   # this is the trigger word, ignore
                self.empty = True
  

    def gotResults(self, words, fullResults):

        #  see if something selected, leaving the clipboard intact
        #  keystroke('{ctrl+x}')  # try to cut the selection
        # if no text is dictated, self.dictated = ""
        text, leftTextDict, rightTextDict = stripFromBothSides(self.dictated)

        if self.here:
            print('do a left buttonClick')
            unimacroutils.buttonClick('left', 1)
            unimacroutils.visibleWait()


        if self.empty:
            if self.dictated:
                print(f'_brackets, warning, dictated text "{self.dictated}" is ignored, because of keyword "empty"')
            self.do_keystrokes_brackets()
            return
        
        # only if no dictated text, try to cut the selection (if there, add one char for safety with
        # the clipboard actions, only fails when at end of file)
        if not self.dictated:
            unimacroutils.saveClipboard()
            keystroke('{shift+right}')   # take one extra char for the clipboard to hit
            action('<<cut>>')
            action('W')
            cb_text = unimacroutils.getClipboard()
            unimacroutils.restoreClipboard()
            if cb_text:
                text, lastchar = cb_text[:-1], cb_text[-1]
            else:
                action('<<undo>>')
                raise OSError('no value in clipboard, restore cut text')
            print(f'_brackets, got from clipboard: "{text}" + extra char: "{lastchar}"')
            self.do_keystrokes_brackets(text=text, lastchar=lastchar)
            return

        self.do_keystrokes_brackets(text=text, l_spacing=leftTextDict, r_spacing=rightTextDict)

#
    def do_keystrokes_brackets(self, text='', lastchar='', l_spacing='', r_spacing=''):
        """do the pleft text pright keystrokes with spacing issues
        
        handle the "between" keyword here!
        """
        keystroke(l_spacing)
        keystroke(self.pleft)
        unimacroutils.visibleWait()
        if text:
            keystroke(text)
            unimacroutils.visibleWait()
        keystroke(self.pright)
        keystroke(r_spacing)
        if lastchar:
            keystroke(lastchar)
            keystroke("{left %s}"% len(lastchar))
        if self.between:
            keystroke("{left %s}"% len(self.pright))
        

def stripFromBothSides(text):
    """strip whitespace from left side and from right side and return
the three parts

    input: text
    output: stripped, leftSpacing, rightSpacing
    """
    if not text:
        return "", "", ""
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

# standard stuff Joel (adapted in course of time, QH)
def unload():
    #pylint:disable=W0603, E0601
    global bracketsGrammar
    if bracketsGrammar:
        bracketsGrammar.unload()
    bracketsGrammar = None


if __name__ == "__main__":
    natlink.natConnect()
    try:
        bracketsGrammar = BracketsGrammar(inifile_stem='_brackets')
        bracketsGrammar.startInifile()
        bracketsGrammar.initialize()
    finally:
        natlink.natDisconnect()
else:
    bracketsGrammar = BracketsGrammar()
    if bracketsGrammar.gramSpec:
        bracketsGrammar.initialize()
    else:
        bracketsGrammar = None
        
