# This was the old "general" intro for all unimacro grammar files:
# This file is part of a SourceForge project called "unimacro" see
# http://unimacro.SourceForge.net and http://qh.antenna.nl/unimacro
# (c) copyright 2003 see http://qh.antenna.nl/unimacro/aboutunimacro.html
#    or the file COPYRIGHT.txt in the natlink\natlink directory 
#
#  _general.py
#
# written by Quintijn Hoogenboom (QH softwaretraining & advies),
#
#
#pylint:disable=C0302, R0904, C0209, C0321, R0912, R0914, R0915, R0911
#pylint:disable=E1101 

"""do a set of general commands

"""
import re
import os
import sys
import time
import pprint
from pathlib import Path

import win32gui

import natlink
from natlinkcore import natlinkstatus
from natlinkcore import nsformat 
from natlinkcore import natlinkutils as natut
from natlinkcore import natlinktimer
from unimacro import natlinkutilsbj as natbj
from unimacro import namelist # for name phrases

from dtactions.unimacroactions import doAction as action
from dtactions.unimacroactions import doKeystroke as keystroke
from dtactions import unimacroactions as actions
from dtactions import unimacroutils

# taskswitching moved to _tasks.py (july 2006)

Counts = list(range(1,20)) + list(range(20,51,5))

# for taskswitch:
Handles = {}
#systray:
systrayHndle = 0

status = natlinkstatus.NatlinkStatus()
language = status.language
FORMATS = {
    # for letters (do nothing):
    'no spacing': (unimacroutils.wf_NoSpaceFollowingThisWord | unimacroutils.wf_NoSpacePreceedingThisWord |
                   unimacroutils.wf_TurnOffSpacingBetweenWords |
                      unimacroutils.wf_DoNotApplyFormattingToThisWord
          ),
    # normal words:
    'normal words': ( unimacroutils.wf_RestoreNormalCapitalization |
            unimacroutils.wf_RestoreNormalSpacing
          ),
    # extra space(do one space):
    'extra space':  ( unimacroutils.wf_RestoreNormalCapitalization |
            unimacroutils.wf_RestoreNormalSpacing |
            unimacroutils.wf_AddAnExtraSpaceFollowingThisWord
          ), 
    }

user = status.user
unimacro_user_dir = status.getUnimacroUserDirectory()
wordsFolder = f'{unimacro_user_dir}\\{language}_words'
if not Path(wordsFolder).is_dir():
    Path(wordsFolder).mkdir()
files = [os.path.splitext(f)[0] for f in os.listdir(wordsFolder)]
## print '_general, files in wordsFolder %s: %s'% (wordsFolder, files)

if language == 'enx':
    nameList = {'Q. H.': 'QH',
                 'R. A.': 'RA',
                'underscore': '',
                 }
elif language == 'nld':
    nameList = {'QH': 'QH',
                 'er aa': 'RA',
                'underscore': '',
                 }
else:
    nameList = {}
        

switchDirection = {
      "{Up}":      "{Down}",
      "{Down}":    "{Up}",
      "{Left}":    "{Right}",
      "{Right}":   "{Left}"}

modes = ['spell', 'command', 'numbers', 'normal', 'dictation', 'dictate']
normalSet = ['test', 'reload', 'info', 'undo', 'redo', 'namephrase', 
             'comment', 'documentation', 'modes', 'variable', 'search',
             'highlight',         # for Shane, enable, because Vocola did not fix _anything yet
             'browsewith', 'hyphenatephrase', 'pastepart',
             'password', 'choose']
#normalSet = ['hyphenatephrase']  # skip 'openuser'

commandSet = normalSet[:] + ['dictate']
thisGrammar = None

ancestor=natbj.IniGrammar
class ThisGrammar(ancestor):
    # pylint: disable=C0116, W0613, W0201

    iniIgnoreGrammarLists = ['modes','count', 'namelist', 'character', 'punctuation']

    language = unimacroutils.getLanguage()        

    try:
        number_rules = natbj.numberGrammar[language] #  including millions
    except KeyError:
        number_rules = natbj.numberGrammar['enx']

    name = "general"
    gramSpec = ["""
<before> = Command | Here;
<dgnletters> imported;
<dgndictation> imported;
# <dgnwords> imported;
<documentation> exported = Make documentation;
<test> exported = test micstate;
<choose> exported = choose {n1-10};
<reload> exported = reload Natlink;
<info> exported = give (user|prog|window|unimacro|path|timer) (info|information) ;
<undo> exported = Undo [That] [{count} [times]];
<redo> exported = Redo [That] [{count} [times]];
<namephrase> exported = Make That [Name] phrase;
<pastepart> exported = [<before>] Paste part {n1-10};
<pasteallparts> exported = Paste all parts;
<hyphenatephrase> exported = Hyphenate (phrase| last word | last ({n2-5}) words);
<comment> exported = Comment {namelist};
<variable> exported = {formatvariable} ((Back [{n1-5}]) | <dgndictation>);
<modes> exported = {modes} mode;
<highlight> exported = highlight <dgndictation>;         # for Shane,
<search> exported = search ('go back'|new|
                            ((for|before|after|extend|insert)([{searchwords}] (<dgndictation>|<characterpunctuation>+)))|
                            ((forward|back|up|down|reverse) [{count} [times]]));
<characterpunctuation> = space|capital|{character}|{punctuation};
<browsewith> exported = ('browse with') {browsers};
<openuser> exported = 'open user' {users};
<password> exported = 'password' <dgndictation>;
<presscode> exported = (press letter) <dgnletters>;

    """]
