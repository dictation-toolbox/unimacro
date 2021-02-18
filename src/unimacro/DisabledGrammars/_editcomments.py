__version__ = "$Rev: 606 $ on $Date: 2019-04-23 14:30:57 +0200 (di, 23 apr 2019) $ by $Author: quintijn $"
# This file is part of a SourceForge project called "unimacro" see
# http://unimacro.SourceForge.net and http://qh.antenna.nl/unimacro
# (c) copyright 2003 see http://qh.antenna.nl/unimacro/aboutunimacro.html
#    or the file COPYRIGHT.txt in the natlink\natlink directory 
#
# This module was written by: Quintijn Hoogenboom (QH softwaretraining & advies)
# (August 2002, extensively revised October 2003)
# adaptations for interaction with emacs/voicecode march 2007
# adapatations for latex, Frank Olaf Sem-Jacobsen (2011)
#
"""copy text to DragonPad for editing with Select-and-Say

With this grammar you can copy text from an arbitrary window into
DragonPad (or other Select-and-Say program), edit with full
Select-and-Say capabilities, and paste it back into the original place.

An important part of this grammar is the possibility to "Edit Comment"
and, new feature, doc strings. With "Edit Comment" the prefixing spaces
and "#" are stripped from the text. With "Edit Ready" the things are
put in front again.

As a side effect edited texts are logged into a file, for future use in
the vocabulary builder.
  
"""
class EditError(Exception): pass

import natlink
natqh = __import__('natlinkutilsqh')
natut = __import__('natlinkutils')
natbj = __import__('natlinkutilsbj')
import utilsqh
import win32gui
import time
import re
import os
from actions import doAction as action
from actions import doKeystroke as keystroke
import actions
import ctypes


normalset = ['edit', 'copy', 'log']
editset = ['ready', 'copy', 'log', 'edit']

# window handle edit program:
nsHandle = 0
sourceHandle = 0

# regular expressions for edit comment and edit docstring
PythonCommentLine = re.compile(' *# ')
EmptyLines = re.compile(' *$')
StartingSpaces = re.compile(r'( *)')
# obsolete:
winwordStartComment = re.compile(" *'")
winwordEmptyCommentLines = re.compile("^ *' *$", re.M)



