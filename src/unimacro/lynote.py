
import re
import sys
import copy
from dtactions.unimacro import utilsqh

reNote = re.compile(r"""([a-g](?:as|es|is|s|f)?)  # the notename also with flat (bf == b flat, english)
                        ([,']*)                 # elevation (octave up/down                        
                        ([0-9]*[.]*)            # duration, including augmentation dots
                        (.*)$                   # rest (assume no spaces)
                    """, re.VERBOSE+re.UNICODE)

reRest = re.compile(r"""([rRsS])  # the name of the rest
                        ##([,']*)                 # elevation (octave up/down                        
                        ([0-9]*[.]*)            # duration, including augmentation dots
                       ### (.*)$                   # rest (assume no spaces)
                    """, re.VERBOSE+re.UNICODE)
reBackslashedWord = re.compile(r"""([\\]\w+)""")

# for analyseString:
reSplitInWords = re.compile(r'(\s+)')  # split on whitespace
reIsWhiteSpace = re.compile(r'\s')



class LyNote
    def __init__(self, s):
        self.originalInput = s
        self.setVariables(s)
    
    def __len__(self):
        return len(str(self))
    
        
    def setVariables(self, s, recursive=None):
        """parse s and set self.note etc."""
        
        m = reNote.match(s)
        n = reRest.match(s)
        self.note = self.elevation = self.duration = ""
        rest = s
        self.additions = ""
        self.backslashed = None
        if m:
            self.note = m.group(1)
            self.elevation = m.group(2)
            self.duration = m.group(3)
            rest = m.group(4)
            if rest:
                self.additions, self.backslashed = self.orderRest(rest)
                # backslashed is a list of \melisma etc.
        elif n:
            self.note = n.group(1)
            self.duration = n.group(2)
            self.elevation = self.rest = ""
            
        else:
            # can be incomplete, add fake note in front and do again
            if recursive:
                print('recursive call of setVariables failed, s: %s'% s)
                return
            # print 'try recursive call of incomplete note: %s'% s
            sFake = 'c' + s
            self.setVariables(sFake, recursive=1)
            self.note = ""


    def isNote(self):
        return ( self.note != "" )
    
    def __str__(self):
        if self.backslashed:
            backslashed = " " + ' '.join(self.backslashed)
        else:
            backslashed = ""
        return "%s%s%s%s%s"% (self.note, self.elevation, self.duration, self.additions, backslashed)
    
    def __repr__(self):
        if self.backslashed:
            backslashed = " " + ' '.join(self.backslashed)
        else:
            backslashed = ""
        return "lynote: %s%s%s%s%s"% (self.note, self.elevation, self.duration, self.additions, backslashed)
    
    def getElevation(self):
        """return as int the elevation
        , = -1, ,, = -2, ' = 1, '' = 2 and "" = 0
        """
        if self.elevation == "":
            return 0
        if self.elevation.find(",") >= 0:
            return -len(self.elevation)
        if self.elevation.find("'") >= 0:
            return len(self.elevation)
        raise ValueError('getElevation: no valid elevation: "%s" (note: "%s"'% (self.elevation, self))
    
    def setElevation(self, elevation):
        """set the elevation string from the numeric elevation value
        0 = "", -1 = ",", 2 = "''" etc
        """
        if elevation == 0:
            return ""
        if elevation > 0:
            return "'"*elevation
        if elevation < 0:
            return ","*-elevation
        
        
    
    def orderRest(self, rest):
        if rest is None:
            return "", None
        
        if rest.find('\\') >= 0:
            additions = ""
            backslashed = []
            restList = reBackslashedWord.split(rest)
            for item in restList:
                if not item:
                    continue
                if reBackslashedWord.match(item):
                    backslashed.append(item)
                else:
                    additions += item

            return additions, backslashed
        return rest, None
        
    
    
    def updateNote(self, note):
        if type(note) in (bytes, str):
            note = LyNote(note)
        
        for attr in ['note', 'duration']:
            value = getattr(note, attr)
            if value:
                setattr(self, attr, value)
        if note.elevation:
            nElv = note.getElevation()
            orgElv = self.getElevation()
            newElv = orgElv + nElv
            self.elevation = self.setElevation(newElv)
            
        if note.additions:
            if self.additions:
                self.additions += note.additions
            else:
                self.additions = note.additions
        if note.backslashed:
            if self.backslashed:
                self.backslashed.extend(note.backslashed)
            else:
                self.backslashed = copy.copy(note.backslashed)