# A\determinerNormalTestThisNowI\pronounTest.\period\full stop
#NormalTestNormalI\pronounTestNormallyTestNormalAttestNormal.\period\periodSigns
#HelloTesting
    
    def initialize(self):
        if self.language:
            self.load(self.gramSpec)
            self.switchOnOrOff(activateSet=normalSet) # initialises lists from inifile, and switches on
                             # if all goes well (and variable onOrOff == 1)
            # search commands:
            self.setCharactersList('character')
            self.setPunctuationList('punctuation')
            self.specialSearchWords = self.Lists['searchwords'] or [] # like function, class of (inifile) section
            # print('specialSearchWords: %s'% self.specialSearchWords)
            self.setNumbersList('count', Counts)
            self.setList('modes', modes)
            self.gotPassword = 0
            self.passwordEnding = None
            self.gotPresscode = 0
            # print "%s, activateSet: %s"% (self.name, normalSet)
            # self.deactivateAll()  # why is this necessary? The activateAll in switchOn is definitly now Ok...
            self.title = 'Unimacro grammar "'+__name__+'" (language: '+self.language+')'
        else:
            print("no valid language in grammar "+__name__+" grammar not initialized")

    def gotBegin(self,moduleInfo):
        if self.checkForChanges:
            self.checkInifile() # refills grammar lists and instance variables
                                # if something changed.
        self.gotPassword = 0
        self.progInfo = unimacroutils.getProgInfo(moduleInfo)
        
    def gotResults_wrongrule(self,words,fullResults):
        natut.playString("%s\n"% fullResults)

    def gotResultsInit(self,words,fullResults):
        self.fullText = ' '.join(words)
        self.progName = unimacroutils.getProgName()

        # variable formatting
        self.gotVariable = ""

        # for Shane
        self.search = self.dictate = self.highlight = 0
        self.text = ''
        self.minimalapp=None
        # self.specialSearchWords = None

        if words[0] in ['Hier', 'Here']:
            print('Here from _general...')
            natut.buttonClick()
            unimacroutils.Wait()
        self.progInfo = unimacroutils.getProgInfo()
    def gotResults_password(self,words,fullResults):
        """interpret password as dictate
        Cap dictation words
        if number precedes @ 
        
        """
        self.gotPassword = 1

    def gotResults_pastepart(self,words,fullResults):
        """paste part of clipboard, parts are separated by ";"
        """
        n = self.getNumberFromSpoken(words[-1])
        t = unimacroutils.getClipboard()
        print('(%s) %s'% (type(t), t))
        T = self.partsSplitSpecial(t)
        if n <= len(T):
            keystroke(T[n-1])
            # action("SCLIP %s"% T[n-1])
        else:
            print('_general, pastepart: length of list only: %s (t: %s)'% (len(T), t))

    def gotResults_pasteallparts(self,words,fullResults):
        """paste parts, separated by ";" with a hard set keystroke in between
        
        Used for pasting multiple addresses in Thunderbird address book
        """
        # n = self.getNumberFromSpoken(words[-1])
        t = unimacroutils.getClipboard()
        print('(%s) %s'% (type(t), t))
        T = self.partsSplitSpecial(t)
        print('put item by item %s words'% len(T))
        for t in T:
            keystroke(t)
            keystroke("{enter}")
            action("VW")

    def partsSplitSpecial(self, t):
        """normally split by ;
        in special cases, eg for coordinates the split can be different
        """
        reCoords = re.compile(r"(.*?) N([0-9\.]+) +E([0-9\.]+)$")
        # Title of place XX N51.5888  E5.901
        m = reCoords.match(t)
        if m:
            parts = m.groups()
            print('coordinates: %s, length: %s'% (repr(parts), len(parts)))
        elif t.find(";") >= 0:
            parts = [t.strip() for t in t.split(";")]
            print('splitted string: %s, length: %s'% (repr(parts), len(parts)))
        else:
            parts = [t]
            print('cannot split text: %s\nreturn list of length 1: %s'% (t, parts))
        return parts
        
    def gotResults_before(self,words,fullResults):
        if self.hasCommon(words, 'here'):
            natut.buttonClick('left', 1)

    def gotResults_highlight(self,words,fullResults):
        # for Shane
        self.highlight = 1

    def gotResults_search(self,words,fullResults):
        self.search = 1
        if words[0] in self.specialSearchWords:
            self.specialSearchWord = self.getFromInifile(words[0], 'searchwords')
            print('do search with special search word: %s (%s)'% (self.specialSearchWord, words[0]))
            words.pop(0)

        counts = self.getNumbersFromSpoken(words, Counts)
        if counts:
            self.count = counts[0]
        else:
            self.count = None
        if self.hasCommon(words, ['new', 'nieuw']):
            self.search = 'new'
        elif self.hasCommon(words, ['back', 'up', 'omhoog', 'terug', 'achteruit']):
            self.search = 'back'
        elif self.hasCommon(words, ['reverse']):
            self.search = 'reverse'
        elif self.hasCommon(words, ['forward', 'down', 'vooruit', 'omlaag', 'verder']):
            self.search = 'forward'
        elif self.hasCommon(words, ['go back', 'ga terug']):
            self.search = 'go back'
        elif self.hasCommon(words, ['for', 'naar']):
            self.search = 'for'
        elif self.hasCommon(words, ['before', 'voor']):
            self.search = 'before'
        elif self.hasCommon(words, ['after', 'na']):
            self.search = 'after'
        elif self.hasCommon(words, ['insert', 'invoegen']):
            self.search = 'insert'
        elif self.hasCommon(words, ['extend', 'uitbreiden']):
            self.search = 'extend'

        # provisions for extra special keywords (in front of spelled characters)            
        self.specialSearchWord = self.hasCommon(words, self.specialSearchWords)


    def gotResults_dictate(self,words,fullResults):
        self.dictate = 1

    def gotResults_dgnletters(self,words,fullResults):
        self.text = ''.join(map(unimacroutils.stripSpokenForm, words))
        if self.search:
            # catch some common misrecognitions:
            if self.text == '4':
                print(f'caught dgnletters {self.text}, switch to forward search')
                self.text = ''
                self.search = 2 # forward search
            elif self.text in ['43', '403']:
                print(f'caught dgnletters {self.text}, switch to forward search 3')
                self.text = ''
                self.count = 3
                self.search = 2 # forward search
            return
        if self.gotPresscode:
            print(f'gotPresscode: {words} -> {self.text}')
            self.do_pressfirst(self.text)
            return
        
        
    def gotResults_characterpunctuation(self,words,fullResults):
        capNext = 0
        for w in words:
            if self.hasCommon(w, "capital"):
                print('got word (synonym of) "capital": %s'% w)
                capNext = 1
                continue
            if self.hasCommon(w, "space"):
                self.text += " "
                capNext = 0
                continue
            char = self.getCharacterFromSpoken(w)
            if char:
                if capNext:
                    self.text += char.upper()
                    capNext = 0
                else:
                    self.text += char
            else:
                capNext = 0
                char = self.getPunctuationFromSpoken(w)
                if char:
                    self.text += char
                else:
                    print('general: character or punctuation not found for spoken form: %s'% w)
        
    # def gotResults_dgnwords(self,words,fullResults):
    #     #self.text = ' '.join(map(unimacroutils.stripSpokenForm, words))
    #     # try with the improved nsformat function
    #     print(f'got dgnwords: {words}')

    def gotResults_dgndictation(self,words,fullResults):
        #self.text = ' '.join(map(unimacroutils.stripSpokenForm, words))
        # try with the improved nsformat function 
        if self.gotPassword:
            print('gotPassword, analyse password: %s'% words)
            text = nsformat.formatPassword(words)
            keystroke(text)
            self.gotPassword = 0
            return
        if self.gotVariable:
            print('do variable trick %s on %s'% (self.gotVariable, words))
            vartrick = self.gotVariable
            funcName = 'format_%s'% vartrick
            # print 'funcName: %s'% funcName
            try:
                func = getattr(self, funcName)
                # print 'func: %s'% func
            except AttributeError:
                print('no formatfunction for variable trick: %s'% vartrick)
                return

            result = func(words)
