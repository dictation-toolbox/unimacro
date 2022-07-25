#
# frescobaldi.py
#
# Written by: Quintijn Hoogenboom (QH softwaretraining &
# advies),2002, revised October 2003
# march 2011: change sol to frescobaldi
"""grammar rules for frescobaldi (lilypond) music typesetting

The note input utterances, which are the most important, can contain
complete or incomplete notes and other parts (eg bar).

The cursor can be at several places, which is primary examined by getNextPrev, which
results in several instance variables.

- if text is selected:
-- the selection is replaced by the new input

- if the cursor is surrounded by whitespace (space of newline):
-- a complete note + what follows is entered new
-- an incomplete note is added to the previous note (eg a rythm or a height octave up/down correction)
-- other string parts are entered as new

- if the cursor is at the start of a note:
-- a complete or incomplete note changes the next note, and inserts what follows in the utterance
-- other string parts are inserted before the cursor

- if the cursor is just after a string,
-- to be filled in

- if the command says insert, a whitespace on both sides of the cursor or selection is ensured

The relevant information from the frescobaldi input window is retrieved by routines in
actionclasses/frescobaldi-actions.py.
The most important routines are:
- hasSelection, retrieving the selected text or returning None
- getPrevNext, retrieving 1 character on both sides of the cursor
- getNextLines(n=1): return n lines after the cursor
- getPrevLines(n=1): return n lines before the cursor

If just input notes are given, the strategy of insert/update of notes is
- cursor not just before another note or character (|):
  - if note is complete: insert
  - if note is partial (eg additional rythm or addition): update previous note
  
- cursor just before a note (or other character):
  - update the following note
  
"""

from dtactions.unimacro import unimacroutils
import unimacro.natlinkutilsbj as natbj
from natlinkcore import natlinkutils
from dtactions.unimacro import unimacroutils
import unimacro.natlinkutilsbj as natbj
import natlink
from dtactions.unimacro.unimacroactions import doAction as action
from dtactions.unimacro.unimacroactions import doAction as action
from itertools import cycle
from dtactions.unimacro import unimacroactions as actions
import re
import copy
import time
from lynote import LyNote, analyseString, getNotesFromWordsList, join

reRythmAttr =  re.compile(r"([132468.-]+)(.*)")


