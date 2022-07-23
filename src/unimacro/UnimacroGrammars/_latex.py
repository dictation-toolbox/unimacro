"""Unimacro grammar to Dictate latex markup, as defined in an inifile

"""
# This file is part of a SourceForge project called "unimacro" see
# http://unimacro.SourceForge.net and http://qh.antenna.nl/unimacro
# (c) copyright 2003 see http://qh.antenna.nl/unimacro/aboutunimacro.html
#    or the file COPYRIGHT.txt in the natlink\natlink directory 
#
# _latex.py: Dictate latex markup
#
# written by: Frank Olaf Sem-Jacobsen
# March 2011
#

import natlink
import nsformat
from dtactions.unimacro import unimacroutils
from natlinkcore import natlinkutils as natut
from dtactions.unimacro import unimacroutils
import unimacro.natlinkutilsbj as natbj
from dtactions.unimacro.unimacroactions import doAction as action
from dtactions.unimacro.unimacroactions import doAction as action

language = unimacroutils.getLanguage()        
ICAlphabet = natbj.getICAlphabet(language=language)

# import re
# reBracedActions = re.compile(r"\{")

ancestor = natbj.IniGrammar
class ThisGrammar(ancestor):
    language = unimacroutils.getLanguage()        


    name = "latex"
    gramSpec = """
<dgndictation> imported;
<structure> exported =  begin {floating} [<dgndictation>];
<reference> exported =  reference ({floating} | {label}) <dgndictation>;
<namereference> exported =  name reference ({floating} | {label}) <dgndictation>;
<label> exported =  label ({floating} | {label}) <dgndictation>;
<command> exported =  {commands} [with] [ (arguments [{arguments}]) | (that | ([this] line)) ] [(and | with) label];
<options> exported =  add option [{options}];
<replace> exported = replace {placeholders} [with <dgndictation>]; 
    """

    def initialize(self):
        if not self.language:
            print("no valid language in grammar "+__name__+" grammar not initialized")
            return

        self.load(self.gramSpec)
        self.switchOnOrOff()

    def gotBegin(self,moduleInfo):
        if self.checkForChanges:
            self.checkInifile()

    def gotResultsInit(self,words,fullResults):
        self.dictation = ''
        self.floating = ''
        self.label = 0
        self.reference = ''
        self.namereference = ''
        self.label_text=''
        self.Cmd = ''
        self.replace_text = 0

    def gotResults_replace(self, words, fullResults):
        place = self.getFromInifile(words, 'placeholders', noWarning=1)
        action('<<startsearch>>')
        keystroke(place)
        action('<<searchgo>>')
        action('<<cancel>>')
        if self.hasCommon(words, ['with']):
            self.replace_text = 1

    def gotResults_command(self, words, fullResults):
        initial=self.getFromInifile(words, 'commands', noWarning=1)
        pos = initial.find('{')
        print(pos)
        contents =''
        if self.hasCommon(words, ['arguments']):
            if pos > 0:
                Cmd = initial[:pos + 1]
            else:
                Cmd = initial+'{'
            args  = self.getFromInifile(words, 'arguments', noWarning=1)
            Cmd = Cmd+args + '}'
            print(Cmd)
        else:
            Cmd = initial
        if self.hasCommon(words, ['that']):
            contents = self.get_selection_that(line = 0)
        if self.hasCommon(words, ['line']):
            contents = self.get_selection_that(line = 1)


        stringpaste(Cmd)
        if pos > 0  or self.hasCommon(words, ['arguments']):
            keystroke('{left}')
        if contents:
            if pos ==  - 1:
                stringpaste('{')
            stringpaste(contents)
            if pos == -1:
                stringpaste('}')
            else:
                keystroke('{right}')
        if self.hasCommon(words, ['label']):
            label =self.getFromInifile(words, 'label', noWarning=1)
            if label:
                ## workaround for keystrokes: {{}
                keystroke('{enter}')
                stringpaste(r'\label{}%s}'% (self.makes_label(label, contents)))
                keystroke('{enter}')
                
    def gotResults_options(self, words, fullResults):
        selection = self.view_selection_current_line()
        options = self.getFromInifile(words, 'options', noWarning=1)
        present = 1
        squared = selection.find(']')
        only = 1
        if squared  == -1:
            squared = selection.find('{')
            present = 0
        else:
            squared = squared +1
            start = selection.find ('[')
            if start!= squared -2:
                only = 0
        if squared ==  - 1:
            keystroke('{end}')
        else:
            keystroke('{home}')
            for i in range(0, squared):
                keystroke('{right}')
            if present == 0:
                keystroke('[')
            if options:
                if present == 1:
                    keystroke('{left}')
                if only == 0:
                    keystroke (',')
                keystroke(options)
            if present == 0:
                keystroke(']')
            if not options:
                keystroke('{left}')
            

    def gotResults_reference(self, words, fullResults):
        self.reference = self.getFromInifile(words, 'floating', noWarning=1) or \
                         self.getFromInifile(words, 'label', noWarning = 1)
                         
    def gotResults_namereference(self, words, fullResults):
        self.namereference = self.getFromInifile(words, 'floating', noWarning=1) or \
                         self.getFromInifile(words, 'label', noWarning = 1)                  

    def gotResults_label(self, words, fullResults):
        self.label_text = self.getFromInifile(words, 'floating', noWarning=1) or \
                         self.getFromInifile(words, 'label', noWarning = 1)
                                                 
    def gotResults_structure(self, words, fullResults):
        self.floating=self.getFromInifile(words, 'floating', noWarning=1)
      
    
    def gotResults(self, words, fullResults):
        if self.floating:
            floatingString = r'\begin{%s}'% self.floating
            stringpaste(floatingString)
            keystroke('{enter}')
            if self.dictation:
                labelString = self.makes_label(self.floating, self.dictation)
                dictationString = r'\label{%s}'% labelString
                stringpaste(dictationString)
            keystroke ('{enter}')
            floatingString = '\\end{%s}'% self.floating
            stringpaste(floatingString)
            keystroke('{up}')
            print('floating: %s'% self.floating)
        if self.reference:
            stringpaste ('\\ref{%s}' % (self.makes_label(self.reference, self.dictation)))
        if self.namereference:
            stringpaste ('\\nameref{%s}' % (self.makes_label(self.namereference, self.dictation)))
        if self.label_text:
            stringpaste ('\\label{%s}' % (self.makes_label(self.label_text, self.dictation)))
        if self.replace_text:
            stringpaste (self.dictation)
        

    def gotResults_dgndictation(self, words, fullResults):
        """do with nsformat functions"""
        print('got dgndictation: %s'% words)
        self.dictation, dummy = nsformat.formatWords(words)  # state not needed in call
        print('   result of nsformat:  %s'% repr(self.dictation))


    def get_selection_that(self, line = 0):
        unimacroutils.saveClipboard()

        if line:
            action('<<selectline>><<cut>>')
        else:
            action('<<cut>>')
        contents = natlink.getClipboard().strip().replace('\r', '')
        if len(contents) == 0:
            if line:
                print('_latex, empty line')
                return ""
            action('HW select that')
            action('<<cut>>')
            contents = natlink.getClipboard().strip().replace('\r', '')
            if len(contents) == 0:
                print('_latex, empty contents, no last dicatate utterance available')
                
        unimacroutils.restoreClipboard()
        return contents

    def view_selection_current_line(self):
        unimacroutils.saveClipboard()
        keystroke('{ctrl+c}')
        contents = natlink.getClipboard()
        if len(contents) == 0:
            print('no_space_by_existing selection')
            keystroke('{end}{shift+home}')
            keystroke('{ctrl+c}')
            contents = natlink.getClipboard()
        unimacroutils.restoreClipboard()
        return contents



    def makes_label(self, type, text):
        return type + ':' + ''.join(text.split()).lower()
  
def stringpaste(t):
    """paste via clipboard, to circumvent German keyboard issues
    """
    action('SCLIP "%s"'%t)
    


# standard stuff Joel (QH, Unimacro)
thisGrammar = ThisGrammar()
if thisGrammar.gramSpec:
    thisGrammar.initialize()
else:
    thisGrammar = None

def unload():
    #pylint:disable=W0603
    global thisGrammar
    if thisGrammar: thisGrammar.unload()
    thisGrammar = None