#
            keystroke(" " + result)
            return
        if self.gotPresscode:
            self.text = ' '.join(map(unimacroutils.stripSpokenForm, words))
            print(f'got dgndictation: {words} -> {self.text}')
            self.do_pressfirst(self.text)
            return
        #very well for like this
        if self.search and self.text in ['on', 'verder']: # 
            self.search = 2
        elif self.search and self.text in ['new', 'nieuw']:
            self.search = 3
        elif self.search and self.text in ['terug', 'back']:
            self.search = 4
        print('dgndictation: %s'% self.text)

    def format_camel(self, words):
        """format camel case, rule variable
        var like this -> varLikeThis
        """
        if not words: return ""   #
        newWords = [w.capitalize() for w in words]
        newWords[0] = newWords[0].lower()
        return ''.join(newWords)

    def format_studly(self, words):
        """format studly case, rule variable
        var like this -> VarLikeThis
        """
        if not words: return ""   #
        newWords = [w.capitalize() for w in words]
        return ''.join(newWords)

    def format_dotword(self, words):
        """format dotword, rule variable
        var like this -> var.like.this
        """
        if not words: return ""   #
        return '.'.join(words)

    def format_jive(self, words):
        """format jive case, rule variable
        var like this -> var-like-this
        """
        if not words: return ""   #
        return '-'.join(words)

    def format_score(self, words):
        """format score, with underscores, rule variable
        var like this -> var_like_this
        """
        if not words: return ""   #
        return '_'.join(words)