def analyseString(S):
    """split string in "words", leave the whitespace and return a second list of the note indexes
    
    return wordsList, notesIndexes, both being a list. the length of notesIndexes gives the number
    of notes found.
    """
    wordsList = [_f for _f in reSplitInWords.split(S) if _f]
    outputWords = []
    notesIndexes = []
    lyn = None
    inComment = 0
    peekwords = utilsqh.peekable(wordsList)
    index = 0

    for w in peekwords:
        if w == "%":
            comment = [w]
            while peekwords.peek() != '\n':
                comment.append(next(peekwords))
            outputWords.append(''.join(comment))
            index += 1
        
        if w and w[0] in 'abcdefgrR':
            lyn2 = LyNote(w)
            if lyn2.isNote():
                # print 'valid note: %s'% lyn2
                
                notesIndexes.append(index)
                outputWords.append(lyn2)
                index += 1
            else:
                print('not a note: %s'% w)
        elif w and w[0].strip():
            outputWords.append(w)
            index += 1
        else:
            # whitespace/text
            intermediate = []
        
            while 1:
                intermediate.append(w)
                peekword = peekwords.peek()
                if peekword is peekwords.sentinel:
                    outputWords.append(''.join(intermediate))
                    break
                if LyNote(peekword).isNote():
                    # flush:
                    outputWords.append(''.join(intermediate))
                    index += 1
                    break
                # else:
                #     print 'strange: peekword: %s'% repr(peekword)
                w = next(peekwords)

                
    return outputWords, notesIndexes
                    
def getNotesFromWordsList(n, wordsList, notesIndexes, reverse=False):
    """get exactly n notes from list, and return the start and end
    
    n = number of notes to be found
    wordsList: list of words, including notes
    notesIndexes: indexes of words that are notes
    reverse: with previous Notes, reverse the lists and back
    return:
    wordsList: the list of n notes and intermediate words
    notesIndexes: the list of indexes of the words, length exactly n
    beforeNotes: string that precedes the first note // is after the last note (reverse)
    afterNotes: string that follows the last note    // precedes the first note (reverse)
    afterNoteComplete: True if afterNotes extends until the next note  //
                                     // or until the previous note (reverse)
                                     
    if reverse == True, the last three variables should be interpreted in the opposite direction.
    
    """
    wordsList = copy.copy(wordsList)
    notesIndexes = copy.copy(notesIndexes)
    if reverse:
        lenw = len(wordsList)
        notesIndexes.reverse()
        wordsList.reverse()
        notesIndexes = [lenw-i-1 for i in notesIndexes]
    
    notesFound = len(notesIndexes)
    takeFromList = notesIndexes[n-1] + 1
    if notesFound == n:
        # string after last note:
        afterNotesList = wordsList[takeFromList:]
        afterNoteComplete = False  # not sure if reach until next note
    else:
        # take after n'th note until next note:
        takeAfterNotes = notesIndexes[n]
        afterNotesList = wordsList[takeFromList:takeAfterNotes]
        afterNoteComplete = True
    # print'afterNotes: %s,complete: %s'% (repr(afterNotes), afterNoteComplete) 
    wordsList = wordsList[:takeFromList]
    notesIndexes = notesIndexes[:n]
    firstNoteAt = notesIndexes[0]

    if firstNoteAt == 0:
        beforeNotesList = []
    else:
        # the string before the notes list:
        beforeNotesList = wordsList[:firstNoteAt]
        # print 'string before first note: %s'% beforeNotes
        wordsList = wordsList[firstNoteAt:]
        notesIndexes = [i-firstNoteAt for i in notesIndexes]
    # print 'notesIndexes: %s'% notesIndexes

    # reverse back:
    if reverse:
        lenw = len(wordsList)
        notesIndexes.reverse()
        wordsList.reverse()
        notesIndexes = [lenw-i-1 for i in notesIndexes]
        beforeNotesList.reverse()
        afterNotesList.reverse()
    
    afterNotes = ''.join(afterNotesList)
    beforeNotes = ''.join(beforeNotesList)

    return wordsList, notesIndexes, beforeNotes, afterNotes, afterNoteComplete
          
def join(Input, separator=''):
    """join all things (recursively if necessary)

    """
    if len(Input) == 0:
        return ''
    if type(Input) in (bytes, str):
        return Input
    else:
        return separator.join(str(i) for i in Input)



if __name__ == '__main__':
    
    #for s in ["", "(", r"(\break\melisma", r"\break\(-^2"]:
    #    mrest = reBackslashedWord.split(s)
    #    print 's: %s, mrest: %s'% (s, mrest)
    
    #for s in ["g,8.", "a", "cis'("]:
    #    lyn = LyNote(s)   
    #    print 'note: "%s", elevation: "%s", duration: "%s", additions: "%s"'% (lyn.note, lyn.elevation, lyn.duration, lyn.additions)
    #    print 'input: "%s", str: "%s", repr: "%s"'% (s, lyn, repr(lyn))
    #    lyn.updateNote("a")
    #    print 'note updated to a: %s'% lyn
    #    lyn.updateNote(r"c8.\(")
    #    print 'note updated to c 8. and \\(: %s'% lyn
    print('melisma: =============================================')
    for s in ["r2", r"g,8.\melisma", r"a\melisma"]:
        lyn = LyNote(s)
        print('note: "%s", elevation: "%s", duration: "%s", additions: "%s"'% (lyn.note, lyn.elevation, lyn.duration, lyn.additions))
        print('input: "%s", str: "%s", repr: "%s"'% (s, lyn, repr(lyn)))
        lyn.updateNote("a")
        print('note updated to a: %s'% lyn)
        lyn.updateNote(r"c8.\(")
        print('note updated to c 8. and \\(: %s'% lyn)
        lyn = LyNote(s)
        
        # join tests:
        print(join('abc'))
        print(join(['a', 'a', 'c']))
        print(join(['a', 'b'], separator='xxx'))