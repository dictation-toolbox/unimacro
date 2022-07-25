"""
This file is part of a Github project (formerly a SourceForge project)
called "unimacro" see http://qh.antenna.nl/unimacro
(c) copyright 2003 see http://qh.antenna.nl/unimacro/aboutunimacro.html
    or the file COPYRIGHT.txt in the natlink\natlink directory 

  _tags.py: make HTML tags

written by: Quintijn Hoogenboom (QH softwaretraining & advies)
august 2003/March 2022 (python3)
#
"""
#pylint:disable=C0116, W0603, W0613, W0201
import natlink
import unimacro.natlinkutilsbj as natbj
from dtactions.unimacro import unimacroutils
from dtactions.unimacro.unimacroactions import doAction as action
from dtactions.unimacro.unimacroactions import doKeystroke as keystroke
from dtactions.natlinkclipboard import Clipboard

language = unimacroutils.getLanguage()        

ancestor = natbj.IniGrammar
class ThisGrammar(ancestor):
    """grammar that makes html tags, as defined in an inifile
    """

    language = unimacroutils.getLanguage()        
    iniIgnoreGrammarLists = ['character']

    name = "tags"
    gramSpec = """
<tags> exported = (Tag | HTML Tag | <prefix> Tag | <prefix> HTML Tag )({tagname}|{character}+);
<prefix> = Open | Close | Begin | End | Empty;
    """

    def initialize(self):
        if not self.language:
            print("no valid language in grammar "+__name__+" grammar not initialized")
            return

        self.load(self.gramSpec)
        self.setCharactersList('character')        
        self.switchOnOrOff()

    def gotBegin(self,moduleInfo):
        if self.checkForChanges:
            self.checkInifile()

    def gotResultsInit(self,words,fullResults):
        self.letters = ''
        self.pleft = ''
        self.pright = ''
        self.dictated = ''
        self.onlyOpen = self.onlyClose = self.empty = 0
        
    def gotResults_tags(self,words,fullResults):
        self.letters = self.getFromInifile(words, 'tagname', noWarning=1)
        if not self.letters:
            print('_tags, no valid tagname found: %s'% words)
            return
        for w in words:
            char = self.getCharacterFromSpoken(w)
            if char:
                self.letters += char

    #def gotResults_dgndictation(self,words,fullResults):
    #    """return dictated text, put in between (or before or after the tags)
    #    """
    #    self.dictated, dummy = nsformat.formatWords(words, state=-1)  # no capping, no spacing
    #    #print '-result of nsformat: |%s|'% repr(self.dictated)
    

    def gotResults_prefix(self,words,fullResults):
        self.empty = self.hasCommon(words, ['Empty', 'Lege'])
        self.onlyOpen = self.hasCommon(words, ['Begin', 'Open'])
        self.onlyClose = self.hasCommon(words, ['Sluit', 'Close', 'End', 'Eind'])


    def gotResults(self,words,fullResults):
        tag = self.letters.strip()
##        print 'rule gotResults: %s'% tag
        pleft = pright = ""
        if not tag:
            return
        pleft = '<%s>' % tag
        if tag.find(' ') >= 0:
            endTag  = ' '.split(tag)[0]
        else:
            endTag = tag
        pright = '</%s>' % endTag

        # see of something selected, leave clipboard intact 
        cb =  Clipboard(save_clear=True)
        keystroke('{ctrl+x}')  # try to cut the selection
        contents = cb.Get_text()   #.replace('\r','').strip()
        
        keystroke(pleft)
        if contents:
            #print 'contents: |%s|'% repr(contents)
            keystroke(contents)
        keystroke(pright)

        if not contents:
            # go back so you stand inside the brackets:
            nLeft = len(pright)
            keystroke('{left %s}'% nLeft)

    def fillDefaultInifile(self, ini):
        """filling entries for default ini file

        """
        ancestor.fillDefaultInifile(self, ini)
        if self.language == 'nld':
            tagNames = {
                'Hedder 1':  'h1',
                'Hedder 2':  'h2',
                'Hedder 3':  'h3',
                'tabel':  'table',
                'tabel honderd procent':  'table border="0" cellpadding="0" cellspacing="0" width="100%"',
                'tabel data':  'td',
                'tabel roo':  'tr',
                'Java script':  'script language="JavaScript"', 
                'script':  'script'
            }
            
        elif self.language == 'enx':
            tagNames = {
                'Header 1':  'h1',
                'Header 2':  'h2',
                'Header 3':  'h3',
                'table':  'table',
                'table data':  'td',
                'table row':  'tr',
                'Java script':  'script language="JavaScript"', 
                'script':  'script'
            }
        else:
            print('-----filling ini file %s , invalid language: "%s"! '% \
                  (self.__module__, self.language))
            ini.set('general', 'error', 'invalid language')
            return
        for k, v in list(tagNames.items()):
            ini.set('tagname', k, v)
        # by default switch off initially:
        ini.set('general', 'initial on', '0')

            
def stripSpokenForm(w):
    pos = w.find('\\')
    if pos == -1:
        return w
    if pos == 0:
        return ' '
    return w[:pos]

# standard stuff Joel (adapted for possible empty gramSpec, QH, unimacro)
if natlink.isNatSpeakRunning(): 
    thisGrammar = ThisGrammar()
    if thisGrammar.gramSpec:
        thisGrammar.initialize()
    else:
        thisGrammar = None
    
    def unload():
        global thisGrammar
        if thisGrammar:
            thisGrammar.unload()
        thisGrammar = None