# try for like this

#
    def gotResults_browsewith(self,words,fullResults):
        """show page in another browser"""
        progInfo = unimacroutils.getProgInfo()
        prog = progInfo.prog
        # Iam2x = prog == '2xexplorer'
        # IamExplorer = prog == 'explorer'
        browser = prog in ['iexplore', 'firefox','opera', 'netscp', 'chrome']
        if not browser:
            self.DisplayMessage ('command only for browsers')
            return
        print('words:', words)
        unimacroutils.saveClipboard()
        action('<<addressfield>>; {extend}{shift+exthome}{ctrl+c};<<addressfieldclose>>')
        askedBrowser = self.getFromInifile(words, 'browsers')
        if askedBrowser == prog:
            self.DisplayMessage('command only for another browser')
            return
        print('try to bring up browser: |%s|'% askedBrowser)
        action('RW')
        action('AppBringUp "%s"'% askedBrowser)
        action('WTC')
        action('<<addressfield>>; {ctrl+v}{enter}')
        
        unimacroutils.restoreClipboard()
 
    def gotResults_documentation(self,words,fullResults):
        print("obsolete")
#         oldPath = os.getcwd()
#         uniGrammars = self.ini.getList('documentation', 'unimacro grammars')
#         uniModules = self.ini.getList('documentation', 'unimacro modules')
#         otherGrammars = self.ini.getList('documentation', 'other grammars')
#         otherModules = self.ini.getList('documentation', 'other modules')
#         base = unimacroutils.getUnimacroUserDirectory()
#         docPath = os.path.join(base, 'doc')
#         pickleFile = os.path.join(docPath, '@unimacro.pickle')
#         try:
#             psock = open(pickleFile, 'r')
#             memory = pickle.load(psock)
#             psock.close()
#             print('--------------------memory from pickle: %s'% pickleFile)
#         except:
#             memory = {}
#             print('--------------------no or invalid pickle file: %s'% pickleFile)
#             
#         utilsqh.createFolderIfNotExistent(docPath)
#         os.chdir(docPath)
#         self.DisplayMessage('writing documentation to: %s'% docPath)
#         pydoc.writedocs(base)
#         self.DisplayMessage('checking unimacro grammars, modules and other grammars, modules')
#         allUnimacroGrammars = list(natlinkmain.loadedFiles.keys())
#         if 'unimacro grammars' not in memory:
#             memory['unimacro grammars'] = {}
#         mem = memory['unimacro grammars']
#         for m in uniGrammars:
#             if m in allUnimacroGrammars:
#                 mem[m] = sys.modules[m].__doc__
#             else:
#                 if not m in mem:
#                     mem[m] = ''
# 
#         if 'unimacro modules' not in memory:
#             memory['unimacro modules'] = {}
#         mem = memory['unimacro modules']
#         for m in uniModules:
#             if m in sys.modules:
#                 mem[m] = sys.modules[m].__doc__
#             else:
#                 try:
#                     M = __import__(m)
#                 except ImportError:
#                     print('cannot import module: %s'% m)
#                     continue
#                 mem[m] = M.__doc__
#                 mem[m] = M.__doc__
#                 del M
# 
#         print('writing to pickle file: %s'% pickleFile)
#         psock = open(pickleFile, 'w')
#         pickle.dump(memory, psock)
#         psock.close()
#         L = []
#         htmlFiles = list(filter(isHtmlFile, os.listdir(docPath)))
#         
#         
#         categories = self.ini.get('documentation')
#         if not categories:
#             self.DisplayMessage('please fill in documentation categories')
# 
#         for c in categories:
#             if not c in memory:
#                 continue
#             L.append("<H1>%s</H1>"% c)
#             mem = memory[c]
#             for m in mem:
#                 file = m+'.html'
#                 if os.path.isfile(os.path.join(docPath, m+'.html')):
#                     link = "<a href=%s.html>%s</a>"% (m, m)
#                     htmlFiles.remove(file)
#                 else:
#                     link = "???%s"% m
#                 if mem[m] == None:
#                     text = 'no doc string for this module'
#                 elif mem[m] == '':
#                     text = 'module could not be loaded, possibly start program and do "Make documentation" again'
#                 else:
#                     text = mem[m]
# 
#                 if text.find('\n\n'):
#                     T = text.split('\n\n')
#                     text = T[0]
#                 L.append("<p>%s: %s</p>"% (link, text))
#         if htmlFiles:
#             M = []
#             L.append("<H1>%s</H1>"% "other files")
#             for f in htmlFiles:
#                 if f == 'index.html':
#                     continue
#                 name = f.split('.')[0]
#                 link = "<a href=%s>%s</a>"% (f, name)
#                 M.append(link)
#             L.append("<p>%s</p>"% ', '.join(M))
#         HTMLpage = '''<!doctype html PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN">
# <html><head><title>Natlink grammars and modules documentations</title>
# <style type="text/css"><!--
# TT { font-family: lucidatypewriter, lucida console, courier }
# --></style></head><body bgcolor="#f0f0f8">
# %s
# </body></html>''' % '\n'.join(L)
#         fsock = open(os.path.join(docPath, 'index.html'), 'w')
#         fsock.write(HTMLpage)
#         fsock.close()
#                     
#         os.chdir(oldPath)
#         
#         self.DisplayMessage('okay')
        

    def gotResults_stopwatch(self,words,fullResults):
        """ stopwatch"""
        if self.hasCommon(words, 'start'):
            self.startTime = time.time()
        else:
            t = time.time()
            elapsed = t - self.startTime
            action(f'MSG {elapsed:.2f} seconds')
            self.startTime = t

    def gotResults_choose(self,words,fullResults):
        """choose alternative, via actions
                
        """
        n = self.getNumberFromSpoken(words)   # return int
        print(f'got choose: {words} -> {n}')
        action(f'<<choose {n}>>')
        
        
    def gotResults_test(self,words,fullResults):

        # micstate = natlink.getMicState()
        for ms in ('off', 'on'):
            print("switching %s mic"% ms)
            natlink.setMicState(ms)
            time.sleep(1)
            newMs = natlink.getMicState()
            time.sleep(1)
            if ms == newMs:
                time.sleep(0.5)
                continue
            print("conflicting mic states, now: %s, expected: %s"% (newMs, ms))

    def getPrevNext(self, n=1):
        """return character to the left and to the right of the cursor
        assume no selection active.
        normally return cursor in same position
        
        This one gives timing problems in Frescobaldi (lilypond edit program), the ctrl+c takes about one second.
        now try in other applications
        """
        playString = natut.playString
        prog = unimacroutils.getProgInfo()[0]
        t0 = time.time()
        unimacroutils.clearClipboard()
        t1 = time.time()
        playString("{left %s}"% n)
        t2 = time.time()
        playString("{shift+right %s}"% (n*2,))
        t3 = time.time()
        playString("{ctrl+c}")
        t4 = time.time()
        playString("{left %s}"% n)
        t5 = time.time()
        result = unimacroutils.getClipboard()
        t6 = time.time()
        print('timing getPrevNext program: %s\nclear clipboard: %.4f, left: %.4f, shiftright2: %.4f, copy: %.4f, left: %.4f, getcl: %.4f'% (
            prog, t1-t0, t2-t1, t3-t2, t4-t3, t5-t4, t6-t5))
        if len(result) == 2:
            return result[0], result[1]
        if result == '\n':
            print('getPrevNext, assume at end of file...')
            # assume at end of file, could also be begin of file, but too rare too handle
            playString("{right}")
            return result, result
        print('getPrevNext, len not 2: %s, (%s)'% (len(result), repr(result)))
        return "", result