ancestor = natbj.IniGrammar
class EditGrammar(ancestor):
    language = natqh.getLanguage()        
    name = 'edit'
    gramSpec = """
<log> exported = log (all|that|messages);
<copy> exported = (copy|cut) (all|that|messages) to (NatSpeak|DragonPad);
<edit> exported = edit (all|that|comment|file|"doc string"|remark) [(('python'|'cc') 'code') | 'latex'];
<ready> exported = edit (ready|cancel);
    """

    def initialize(self):
        self.load(self.gramSpec)
        self.defineLogfiles()
        self.activateSet(normalset)
        self.switchOnOrOff()
        self.comment = 0
        self.remark = 0
        self.startString = ''
        self.emacsWait= 0
        self.emacsHndle = 0
        self.word_handle = 0

    def defineLogfiles(self):
        """folder for logging texts and folder for messages"""

        umFolder = natqh.getUnimacroUserDirectory()
        self.messagesFolder = os.path.join(umFolder, 'log messages')
        self.logFolder = os.path.join(umFolder, 'log %s'%self.language, natqh.getUser())


    def gotBegin(self,moduleInfo):
        if self.checkForChanges:
            self.checkInifile()

    def gotResultsInit(self,words,fullResults):
        """This is a new docstring"""
        self.fullText = ' '.join(words)

    def gotResults_edit(self,words,fullResults):
        global sourceHandle
        print('---------------------edit: %s'% words)
        modInfo = natlink.getCurrentModule()
        progInfo = natqh.getProgInfo()
        if progInfo[0] == self.startProgram.lower() or \
            self.startProgram == 'DragonPad' and progInfo[1].find('dragonpad') == 0:
            self.DisplayMessage('Do not use "%s" in %s'% (self.fullText, self.startProgram))
            return
        sourceHandle = modInfo[2]
        ##  If "edit all" is said, first select whole document
        # mark cursor if possible:
        fileMode = self.hasCommon(words, "file")
        if fileMode:
            toProg = 'emacs'
            self.changeFileToProg(sourceHandle, toProg)
            return
        natqh.clearClipboard()
        action('<<copy>>')
        t = natqh.getClipboard()

        if self.hasCommon(words, ['all']):
            action('<<selectall>>')            

        self.progName = natqh.getProgName()
        self.comment = self.hasCommon(words,['comment','doc string'])
        self.remark = self.hasCommon(words,['remark']) # for excel, not well implemented
        self.emacs = self.hasCommon(words, ['code'])
        self.latex = self.hasCommon (words, ['latex'])
        
        if not self.remark:
            natqh.clearClipboard()
            action('<<copy>>')
            inputText = natqh.getClipboard()
            if inputText.endswith('\n') and not self.emacs:
                self.endsWithNewline = 1
                inputText = inputText[:-1]
            else:
                self.endsWithNewline = 0

        if self.comment:
            print('self.comment: %s'% self.comment)
            if self.comment in ['doc string']:
                try:
                    exec("com2text = self."+self.progName+"Docstring2text")
                except AttributeError:
                    self.DisplayMessage('command '+self.fullText+' not valid for program: %s'%self.progName)
                    self.comment = 0
                    return 
            else:
                try:
                    exec("com2text = self."+self.progName+"Com2text")
                except AttributeError:
                    self.DisplayMessage('command '+self.fullText+' not valid for program: %s'%self.progName)
                    self.comment = 0
                    return

        # goto the other program:
        if self.emacs:
            self.python = self.hasCommon(words, 'python')
            self.cc = self.hasCommon(words, 'cc')
            if self.python:
                self.emacsFile = r'C:/emacspythoncode.py'
            elif self.cc:
                self.emacsFile = r'C:/emacsCCcode.c'
            else:
                raise EditError('%s: invalid program code in command: %s'% (self.name, words))
            print('wanting to start emacs')         
            self.targetProg = "emacs"
            if self.startEditProgram(prog=self.targetProg):
                print('found emacs, fill in with file: %s'% self.emacsFile)
                self.fillAndFindEmacsFile(inputText)
                self.activateSet(editset)
            else:
                print('error with "edit that code command: %s"'% words)
                return
	elif self.latex:
	    
	    dll = ctypes.windll.shell32
	    buf = ctypes.create_unicode_buffer(300)
	    dll.SHGetSpecialFolderPathW(None, buf, 0x0005, False)
	    print(buf.value)

            self.wordFile = buf.value + r'\wordlatextemp.tex'
            print('wanting to start WinWord')         
            self.targetProg = "winword"
            if self.startEditProgram(prog=self.targetProg):
                print('found WinWord, fill in with file: %s'% self.wordFile)
                self.fillAndFindWordFile(inputText)
                self.activateSet(editset)
            else:
                print('error with "edit that code command: %s"'% words)
                return
        else:
            self.targetProg = None
            if self.startEditProgram():
                action('<<selectall>>;')
            else:
                print('%s: problem with finding targetProg: %s'% (self.name, self.targetProg))
                return
            if inputText:
                natut.playString(inputText)
        self.activateSet(editset)

    def gotResults_copy(self,words,fullResults):
        global sourceHandle, nsHandle
        modInfo = natlink.getCurrentModule()
        if natut.matchWindow(modInfo, self.startProgram, self.startProgram):
            self.DisplayMessage('Do not use "'+self.fullText+'" in '+self.startProgram)
            return 
        # get Handle of this window:
        sourceHandle = modInfo[2]
        
        ##  If "edit all" is said, first select whole document
        if (self.hasCommon(words, ['all'])):
            action('<<selectall>>')
            natqh.Wait(0.2)
        if (self.hasCommon(words, ['messages'])):
            natqh.switchToWindowWithTitle('messages from python macros')
            action('<<selectall>>')
            natqh.Wait(0.2)
        # copy and goto NatSpeak
        #  clear clipboard, copy and goto DragonPad
        natqh.saveClipboard()
        if (self.hasCommon(words, ['copy'])):
            action('<<copy>>')
        elif (self.hasCommon(words, ['cut'])):
            action('<<cut>>')
        else:
            print('no copy or cut in words: %s'% words)
            return
        natqh.rememberWindow()
        if self.startEditProgram():
            if natqh.getClipboard():
                    keystroke('{Ctrl+ExtEnd}{Enter}{Ctrl+v}')
            natqh.returnToWindow(20,0.2, winHandle=sourceHandle)
        natqh.restoreClipboard()
        
    def changeFileToProg(self,fromHndle, toProg):
        """try getting file and folder in pythonwin <CURSOR> and emacs"""
        actions.putCursor()
        action("<<filesave>>")
        fileName =actions.getPathOfOpenFile()
        if fileName:
            print('fileName: %s'% fileName)
        else:
            print('no filename found')
            return
        print("closing and return to: %s"% fileName)
        action("<<documentclose>>")
        if not self.startEditProgram(prog=toProg):
            print('did not find emacs')
            return

        action("<<fileopen>>")
        action("W")
        keystroke(fileName)
        keystroke("{enter}")
        actions.findCursor()

    # This is for the purpose of logging the text to a
    # file, which can
    # be used by the vocabulary builder later on.
    def gotResults_log(self,words,fullResults):
        natqh.saveClipboard()
        if ( words[1] in ['all']):
            #print "select all"
            action('<<selectall>>')
            natqh.Wait(0.2)
            
        if (self.hasCommon(words, ['messages'])):
            natqh.switchToWindowWithTitle('Messages')
            natqh.Wait(0.5)
            action('<<selectall>>')
            action('<<copy>>')
            yearMonthDay = time.localtime(time.time())[:3]
            messagesLogbase = 'Messages %s %s %s'% yearMonthDay
            name = logToFileNow(self.messagesFolder, messagesLogbase, append=0)
            if name:
                natqh.Wait(1)
                action("{alt+f4}")
                self.DisplayMessage('Messages logged to %s'% name)
            else:
                self.DisplayMessage('error logging')
            natqh.restoreClipboard()
            return