ancestor = natbj.DocstringGrammar
class ThisGrammar(ancestor):
    name = 'frescobaldi'

    def initialize(self):
        global language
        if self.load(self.gramSpec):
            print 'grammar frescobaldi (%s) active'% self.name
            self.prevHandle = -1
        else:
            language = ""
        self.frescobaldi = None
        self.rythmicPattern, self.rythmicKeys = None, None
                        
    def gotBegin(self, moduleInfo):
        winHandle = moduleInfo[2]
        if self.prevHandle == winHandle: return
        self.prevHandle = winHandle
        if moduleInfo[0].lower().find('frescobaldi.exe') > 0 and unimacroutils.isTopWindow(moduleInfo[2]):
            if self.frescobaldi is None:
                progInfo = unimacroutils.getProgInfo(moduleInfo)
                self.frescobaldi = actions.get_instance_from_progInfo(progInfo)
                if not self.frescobaldi:
                    raise Exception("frescobaldi, cannot get frescobaldi actions module")
                
            if self.checkForChanges:
                #print 'grammar frescobaldi (%s) checking the inifile'% self.name
                self.checkInifile()
            self.switchOnOrOff()
        elif self.isActive():
            self.deactivateAll()


    def gotResultsInit(self,words,fullResults):
        """initialize values
        """
        self.note = ""
        self.rythm = ""
        self.point = "" # for rythms, halving a note or rest
        self.noteaddition = "" # up, down, slur
        self.separator = "" # bar
        self.pitch = "" # up or down octave(s)
        self.wordsList, self.notesIndexes = [], [] # for notesnavigate
        self.afterNotesList = [] # list items after the selected notes
        self.notesWanted = 0 # also for notesnavigate...
        self.newNotes = []
        self.hadFigure = 0
        self.nextchars = None
        self.prevchars = None
        self.justInsert = 1
        t0 = time.time()
        self.hasSelection = self.frescobaldi.hasSelection()
        t1 = time.time()
        print 'hasSelection, (%.4f seconds): %s'% (t1-t0, self.hasSelection)
        self.justLeft = self.justRight = None # to be filled with getPrevNext()
        self.inMiddleOfWord = None
        if self.hasSelection:
            print 'hasSelection, selected text: %s'% unimacroutils.getClipboard()
        self.hasAllInfoNext = False ## set to true if nextlines end with double \n
        self.hasAllInfoPrev = False ## set to true if prevlines contains a double \n so starts with ir
        
    def rule_testgetprevnext(self, words):
        "get previous next"
        ## test just notes around the cursor:
        if self.hasSelection:
            print "selection: %s"% self.hasSelection
        else:
            t0 = time.time()
            self.getPrevNext()
            t1 = time.time()
            print '----testgetprevnext, time: %.4f'% (t1-t0,)
            print 'justLeft: %s (%s), justRight: %s (%s)'% (repr(self.justLeft), len(self.justLeft), repr(self.justRight), len(self.justRight))
            print 'inMiddleOfWord: %s'% self.inMiddleOfWord
            print 'hasWhiteSpaceAround: %s, atEndOfLine: %s'% (self.hasWhiteSpaceAround, self.atEndOfLine)
            print 'hasWhiteSpaceBefore: %s, hasWhiteSpaceAfter: %s'% (self.hasWhiteSpaceBefore, self.hasWhiteSpaceAfter)
            print '----'
            
    def rule_testgetnotes(self, words):
        """get (next|previous) (note | ({n2-10} notes))"""
        n = self.getNumberFromSpoken(words[-2]) or 1

        if self.hasCommon(words, 'next'):
            wordsList, notesIndexes, beforeString, afterString, afterNoteComplete = self.getNextNotes(n)
            print '--- next %s notes:'% n
            print 'before: %s, after: %s, notesfound: %s'% (repr(beforeString), repr(afterString), len(notesIndexes))
            print 'wordsList: %s'% wordsList
            print 'notesIndexes: %s'% notesIndexes
            print 'notes: %s'% repr([str(wordsList[i]) for i in notesIndexes])
        elif self.hasCommon(words, 'previous'):
            wordsList, notesIndexes, beforeString, afterString, beforeNoteComplete= self.getPrevNotes(n)
            print '--- previous %s notes:'% n
            print 'before: %s, after: %s, notesfound: %s'% (repr(beforeString), repr(afterString), len(notesIndexes))
            print 'wordsList: %s'% wordsList
            print 'notesIndexes: %s'% notesIndexes
            print 'notes: %s'% repr([str(wordsList[i]) for i in notesIndexes])
        else:
            print 'wrong word in grammar rule, not next or previous found: %s'% words
            
        
    def rule_sequence(self, words):
        "(<note>|<pitch>|<rythm>|<separator>|<noteaddition>)+"
        pass
    
    def subrule_note(self, words):
        "{notes} [{notesalteration}]"
        for w in words:
            note = self.getFromInifile(w, 'notes')
            if note:
                if self.note:
                    self.finishNote()
                self.note = note
                continue
            altnote = self.getFromInifile(w, 'notesalteration')
            if altnote:
                if not self.note:
                    raise ValueError("should have note before making a notesalteration: %s (%s)"% (altnote, w))
                self.note = self.noteAlteration(self.note, altnote)
    
    def noteAlteration(self, note, alteration):
        """make a note sharp or flat
        
        way to do depends on the inputlanguage of lilypond
        """
        return note + alteration

    def subrule_pitch(self, words):
        "{pitchs}"
        for w in words:
            pitch = self.getFromInifile(w, 'pitchs')
            if pitch:
                self.pitch += pitch
                continue                                

    def subrule_noteaddition(self, words):
        "{noteadditions}"
        for w in words:
            self.noteaddition = self.getFromInifile(w, 'noteadditions')
        
    def subrule_rythm(self, words):
        "{rythms}|{rythms} point"
        # switch off rythmicPattern as soon as a rythm is called:
        # if rythm contains a space, it is converted into a rythmicPattern        
        self.rythmicPattern = None
        for w in words:
            if self.hasCommon(w, "point"):
                self.point += "."
            else:
                rythm = self.getFromInifile(w, 'rythms')
                if self.rythm and self.note:
                    self.finishNote()
                if rythm.find(' ') > 0:

                    self.rythmicPattern = cycle(self.analyseRythmicPattern(rythm))
                    print('self.rythmicPattern: %s'% self.rythmicPattern)
                else:
                    self.rythm = rythm

    def analyseRythmicPattern(self, rythm):
        """analyse rythmic pattern
        
        it consists of rythms, separated by spaces.
        a rythm can be augmented with noteadditions, like beams ([]) or slurs ()
        '-' as key is no new rythmic value
        
        return a list of 2-tuples [(rythm, attr), (rythm, attr)]
        rythm '8.( 16) 8' returns [('8.', '('), ('16',')', ('8', '')]
        """
        if not ' ' in rythm:
            raise ValueError('analyseRythmicPattern, no space found in pattern: %s'% rythm)
        rythms = [r.strip() for r in rythm.split()]
        print("rythm: %s, rythms: %s"% (rythm, rythms))
        L = []
        for r in rythms:
            print('rythmic part: %s'% r)
            m = reRythmAttr.match(r)
            if m:
                L.append(m.groups())
            else:
                raise ValueError("invalid rythm in part %s of rythmic pattern: %s"% (r, rythm))
        
        print("rythmic L: %s"% L)
        return L

    def subrule_separator(self, words):
        "{separators}"
        self.finishNote()
        s = []
        for w in words:
            separator = self.getFromInifile(w, 'separators')
            self.newNotes.append(separator)
            
    def rule_figure(self, words):
        """here figure {figures}+"""
        # start with the pointer in the music pane
        # always click
        unimacroutils.buttonClick()
        unimacroutils.visibleWait()
        self.hadFigure = 1

        selection = self.getFigurePart()
        if not selection:
            print 'rule_figure, no selection found, stop macro'
            return
        
        # print 'figurepart: %s'% selection
        L = []
        previous = None
        for w in words:
            figure = self.getFromInifile(w, 'figures')
            # print 'figure: %s, result: %s'% (w, figure)
            if figure:
                if previous and self.isFigure(previous) and not self.isFigure(figure):
                    if figure.startswith("_"):
                        figure = figure.lstrip("_")
                    L[-1] = L[-1] + figure
                else:
                    L.append(figure)
                previous = figure
        self.keystroke("<" + ' '.join(L) + ">")  # allow for { , not being a control character!
        
    def isFigure(self, figure):
        """return True if figure is a cipher, 1, 2, ...
        """
        try:
            int(figure)
        except ValueError:
            return False
        return True
            
    def rule_notesaddition(self, words):
        "<notesnavigate>{notesaddition}"
        # if words end with Off, On or End, they are in front of the first word and separated from the last.
        self.justInsert = False
        if not self.notesIndexes:
            print 'notesaddition, no notes found in selection'
            return
        
        prepost = self.getFromInifile(words[-1], 'notesaddition')
        print 'prepost: "%s"'% prepost
        doEachNote = False
        # to be switched on with eg ()() (eachnoteslur)
        if not prepost:
            return
        if ":" in prepost:
            pre, post = prepost.split(":")
        else:
            lenpart = len(prepost)/2
            pre, post = prepost[:lenpart], prepost[-lenpart:]
        if pre == post and len(pre) > 1:
            lenpart = len(pre)/2
            pre, post = pre[:lenpart], post[-lenpart:]
            print 'pre: %s, post: %s, do continuous'% (pre, post)
            doEachNote = True
        startNote = self.wordsList[self.notesIndexes[0]]
        print 'notesIndexes: %s, notesWanted: %s'% (self.notesIndexes, self.notesWanted)
        endNote = self.wordsList[self.notesIndexes[self.notesWanted-1]]
        
        startNote.updateNote(pre)
        endNote.updateNote(post)
        if doEachNote and self.notesWanted > 2:
            for i in range(1, self.notesWanted-1):
                print 'do extra for note %s'%i
                note = self.wordsList[self.notesIndexes[i]]
                note.updateNote(post)
                note.updateNote(pre)
                
        #for ending in ['On', 'Off']:  # strange bit here
        #    if post.endswith(ending):
        #        self.wordsList.insert(endNote, post)
        #        break
        #else:
        #    self.wordsList.insert(endNote+1, post)
        #
        #for ending in ['On', 'Off', 'End']:
        #    if pre.endswith(ending):
        #        self.wordsList.insert(startNote, pre)
        #        print 'pre "%s" ending: "%s", wordsList: %s'% (pre, ending, self.wordsList)
        #        break
        #else:
        #    print 'pre "%s" general, wordList: %s'% (pre, self.wordsList)
        #    self.wordsList.insert(startNote+1, pre)

        snippet = " ".join([str(x).strip() for x in self.wordsList])
        print 'new snippet: %s'% snippet
        keystroke(snippet)
        self.gotoNextNote()
        
    def rule_notechangemove(self, words):
        """<notesnavigate>(<sequence>|{noteaction}|forward)"""
        self.justInsert = False

        act =  self.getFromInifile(words[-1], 'noteaction')
        if act:
            action(act)
            return
        if self.hasCommon(words[-1], 'forward'):
            self.gotoNextNote()

    def rule_notesinsert(self, words):
        """[here] insert [<sequence>]"""
        ###
        ### position at correct position, possibly put a space.
        if self.hasCommon(words, 'here'):
            unimacroutils.buttonClick()
        self.getPrevNext()
        # position at left of word
        while self.inMiddleOfWord:
            keystroke("{left}")
            self.getPrevNext()
        # and put a space:
        keystroke("{space}{left}")
        self.getPrevNext()
        
      
     # def rule_test(self, words):
    #     """test position {direction}"""
    #     # position first at word boundary
    #     direction = self.getFromInifile(words[-1], 'direction')
    #     self.positionAtWordBoundary(direction)
    
    def subrule_notesnavigate(self, words):
        "here | [here] [next] (note | {n2-20} notes)"
        # leave next|previous for the moment, assume always count from the beginning      
        DIR = 'right'
        if self.hasCommon(words, 'here'):
            unimacroutils.buttonClick()
        try:
            nStr = self.getNumbersFromSpoken(words)[0] # returns a string or None
            n = int(nStr)
        except IndexError:
            n = 1
        if n == 1:
            gotoNext = self.hasCommon(words, 'next')
            if gotoNext:
                print 'move right one note! Todo'
        self.notesWanted = n
        print 'get %s notes'% n
        self.getNextNotes(n)
        print 'notesNavigate, wordsList: %s'% self.wordsList
        
       
    def getNextNotes(self, n=1):
        if self.nextchars is None:
            self.nextchars = self.frescobaldi.getNextLine()
        print 'nextchars: |%s|'% self.nextchars
        if self.justLeft is None:
            self.getPrevNext()
        if self.inMiddleOfWord:
            print 'inMiddleOfWord %s'% self.inMiddleOfWord
            if not self.prevchars:
                self.prevchars = self.frescobaldi.getPrevLine()
            lastWord = self.prevchars.split()[-1]
            numcharsleft = len(lastWord)
            print 'go left %s characters'% numcharsleft
            keystroke("{left %s}"% numcharsleft)
            self.getPrevNext()
            self.nextchars = self.frescobaldi.getNextLine()

        print 'nextchars: %s'% repr(self.nextchars)
        wordsList, notesIndexes = analyseString(self.nextchars)
        print 'wordsList: %s, notesIndexes: %s'% (wordsList, notesIndexes)
        notesFound = len(notesIndexes)
        
        if notesFound <= n:
            moreLines = 5
            print 'get %s more lines'% moreLines
            nextchars = self.frescobaldi.getNextLine(moreLines)
            # nextcharsplit = self.nextchars.split('\n\n') # double empty line ends the search
            # if len(nextcharsplit) > 1:
            #     self.hasAllInfoNext = True
            # self.nextchars = nextcharsplit[0]
            if nextchars == self.nextchars:
                raise Exception("getNextNotes, not enough notes found: %s, wanted: %s"% (notesFound, n))
            self.nextchars = nextchars
            wordsList, notesIndexes = analyseString(self.nextchars)
            notesFound = len(notesIndexes)
            print '----nextchars: %s'% repr(self.nextchars)
            if notesFound < n:
                print 'notesFound: %s'% notesFound
                print 'wordsList: %s, notesIndexes: %s'% (wordsList, notesIndexes)
                raise Exception("too little notes caught in %s lines down: %s, wanted: %s"%
                                (moreLines, notesFound, n))
        else:
            self.hasAllInfoNext = True
        wordsList, notesIndexes, beforeNotes, afterNotes, afterNoteComplete = \
                              getNotesFromWordsList(n, wordsList, notesIndexes)
        afterNoteComplete =afterNoteComplete or self.hasAllInfoNext
        return wordsList, notesIndexes, beforeNotes, afterNotes, afterNoteComplete
        

    def getPrevNotes(self, n=1):
        if self.justLeft is None:
            self.getPrevNext()
        if self.prevchars is None:
            self.prevchars = self.frescobaldi.getPrevLine()
        if self.inMiddleOfWord:
            print 'inMiddleOfWord %s'% self.inMiddleOfWord
            lastWord = self.prevchars.split()[-1]
            numcharsleft = len(lastWord)
            print 'go left %s characters'% numcharsleft
            keystroke("{left %s}"% numcharsleft)
            self.justLeft, self.justRight = self.prevchars[-numcharsleft-1], self.prevchars[-numcharsleft]
            print 'after go left: justLeft: %s, justRight: %s'% self.justLeft, self.justRight
            self.getPrevNextVariables(self, self.justLeft, self.justRight)
            self.prevchars = self.prevchars[:-numcharsleft]
            print 'prevchars after go left to beginning of note: %s'% repr(self.prevchars)
        
        print 'prevchars: %s'% repr(self.prevchars)
        wordsList, notesIndexes = analyseString(self.prevchars)
        print 'wordsList: %s, notesIndexes: %s'% (wordsList, notesIndexes)
        notesFound = len(notesIndexes)
        
        if notesFound <= n:
            moreLines = 5
            print 'get %s more lines'% moreLines
            prevchars = self.frescobaldi.getPrevLine(moreLines)
            if prevchars == self.prevchars:
                raise Exception("getPrevNotes, not enough notes found: %s, wanted: %s"% (notesFound, n))
            print '%s more lines prev:\n%s'% (moreLines, repr(prevchars))
            self.prevchars = prevchars

            wordsList, notesIndexes = analyseString(self.prevchars)
            notesFound = len(notesIndexes)
            print '----prevchars: %s'% repr(self.prevchars)
            if notesFound < n:
                print 'notesFound: %s'% notesFound
                print 'wordsList: %s, notesIndexes: %s'% (wordsList, notesIndexes)
                raise Exception("too little notes caught in %s lines up: %s, wanted: %s"%
                                (moreLines, notesFound, n))
        else:
            self.hasAllInfoPrev = True  ## know enough

        wordsList, notesIndexes, afterNotes, beforeNotes, beforeNoteComplete = \
                              getNotesFromWordsList(n, wordsList, notesIndexes, reverse=True)
        beforeNoteComplete = beforeNoteComplete or self.hasAllInfoPrev
        return wordsList, notesIndexes, afterNotes, beforeNotes, beforeNoteComplete
            

        
    def gotResults(self,words,fullResults):
        """flush last part of utterance"""
        if self.hadFigure:
            return
        
        output = []
        self.finishNote()
        print 'gotResults: newNotes: %s'% self.newNotes
        if not self.newNotes:
            return
        
        if self.hasSelection:
            keystroke("{del}")            
        
        if self.justLeft is None:
            self.getPrevNext()
        # print '------hasWhiteSpaceAround: %s, atEndOfLine: %s, hasWhiteSpaceBefore: %s'% (
            # self.hasWhiteSpaceAround, self.atEndOfLine, self.hasWhiteSpaceBefore)
        # print '===newNotes: %s'% self.newNotes
        
        noteOne = self.newNotes[0]
        if isinstance(noteOne, LyNote) and not noteOne.isNote():
                # update previous note, with partial note (eg a rythm)
                print 'noteOne is not a complete note: %s'% noteOne
                    # previous one:
                wordsList, notesIndexes, afterNotes, beforeNotes, beforeNoteComplete = self.getPrevNotes(1)
                lenBack = len(join(wordsList)) + len(afterNotes)
                keystroke("{shift+left %s}"% lenBack)
                wordsList[notesIndexes[0]].updateNote(noteOne)
                output.extend(wordsList)
                output.append(afterNotes)
                keystroke(join(output))
                output = []
                time.sleep(3)
                self.getPrevNext()
                if self.justRight:
                    print 'go one to the left'
                    keystroke(" {left}")
                    self.getPrevNext()
                self.newNotes.pop(0)
                
            
        # not a LyNote, such as a bar, put a space if it is not there
        if self.newNotes:
            noteOne = self.newNotes[0]
        if self.justLeft is None:
            self.getPrevNext()
            print("+++++hasWhiteSpaceBefore: |%s|"% self.hasWhiteSpaceBefore)
        if not self.hasWhiteSpaceBefore:
            print "insert space"
            output.insert(0, ' ')
            
        output.append(join(self.newNotes, separator=' '))
        if not (self.hasWhiteSpaceAfter or str(self.newNotes[-1]).endswith("{enter}")):
            output.append(' ')
        
        # print 'keystroking output: %s'% repr(output)
        keystroke(join(output))

        return
    
        print 'wordsList: %s'% self.wordsList
        if not self.wordsList:
            # check if just before a new note
            if self.justRight:
                print 'get next note'
                self.getNextNotes()

        if self.wordsList:
            print 'merge notes in wordsList'
            for i, note in enumerate(self.newNotes):
                if i < len(self.notesIndexes):
                    self.wordsList[self.notesIndexes[i]].updateNote(self.newNotes[i])
                else:
                    self.wordsList.append(note)
                    self.wordsList.append(' ')
            keystroke(join(wordsList))
            
            return
        # see if first note is a note, if so, output notes otherwise
        # change previous note (for example add rythm)
        
                
        
    def finishNote(self):
        """flush if far enough"""
        t = []
        noteDict = {}
        if self.note:
            if not self.rythm:
                if self.rythmicPattern:
                    rKey, rAttr = self.rythmicPattern.next()
                    if rKey == '-':
                        pass
                    else:
                        self.rythm = rKey
                    self.noteaddition = self.noteaddition + rAttr
                print 'rythm %s from pattern: %s'% (self.rythm, self.rythmicPattern)
        for name in ['note', 'pitch', 'rythm', 'point', 'noteaddition']:
            s = getattr(self, name, None)
            if s:
                # print 'name: %s, content: "%s"'% (name, s)
                t.append(s)
                setattr(self, name, "")

        noteText = ''.join(t)
        if noteText:
            note = LyNote(noteText)
            self.newNotes.append(note)
        print('newNotes: %s'% self.newNotes)

    def outputNewNotes(self):
        """just print the self.newNotes, separated by a space
        """
        output = []
        for note in self.newNotes:
            output.append(str(note))
            if not str(note).endswith("{enter}"):
                output.append(' ')
        self.keystroke(join(output))

    def getPrevNext(self):
        """get next en previous character
        
        assume there is no selection
        several instance variable are filled, for convenience
        self.justLeft, self.justRight : one character left and one char right of cursor
        self.hasWhiteSpaceAround
        self.hasWhiteSpaceBefore, self.hasWhiteSpaceAfter
        self.atEndOfLine
        """
        self.justLeft, self.justRight = self.frescobaldi.getPrevNext()
        # print 'from fr: |%s|(%s) |%s|(%s)'% (self.justLeft, len(self.justLeft), self.justRight, len(self.justRight))
        self.getPrevNextVariables(self.justLeft, self.justRight) 


    def getPrevNextVariables(self, justLeft, justRight):
        """compute several state variables, when justLeft and justRight are given
        
        mostly called from getPrevNext, but after a cursor movement justLeft and justRight are calculated,
        this routine calculates the remaining state variables.
        """
        self.atEndOfLine = (justRight == "\n")
        self.hasWhiteSpaceBefore = not justLeft.strip(' ')
        self.hasWhiteSpaceAfter = not justRight.strip(' ')
        self.inMiddleOfWord = not (self.hasWhiteSpaceAfter or self.hasWhiteSpaceBefore)
        self.hasWhiteSpaceAround = self.hasWhiteSpaceAfter and self.hasWhiteSpaceBefore
       
    def getFigurePart(self):
        # go left then right for selecting the note at the cursor position
        unimacroutils.saveClipboard()
        self.getPrevNext()
        if self.justRight != "<":
            # go left until < has been reached:
            for i in range(20):
                if self.getprevchar() == "<":
                    keystroke("{left}")
                    break
                keystroke("{left}")
            else:
                print 'getFigurePart, did not find "<"'
                keystroke("{right 20}")
                return
        # select step by step until > has been reached:
        for i in range(20):
            t = self.getselectionafterkeystroke("{shift+right}")
            if t and t.endswith(">"):
                break
        else:
            print 'getFigurePart, did not find ">"'
            unimacroutils.restoreClipboard()
            return
        result = t
        unimacroutils.restoreClipboard()
        return result
        
        
        
    def keystroke(self, keys):
        """internal keys for frescobaldi can have {] (braces), output them separate
        """
        keystroke(keys)
    
    def fillInstanceVariables(self):
        """fills the necessary instance variables
        
        configured from ini file, [general] section
        """
        self.newlineAfterBar = self.ini.getBool('general', 'newline after bar')

                
# standard stuff Joel (adapted for possible empty gramSpec, QH, unimacro)
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