##        
    def gotResults_reload(self,words,fullResults):
        print("reloading natlink....")
        unimacroutils.switchToWindowWithTitle("Messages from Python Macros")
        unimacroutils.Wait()
        natlink.setMicState("off")
        unimacroutils.Wait()
        print("do it yourself...")
    
   # deze regel print de naam van de huidige module in het debug-venster
    def gotResults_info(self,words,fullResults):
        """display in a message box information about the window, user or unimacro


        """
        T = []
        extra = []
        if self.hasCommon(words,'window') or self.hasCommon(words,'prog'):
            p = unimacroutils.getProgInfo()
            hndle = p.hndle
            T.append('---from unimacroutils.getProgInfo:')
            # (progpath, prog, title, toporchild, classname, hndle)
            if self.hasCommon(words, 'prog'):
                T.append(f'progInfo = {p}')
            T.append(f'  .progpath: "{p.progpath}"\n')
            T.append(f'  .prog:\t{p.prog}')
            T.append(f'  .title: "{p.title}"\n')
            T.append(f'  .toporchild\t{p.toporchild}')
            T.append(f'  .classname\t{p.classname}')
            T.append(f'  .hndle:\t{hndle}')
            # # for special behaviour:
            # childClass = "#32770"
            # overruleIsTop = self.getTopOrChild(self.progInfo, childClass=childClass)
            # 
            # if p.toporchild != overruleIsTop:
            #     T.append('')
            #     if overruleIsTop:
            #         T.append("**** treat as TOP window although it is a child window")
            #     else:
            #         T.append(f'**** treat as CHILD window although it is a top window (classname: {classname})')


        elif self.hasCommon(words,'user'):
            # status (natlinkstatus.NatlinkStatus()) is global variable
            T.append('user:\t\t%s'% status.user)
            T.append('userLanguage:\t%s'% status.language)
            # T.append('see messages window for trainuser info')
            extra = []
            
        elif self.hasCommon(words,'unimacro'):
            # status (natlinkstatus.NatlinkStatus()) is global variable
            version = status.getDNSVersion()
            T.append('DNSVersion:\t\t%s'% version)
            wVersion = status.getWindowsVersion()
            T.append('WindowsVersion:\t\t%s'% wVersion)
            T.append('UnimacroDirectory:\t%s'% status.getUnimacroDirectory())
            T.append('UnimacroUserDirectory:\t%s'% status.getUnimacroUserDirectory())
            T.append('UnimacroGrammarsDirectory:\t%s'% status.getUnimacroGrammarsDirectory())
        elif self.hasCommon(words,'path'):
            T.append('the python path:')
            T.append(pprint.pformat(sys.path))
        elif self.hasCommon(words, "timer"):
            timer_info = natlinktimer.getNatlinktimerStatus()
            if timer_info is None:
                T.append('natlinktimer is not active')
            elif timer_info == 1:
                T.append('there is 1 timer active')
            else:
                T.append(f'there are {timer_info} timers active')
        elif self.hasCommon(words, "class"):
            T.append()
        else:
            T.append('no valid keyword found')

        s = '\n'.join(T)
            
        actions.Message(s)
        print(s)
        print()
        for e in extra:
            print(e)

    def gotResults_variable(self,words,fullResults):
        vartrick = self.getFromInifile(words[0], 'formatvariable', '')
        print('vartrick: %s'% vartrick)
        if vartrick:
            self.gotVariable = vartrick
        else:
            print('no vartrick found, return')
        # 
        c = self.getNumberFromSpoken(words[-1])
        
        if not c:
            print('vartrick %s wait for dgndictation'% vartrick)
            return
        keystroke('{Shift+Ctrl+Left %s}' % c)
        keystroke('{ctrl+x}')
        print('here comes the copy paste trick %s words'% c)
        unimacroutils.Wait(0.5)
        t = natlink.getClipboard()
        tList = t.split()
        print('tList: %s'% tList)
        unimacroutils.Wait(0.5)
        funcName = 'format_%s'% vartrick
        # print 'funcName: %s'% funcNameyour 
        try:
            func = getattr(self, funcName)
            # print 'func: %s'% func
        except AttributeError:
            print('no formatfunction for variable trick: %s'% vartrick)
            return

        result = func(tList)