##            action("{alt+f4}")   
        # copy and goto NatSpeak
        action('<<copy>>')
        intros = dict(nld='teksten ', enx='texts ')
        fileIntro = intros.get(self.language, 'texts ')

        yearMonth = time.localtime(time.time())[:2]
        logFile = fileIntro +  (" %s %s"%yearMonth) + '.txt'
        name = logToFileNow(self.logFolder, logFile)
        if name:
            self.DisplayMessage('logged (append) to %s'% name)
        else:
            self.DisplayMessage('could not do logging')
    
        natqh.restoreClipboard()

    def gotResults_ready(self,words,fullResults):
        modInfo = natlink.getCurrentModule()
        checkHandle = modInfo[2]
        if self.hasCommon(words,['cancel']):
            if self.targetProg == 'emacs':
                self.killEmacsFile()

            if checkHandle == nsHandle:
                keystroke('{Ctrl+z}')
            natqh.returnToWindow(20,0.2, winHandle=sourceHandle)

        else:        # klaar:
            if checkHandle != nsHandle and self.targetProg != 'winword' and self.targetProg != 'emacs':                
                self.DisplayMessage('command "%s" cannot be done from this window, only from "%s"'%(self.fullText, self.startProgram))
            else:
                natqh.clearClipboard()
                if self.targetProg == "emacs":
                    keystroke('{alt+x}mark-whole-buffer{enter}')
                    natqh.Wait()
                    keystroke('{alt+x}clipboard-kill-region{enter}')
                    natqh.Wait()
                    self.killEmacsFile()
                else:
                    keystroke('{Ctrl+a}{Ctrl+c}')
		if self.targetProg == "winword":
		    action ('<<filesave>>')
		    natqh.Wait()
                    if natqh.waitForWindowTitle ('microsoft word') == 1:
                        progInfo = natqh.getProgInfo()
                        if progInfo[2] == 'child':
        		    keystroke('{enter}')
		    natqh.Wait()
		    action ('<<documentclose>>')
                t = natqh.getClipboard()
                if self.automaticLogToFile:
                    intros = dict(nld='teksten auto ', enx='texts auto ')
                    fileIntro = intros.get(self.language, 'texts ')
                    yearMonth = time.localtime(time.time())[:2]

                    logFile = fileIntro +  (" %s %s"%yearMonth) + '.txt'
                    name = logToFileNow(self.logFolder, logFile)
                    ##                natqh.killWindow()
                natqh.returnToWindow(20,0.2, winHandle=sourceHandle)
                if self.comment:
                    if self.comment in ['doc string']:
                        try:
                            exec("text2com = self."+self.progName+"Text2docstring")
                        except AttributeError:
                            self.DisplayMessage('command '+self.fullText+' for a comment is not valid for this program: %s'% self.progName)
                            self.comment = 0
                            return None
                    else:
                        try:
                            exec("text2com = self."+self.progName+"Text2com")
                        except AttributeError:
                            self.DisplayMessage('command '+self.fullText+' for a comment is not valid for this program: %s'% self.progName)
                            self.comment = 0
                            return None
                    
                    t = text2com(t)
                    keystroke(t)
                elif self.remark:
                    # assume excel
                    action('{shift+f10}')
                else:
                    # default action:
                    action('<<paste>>')

                if self.endsWithNewline:
                    keystroke('\n')
        self.activateSet(normalset)

    def killEmacsFile(self):
        """do the emacs commands to kill the file/buffer self.emacsPythonFile

        """
        self.emacsCommand('save-buffer')
        self.emacsCommand('kill-this-buffer')
        
    def fillAndFindEmacsFile(self, text):
        """get the file/buffer self.emacsPythonFile in the front
        
        """
        open(self.emacsFile, 'w').write(text)
        
        self.emacsCommand('find-file')
        natqh.Wait()
        keystroke('{backspace 100}')
        natqh.Wait()
        keystroke(self.emacsFile)
        natqh.Wait()
        keystroke('{enter}')
        self.emacsCommand('delete-other-windows')
        
    def fillAndFindWordFile(self, text):
        """get the file/buffer self.emacsPythonFile in the front
        
        """
        open(self.wordFile, 'w').write(text)
	natqh.waitForWindowTitle ('Microsoft Word')
	print("found Microsoft Word")
        while 1:
            action('<<fileopen>>')
            if natqh.waitForWindowTitle ('Open') == 1:
                print("got window title open")
                progInfo = natqh.getProgInfo()
                if progInfo[2] == 'child':
                    break
                else:
                    print("not a child")

	print("open file")
        natqh.Wait()
        keystroke(self.wordFile)
        natqh.Wait()
        keystroke('{enter}')
        natqh.Wait()
	if natqh.waitForWindowTitle ('File conversion'):
            keystroke('{alt+w}')
            natqh.Wait()
	    keystroke ('{enter}')
	keystroke('{ctrl+alt+n}') #Switch Word to draft mode


    def emacsCommand(self, cmd):
        """the alt+x commands, can be slowed down"""
        keystroke('{alt+x}')
        keystroke(cmd)
        if self.emacsWait:
            natqh.Wait(self.emacsWait)
        keystroke('{enter}')
        if self.emacsWait:
            natqh.Wait(self.emacsWait)
        


    def startEditProgram(self, prog=None):
        global nsHandle
        prog = prog or "dragonpad"
        hndle = actions.UnimacroBringUp(prog)
        if not hndle: return   # wrong
        if prog == 'emacs':
            self.emacsHndle = hndle
            return hndle
	elif prog == 'winword':
	    self.word_handle =hndle
	    return hndle
        else:
            nsHandle = hndle
            return hndle
