"""
This file is part of a Github project (formerly a SourceForge project)
called "unimacro" see http://qh.antenna.nl/unimacro
(c) copyright 2003 see http://qh.antenna.nl/unimacro/aboutunimacro.html
    or the file COPYRIGHT.txt in the natlink\natlink directory 

  _tags.py: make HTML tags
  
  The basics, make a tags work (again), more testing should be done

written by: Quintijn Hoogenboom (QH softwaretraining & advies)
august 2003/March 2022 (python3)/August 2024
#
"""
#pylint:disable=C0116, W0603, W0613, W0201, R0912
import natlink
import unimacro.natlinkutilsbj as natbj
from dtactions import unimacroutils
from dtactions.unimacroactions import doKeystroke as keystroke
from dtactions.unimacroactions import doAction as action
# from dtactions.natlinkclipboard import Clipboard
# natlinkclipboard is not safe at the moment. 

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
        self.onlyOpen = self.onlyClose = self.empty = False
        
    def gotResults_tags(self,words,fullResults):
        self.letters = self.getFromInifile(words, 'tagname', noWarning=1)
        if not self.letters:
            print('_tags, no valid tagname found: {words}')
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
        """set the following instance variables
        """
        self.empty = bool(self.hasCommon(words, 'Empty'))
        self.onlyOpen = bool(self.hasCommon(words, ['Begin', 'Open']))
        self.onlyClose = bool(self.hasCommon(words, ['Close', 'End']))
        

    def gotResults(self,words,fullResults):
        tag = self.letters.strip()
##        print 'rule gotResults: %s'% tag
        pleft = pright = ""
        if not tag:
            return
        pleft = f'<{tag}>'
        if tag.find(' ') >= 0:
            endTag  = ' '.split(tag, maxsplit=1)[0]
        else:
            endTag = tag
        pright = f'</{endTag}>'

        # see of something selected, leave clipboard intact 
        # cb =  Clipboard(save_clear=True)
        unimacroutils.saveClipboard()
        keystroke('{shift+right}')   # take one extra char for the clipboard to hit
        action('<<cut>>')
        action('W')
        cb_text = unimacroutils.getClipboard()
        unimacroutils.restoreClipboard()
        if cb_text:
            contents, lastchar = cb_text[:-1], cb_text[-1]
        else:
            action('<<undo>>')
            raise OSError('no value in clipboard, restore cut text (probably at end of file)')
        print(f'_tags, got from clipboard: "{contents}" + extra char: "{lastchar}"')

        # contents = cb.Get_text()   #.replace('\r','').strip()
        if not self.onlyClose:
            keystroke(pleft)
        if self.empty:
            if contents:
                print(f'_tags: ask for empty, but have contents: "{contents}", ignore these')
        else:
            keystroke(contents)
        if self.onlyOpen:
            if lastchar:
                keystroke(lastchar)
                keystroke('{left %s}'% len(lastchar))
        else:            
            keystroke(pright)
            if lastchar:
                keystroke(lastchar)
                keystroke('{left %s}'% len(lastchar))
            if not self.onlyClose:
                if pright:
                    keystroke('{left %s}'% len(pright))

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
            print('-----filling ini file {self.__module__}, invalid language: "{self.language}"!')
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