#
        keystroke(result)
        return


    def capit(self, s):
        """ capitalise, but leave upper case characters as they are

        (the builtin capitalise makes first letter upper case and the following
         letters lowercase)
        """
        return s[0].upper() + s[1:]

    def gotResults_undo(self,words,fullResults):
        counts = self.getNumbersFromSpoken(words)
        if counts:
            count = counts[0]
        else:
            count = 1
        #print 'count: %s'% count
        for _ in range(count):
            action('<<undo>>')

    def gotResults_redo(self,words,fullResults):
        counts = self.getNumbersFromSpoken(words)
        if counts:
            count = counts[0]
        else:
            count = 1
        #print 'count: %s'% count
        for _ in range(count):
            action('<<redo>>')

    def gotResults_comment(self,words,fullResults):
        name = nameList[words[-1]]
        if name:
            ts = time.strftime("%d%m%Y", time.localtime(time.time()))
        else:
            ts = time.strftime("%d%m%y_", time.localtime(time.time()))

        progInfo = unimacroutils.getProgInfo()
        if unimacroutils.matchModule('pythonwin', progInfo=progInfo):
            com = "#" + name + ts
        elif unimacroutils.matchModule('textpad', 'html', progInfo=progInfo):
            com = "<!--" + name + ts + "-->"
        elif unimacroutils.matchModule('textpad', '.c', progInfo=progInfo):
            com = "$$$$" + name + ts + "$$$$"
        elif unimacroutils.matchModule('textpad', '.py', progInfo=progInfo):
            com = "#" + name + ts
        else:
            com = name + ts
        keystroke(com+"\n")
            
    def gotResults_modes(self,words,fullResults):
        """enable different modes

        When going to spell mode or command mode the special
        set which makes searching and dictating a single word
        or a few words possible are enabled.

        """
        mode = self.hasCommon(words, modes)
        if not mode:
            print('modes, invalid mode: %s'% words)
            return
        if mode in ['normal', 'normale']:
            M = 0
        elif mode in ['dictation', 'dicteer', 'dictate']:
            M = 1
        elif mode in ['command', 'commando']:
            M = 2
        elif mode in ['numbers', 'nummer']:
            M = 3
        elif mode in ['spell', 'spel']:
            M = 4
        else:
            print('no valid mode: %s'% mode)
            return

        self.setMode(M)

        if M > 1:
            self.DisplayMessage('<_general: setting command set>')
            self.activateSet(commandSet)
        else:
            self.DisplayMessage('<_general: setting normal set>')
            self.activateSet(normalSet)
            
        

    def gotResults_namephrase(self,words,fullResults):
        # list of words that can be combined in a double christian name
        #  eg Jan Jaap or Jan-Marie 
        # voornamenList = ['Jan', 'Jaap', 'Peter', 'Louise', 'Anne']
        modInfo = natlink.getCurrentModule()
        action("CLIPSAVE")
        keystroke("{Ctrl+c}")
        time.sleep(0.1)
        # do contents of clipboard:
        t = natlink.getClipboard().strip()
        if not t:
            modInfo = natlink.getCurrentModule()
            if unimacroutils.matchModule('natspeak', 'spell', modInfo):
                keystroke("{ExtHome}{Shift+ExtEnd}{Ctrl+x}")
                unimacroutils.Wait(0.5)
                t = natlink.getClipboard().strip()
                if not t:
                    action("CLIPRESTORE")
                    return
            else:
                if self.language == 'nld':
                    com = "selecteer dat"
                else:
                    com  = "select that"
                action("HW %s"%com)
                unimacroutils.Wait(0.5)
                keystroke("{Ctrl+c}")
                time.sleep(0.1)
                t = natlink.getClipboard().strip()
                if not t:                    
                    self.DisplayMessage("select a text first")
                    action("CLIPRESTORE")
                    return
        if self.hasCommon(words, ['naam', 'Name']):
            result = namelist.namelistUnimacro(t, ini=self.ini)
            print('result of namelistUnimacro function: %s'% result)
            r = '' # in case result is empty
            for r in result:
                print(f'adding part: {r}')
                unimacroutils.addWordIfNecessary(t)
            keystroke(r)
        else: # zonder naam in words, a normal phrase:
            print('adding phrase %s'% t)
            unimacroutils.addWordIfNecessary(t)
            keystroke(t)
        action("CLIPRESTORE")

            
    def gotResults_hyphenatephrase(self,words,fullResults):
        # selection or last utterance is spelled out with all caps and hyphens
        # Quintijn, August 15, 2009

        # save clipboard, release after the action:                                 
        action("CLIPSAVE")
        # hasCommon function for possibility of translations/synonyms without altering the code:
        if self.hasCommon(words[-1], "phrase"):
            keystroke("{Ctrl+c}")
            # do contents of clipboard:
            t = natlink.getClipboard().strip()
            if not t:
                if self.language == 'nld':
                    com = "selecteer dat"
                else:
                    com  = "select that"
                action("HW %s"%com)
                unimacroutils.Wait(0.5)
                keystroke("{Ctrl+c}")
                t = natlink.getClipboard().strip()
            if not t:                    
                self.DisplayMessage("select a text first")
                action("CLIPRESTORE")
                return
        elif self.hasCommon(words, ('word', 'words')):
            counts = self.getNumbersFromSpoken(words)
            if counts:
                count = counts[0]
            else:
                count = 1
            keystroke("{shift+ctrl+left %s}"% count)
            keystroke("{Ctrl+c}")
            t = natlink.getClipboard().strip()
            if not t:                    
                self.DisplayMessage("could not select a valid text")
                action("CLIPRESTORE")
                return
        else:
            self.DisplayMessage("unexpected last word in command phrase: %s"% words[-1])
            action("CLIPRESTORE")
            return
            

        # first paste back the selected text, and add a space if needed:
        L = []
        # for each word in utterance join uppercased characters of word with a '-'
        tWords = t.split()
        for word in tWords:
            L.append('-'.join([t.upper() for t in word]))
            L.append(' ')
        keystroke(''.join(L))
        action("CLIPRESTORE")
        # 
    def gotResults_openuser(self,words,fullResults):
        User = self.getFromInifile(words[-1], 'users')
        print('user: %s'% User)
        try:
            natlink.openUser(User)
        except natlink.UnknownName:
            print(f'cannot open user "{User}", unknown name')
            
    def gotResults(self,words,fullResults):
        if self.highlight:
            # for Shane
            asterisksSpacing = 1   # to be perfected later as option of this grammar
            if asterisksSpacing:
                if self.text.find('*'):
                    self.text = self.text.replace('*', ' * ')
            if self.text:
                action("<<startsearch>>")
                keystroke(self.text)
                action("<<searchgo>>")    
            else:
                print('no text to highlight')
            return
            #keystroke("{ctrl+f}")
            #t = self.text
            #t = t.replace(' . ', '.')
            #t = t.replace('( ', '(')
            #t = t.replace(' )', ')')
            ##print 'execute highlight with "%s"'% highlightText
            #keystroke(t)
            #keystroke("{enter}")
            #return

        if self.search:
            progInfo = unimacroutils.getProgInfo()

            # make provisions for searchwords (function (def), class (class) etc)
            if self.specialSearchWord:
                self.text = self.ini.get('searchwords', self.specialSearchWord) + self.text
            if self.count:
                count = int(self.count)
            else:
                count = 1
            if self.search == 'forward':
                # forward
                self.direc = 'down'
                self.searchOn(count, progInfo=progInfo)
                return
            if self.search == 'new':
                # new, just start the search dialog:
                self.searchMarkSpot(progInfo=progInfo)
                action('<<startsearch>>', progInfo=progInfo)
                return
            if self.search == 'back':
                # back:
                self.direc = 'up'
                self.searchOn(count, progInfo=progInfo)
                return
            if self.search ==  'go back':
            # go back, return to origin
                print("search go back")
                self.searchGoBack(progInfo=progInfo)
                return
            if self.search in ('for', 'before','after'):
                # new search with text
                self.direc = 'down'
                print('new leap to text: %s'% self.text)
                self.searchMarkSpot(progInfo=progInfo)
                res = self.searchForText(self.direc, self.text, progInfo=progInfo, beforeafter=self.search)
            elif self.search == 'extend':
                res = self.searchForText(self.direc, self.text, progInfo=progInfo, extend=1)
            elif self.search == 'insert':
                res = self.searchForText(self.direc, self.text, progInfo=progInfo, insert=1)
            else:
                print('invalid search code: %s'% self.search)
                self.DisplayMessage('search, invalid search code: %s'% self.search)
                return
            if res == -2:
            # search failed, did cancel mode
                return 
            unimacroutils.visibleWait()
            print('calling stop search')
            self.stopSearch(progInfo=progInfo)
            

    def searchOn(self, count, progInfo=None):
        """search up or down possibly more times"""
        if progInfo is None:
            progInfo = unimacroutils.getProgInfo()
        sectionList = actions.getSectionList(progInfo=progInfo)
        if self.direc == 'back':
            searchGoOn = actions.getMetaAction('searchgoback', sectionList=sectionList, progInfo=progInfo)
        else:
            searchGoOn = actions.getMetaAction('searchgoforward', sectionList=sectionList, progInfo=progInfo)
            
        for _ in range(count):
            if searchGoOn:
                res = action(searchGoOn)
            else:
                res = self.searchForText(self.direc, progInfo=progInfo)
            self.direc = self.getLastSearchDirection() # in case back search changed it!
            if res == -2:
                # search failed, did cancel mode
                return 
        unimacroutils.visibleWait()
        if not searchGoOn:
            self.stopSearch(progInfo)


    def GetGrammarModuleName(self):
        return __name__    

    def GetDictionaries(self):
        Dicts={
        }
        return Dicts

    def Message(self,t):
        tt = t + "  (command: " + self.fullText + ")"
        unimacroutils.Message(tt,self.title)
        
    def do_pressfirst(self, text):
        """first character "hard", rest normal
        """
        if text:
            action(f'SSK {text[0]}')
            if len(text) > 1:
                action('VW')
                keystroke(text[1:])