##        
##        natqh.rememberWindow()
##        print ' starting: %s'% prog
##        if prog == 'emacs':
##            finish = 'emacs'
##            
##            if self.emacsHndle:
##                try:
##                    natqh.SetForegroundWindow(self.emacsHndle)
##                except:
##                    self.emacsHndle = None
##            if not self.emacsHndle:
##                natbj.AppSwapWith("emacs")
##        elif prog:
##            finish = prog
##            natlink.recognitionMimic(["start", prog])
##        else:
##            finish = None
####            natlink.recognitionMimic(["start", self.startProgram])
##        print 'waiting for new window...'
##        try:
##            natqh.waitForNewWindow(100,0.1)   # 3 seconds to start or switch
##        except natqh.NatlinkCommandTimeOut:
##            self.DisplayMessage('cannot switch to edit program: "%s"'% (prog or self.startProgram))
##            nsHandle = 0
##            return 0
##        newMod = natlink.getCurrentModule()
##        nsHandle = newMod[2]
##        if finish:
##            newProg = natqh.matchModule('emacs', modInfo=newMod)
##            if finish == newProg:
##                print 'emacs found ok'
##                self.emacsHndle = newMod[2]
##                action('SSK {alt+tab}')
##                action('SSK {alt+tab}')
##            else:
##                print 'emacs NOT found'
##                return 0
##            
##        return 1

    def fillInstanceVariables(self, ini=None):
        """fills instance variables with data from inifile

        overload for grammar lines: get activate/deactivate windows

        """