def isPythonFile(f):
    return f[-3:] == '.py'

def isHtmlFile(f):
    return f[-5:].lower() == '.html'


Classes = ('TkTopLevel')
def getIdleTitles():
    """get all titles of top windows with class name in tuple below

    This class name belongs, as far as I know, to the window explorer window

    """
    TitlesHandles = []

    ##print 'Classes:', Classes
##    Classes = None
    win32gui.EnumWindows(getIdleWindowsWithText, (TitlesHandles, Classes))
    return TitlesHandles

def getIdleWindowsWithText(hwnd, th):
    TH, classes = th
##    if wTitle.find('d:') == 0:
##        print 'class:', win32gui.GetClassName(hwnd)
    if win32gui.GetClassName(hwnd) in classes:
        wTitle = win32gui.GetWindowText(hwnd).strip().lower()
        TH.append((wTitle, hwnd))

def unload():
    #pylint:disable=W0603
    global thisGrammar
    if thisGrammar:
        thisGrammar.unload()
    thisGrammar = None
#
if __name__ == "__main__":
    # here code to interactive run this module
    thisGrammar = ThisGrammar(inifile_stem='_general')
    thisGrammar.startInifile()
    thisGrammar.initialize()
elif __name__.find('.') == -1:
    # this is caught when this module is imported by the loader (when Dragon/Natlink starts)
    thisGrammar = ThisGrammar()
    thisGrammar.initialize()