##        print 'fillInstantVariables for %s'% self
        ini = ini or self.ini
        #  If next variable is set to 1, after each "Edit Ready" command to
        #    complete text is written to a log file.
        #
        #  You can always log the active selection or the whole window text

        self.automaticLogToFile = ini.getInt('general', 'automatic log to file')
        #  Set the directory you wish here.
        ##startProgram = 'DragonPad'
        self.startProgram = ini.get('general', 'start program', 'dragonpad')
        # line length for automatic splitting
        self.linelen = ini.getInt('general', 'line length')



    def fillDefaultInifile(self, ini=None):
        """initialize as a starting example the ini file

        """
        ini = ini or self.ini
        ancestor.fillDefaultInifile(self, ini)
        self.ini.set('general', 'automatic log to file', '1')
        self.ini.set('general', 'line length', '70')
        self.ini.set('general', 'start program', 'DragonPad')
        
################################################################
#  expressions for manipulating comment conversion functions:
#
#  for Python these two functions:

#  This function converts a comment into text (stripped off the
#    leading comment character)
    def pythonwinCom2text(self, t):
        # t is the input text, to be stripped from "#"s
        #
        # look for starting spaces and '#' and spaces:
        m = PythonCommentLine.match(t)
        if m:
            self.prefix = m.group(0)
            # get list of paragraphs, with generator function,
            # regular expression for recognising comment lines given
            L = [par for par in stripPrefix(t, self.prefix)]
            return '\n'.join(L)
                
        elif not t: # starting with empty comment
            natqh.saveClipboard()
            action('<<selectline>>{ctrl+c}')
            t = natqh.getClipboard()
            natqh.restoreClipboard()
            p = len(t) - len(t.lstrip())
            self.prefix = ' '*p + "# "
            if t.find(self.prefix) == 0:
                return t[len(self.prefix):]
            else:
                return t
        else:
            raise utilsqh.QHerror('not a valid python comment, try again')
        

#
    def pythonwinText2com(self, tIn):
        """Format text back into chunks of python comment"""
        # split into real paragraphs:
        tList = tIn.split('\n')
        tOut = []
        for t in tList:
            if t:
                lenSpaces = len(t) - len(t.lstrip())
                prefix = self.prefix + ' '*lenSpaces
                localLineLen = self.linelen - len(prefix)
                # format the string into parts that are less than maxLen
                tOut.extend(utilsqh.splitLongString(t, maxLen=localLineLen, 
                                                    prefix=prefix))
            else:
                tOut.append(self.prefix.rstrip())
        
        tOut = list(pythonwinList(tOut))
        if tOut:
            return '\n'.join(tOut)
        else:
            return self.prefix.rstrip()


    def pythonwinDocstring2text(self, t):
        # t is the input text
        m = StartingSpaces.match(t)
        if m:
            self.prefix = m.group(0)
            # get list of paragraphs, with generator function,
            # regular expression for recognising comment lines given
            L = [par for par in stripPrefix(t, self.prefix)]
            return '\n'.join(L)
                
        elif not t: # startin with current line
            natqh.saveClipboard()
            action('<<selectline>>{ctrl+c}')
            t = natqh.getClipboard()
            natqh.restoreClipboard()
            if not t:
                self.prefix = ''
                return ''
            
            p = len(t) - len(t.lstrip())
            self.prefix = ' '*p
            if t.find(self.prefix) == 0:
                return t[len(self.prefix):]
            else:
                return t
        else:
            self.prefix = ''
            return t
        

#
    def pythonwinText2docstring(self, tIn):
        """Format text back into chunks of python


        """
        # split into real paragraphs: and going on
        tList = tIn.split('\n')
        tOut = []

        for t in tList:
            if t:
                lenSpaces = len(t) - len(t.lstrip())
                prefix = self.prefix + ' '*lenSpaces
                localLineLen = self.linelen - len(prefix)
                # format the string into parts that are less than maxLen
                tOut.extend(utilsqh.splitLongString(t, maxLen=localLineLen, 
                                                    prefix=prefix))
            else:
                tOut.append(prefix.rstrip())
        
        tOut = list(pythonwinList(tOut))
        if tOut:
             return '\n'.join(tOut)
        else:
            return self.prefix

def stripPrefix(Text, prefix):
    """generator function, strips the given prefix

    if not there, yield an empty line,
    with another line, raises error

    """
    L = Text.split('\n')
    if not L:
        yield ''
        return
    for t in L:
        if not prefix:
            yield t
        elif t.find(prefix) == 0:
            yield t[len(prefix):].rstrip()
        elif t.find(prefix.rstrip()) == 0:
            yield t[len(prefix.rstrip()):].rstrip()
        elif EmptyLines.match(t):
            yield ''
        else:
            raise EditError('stripPrefix: not a prefix: %s' % t)

def pythonwinList(L):
    """left strips lines that are indented by pythonwin

    assuming after # ldldsldsl the next line is indented,
    after an empty line, the indenting is thrown away.

    Thus when pythonwin indents a line from itself, the string
    must be stripped on the left side.
    
    """
    stripLeft = 0
    for l in L:
        if stripLeft:
            yield(l.lstrip())
        else:
            yield l
        # if we have a non empty line, the following must be stripped,
        # because pythonwin indents the line by itself.
        stripLeft = (l.strip() != '')


def logToFileNow(folderName, fileNameBase, append=1):
    print('start log to file now: folderName: %s, fileNameBase: %s, append: %s'% \
          (folderName, fileNameBase, append))
    t = natqh.getClipboard()
    if t:
        utilsqh.createFolderIfNotExistent(folderName)
        try:
            if append:
                base, ext = os.path.split(fileNameBase)
                ext = ext or '.txt'
                name = os.path.join(folderName, base+ext)
##                print 'open for append: %s'% name
                fout = open(name, 'a')
            else:
                name = findNewFile(folderName, fileNameBase)
                if name:
                    fout = open(name, 'w')
                else:
                    print('cannot find valid logfile')
                    return

            fout.write(t)
            fout.write('\n\n')
            fout.close()
            return name
        except IOError:
            print('Grammar _editcomments: cannot log to file: %s:::%s'% (folderName, fileName))
    else:
        print('nothing to log')

def findNewFile(folderName, baseName,digits=2):
    """find an unexisting file

    """
    base, ext = os.path.splitext(baseName)
    ext = ext or '.txt'
    
    maxNumber = 10**digits
    formatString = '%%s - %%.%sd%%s'% digits
##    print 'formatString: %s'% formatString
    for i in range(1, maxNumber):
        filePart = formatString % (base, i, ext)
        fullName = os.path.join(folderName, filePart)
        if not os.path.isfile(fullName):
            return fullName

                          


    
# standard stuff Joel (adapted for possible empty gramSpec, QH, unimacro)
thisGrammar = EditGrammar()
if thisGrammar.gramSpec:
    thisGrammar.initialize()
else:
    thisGrammar = None

def unload():
    global thisGrammar
    if thisGrammar:
        thisGrammar.unload()
    thisGrammar = None



# ###### Visual Basic script for syntax highlighting of latex in Word
#Sub AssociateStyle(pattern As String, style As String, colour As Long)
#'Associate Styles with headings and quotations
#'Ensure Tools/References/Microsoft VBscript Regular Expression 5.5 is on
#  
#Dim regEx, Match
#'Dim Matches As MatchCollection
#Dim str As String
#Dim region As Range
#
#Set regEx = CreateObject("VBScript.RegExp")
#regEx.pattern = pattern           ' Set pattern.
#regEx.Global = True
#regEx.MultiLine = True
#
#'obtain matched RegExp.
#Set Matches = regEx.Execute(ActiveDocument.Range.Text)
#'MsgBox (Len(ActiveDocument.Range.Text))
#'MsgBox (Matches.Count)
#'loop through and replace style
#For Each Match In Matches
#    Set region = ActiveDocument.Range(Match.FirstIndex, Match.FirstIndex + Len(Match.Value))
#    If colour > -1 Then
#   '     MsgBox (Match.Value)
#    '    MsgBox (Match.FirstIndex)
#     '   MsgBox (Len(Match.Value))
#        region.Font.ColorIndex = colour
#    Else
#        region.style = _
#        ActiveDocument.Styles(style)
#    End If
#Next
# 
#End Sub
#
# 
#Sub AutoOpen()
#'
#' AutoOpen Macro
#' Macro recorded 5/6/2009 by reagle
#'
#FileName = ActiveDocument.FullName
#Extension = Right(FileName, 3)
#If Extension = "tex" Then
#        Selection.WholeStory
#        Selection.Font.Name = "Georgia"
#        Selection.Font.Size = 12
#        Selection.ParagraphFormat.LineSpacing = 16
#        Selection.style = "Body Text"
#        'Call ReplaceMarkup("\\emph\{(*)\}", "<<\1>>")
#        Call AssociateStyle("[{}]", "Quote", wdGreen)
#        Call AssociateStyle("\\.*?}", "Quote", wdDarkBlue)
#        Call AssociateStyle("^\\title{", "Heading 1", -1)
#        Call AssociateStyle("^\\chapter{", "Heading 1", -1)
#        Call AssociateStyle("^\\section{", "Heading 1", -1)
#        Call AssociateStyle("^\\subsection{", "Heading 2", -1)
#        Call AssociateStyle("^\\subsubsection{", "Heading 3", -1)
#        Call AssociateStyle("^\\begin{quotation}", "Quote", -1)
#        Call AssociateStyle("\$.*?\$", "Quote", wdRed)
#        Call AssociateStyle("[^\\]%.*?$", "Quote", wdGray25)
#        
#End If
#
#End Sub
