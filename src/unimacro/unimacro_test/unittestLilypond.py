#
# Python Macro Language for Dragon NaturallySpeaking
#   (c) Copyright 1999 by Joel Gould
#   Portions (c) Copyright 1999 by Dragon Systems, Inc.
#
# unittestLilypond.py
#   This script performs some basic tests of the LyNote class which handles lilypond input strings
#   This has nothing to do with speech recognition, but here because a Unimacro grammar "frescobaldi.py"
#   is developed in order to do inputs for lilypond in frescobalde.
#
#pylint:disable=C0209, R0913, R0914

import sys
import unittest
import os
import os.path
from unimacro import lynote
import TestCaseWithHelpers

def getBaseFolder(globalsDict=None):
    """get the folder of the calling module.

    either sys.argv[0] (when run direct) or
    __file__, which can be empty. In that case take the working directory
    """
    globalsDictHere = globalsDict or globals()
    baseFolder = ""
    if globalsDictHere['__name__']  == "__main__":
        baseFolder = os.path.split(sys.argv[0])[0]
        print('baseFolder from argv: %s'% baseFolder)
    elif globalsDictHere['__file__']:
        baseFolder = os.path.split(globalsDictHere['__file__'])[0]
        print('baseFolder from __file__: %s'% baseFolder)
    if not baseFolder or baseFolder == '.':
        baseFolder = os.getcwd()
        print('baseFolder was empty, take wd: %s'% baseFolder)
    return baseFolder

thisDir = getBaseFolder(globals())
logFileName = os.path.join(thisDir, "testresult.txt")

#---------------------------------------------------------------------------
# These tests should be run after we call natConnect
# no reopen user at each test anymore..
# no default open window (open window will be the calling program)
# default .ini files pop up when you first run this test. just ignore them.
class UnittestLyNote(TestCaseWithHelpers.TestCaseWithHelpers):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def checkLyResult(self, expNote, lyn):
        """check the parts of the note (lyn) against the expected values
        """
        note, elevation, duration, additions, backslashed = expNote
        self.assertEqual(note, lyn.note, 'note not equal "%s", expected: "%s", got: "%s"'% (lyn.originalInput, note, lyn.note))
        self.assertEqual(elevation, lyn.elevation, 'elevation not equal "%s", expected: "%s", got: "%s"'% (lyn.originalInput, elevation, lyn.elevation))
        self.assertEqual(duration, lyn.duration, 'duration not equal "%s", expected: "%s", got: "%s"'% (lyn.originalInput, duration, lyn.duration))
        self.assertEqual(additions, lyn.additions, 'additions not equal "%s", expected: "%s", got: "%s"'% (lyn.originalInput, additions, lyn.additions))
        self.assertEqual(backslashed, lyn.backslashed, 'backslashed not equal "%s", expected: "%s", got: "%s"'% (lyn.originalInput, backslashed, lyn.backslashed))
    
    def testSimpleNote(self):
        """test a few basic examples of a lilypond note
        """
        for s, expNote in [("bf,8.", ("bf", ",", "8.", "", None)),
                        ("g,8.", ("g", ",", "8.", "", None)),
                        ("a,,8", ("a", ",,", "8", "", None)),
                        ("cis", ("cis", "", "", "", None)),
                        ("aes'(", ("aes", "'", "", "(", None)),
                        (r"d4([\melisma", ("d", "", "4", "([", ['\\melisma'])),
                        (r"ais,,32..\melismaEnd]\break\)", ("ais", ",,", "32..", r"]\)", [r'\melismaEnd', r'\break']))]:
                        
            lyn = lynote.LyNote(s)
            self.checkLyResult( expNote, lyn )
            self.assertTrue(lyn.isNote(), '"%s" should be a note (isNote function), not: %s'% (s, lyn.isNote()))
            print('testSimpleNote OK: "%s", result: "%s"'% (s, lyn))

    def testIncompleteNoteAndUpdate(self):
        """test a few basic examples of a lilypond note
        """
        for s, expNote in [(",8.", ("", ",", "8.", "", None)),
                        ("8", ("", "", "8", "", None)),
                        (r"\melismaEnd", ("", "", "", "", [r"\melismaEnd"])),
                        (r",,1\melismaEnd]\break\)", ("", ",,", "1", r"]\)", [r'\melismaEnd', r'\break']))]:
                        
            lyn = lynote.LyNote(s)
            self.checkLyResult( expNote, lyn )
            print('testIncompleteNote OK: "%s", result: "%s"'% (s, lyn))

        updateNote = "4"            
        orgNote = "bf"
        lyorg = lynote.LyNote(orgNote)
        lyorg.updateNote(updateNote)
        expUpdated = ("bf", "", "4", "",  None)
        self.checkLyResult( expUpdated, lyorg )
        print('testIncompleteNote "%s" updated with "%s" OK, result: "%s"'% (orgNote, updateNote, lyorg))



        updateNote = ","            
        orgNote = "g'4("
        lyorg = lynote.LyNote(orgNote)
        lyorg.updateNote(updateNote)
        expUpdated = ("g", "", "4", "(", None)
        self.checkLyResult( expUpdated, lyorg )
        print('testIncompleteNote "%s" updated with "%s" OK, result: "%s"'% (orgNote, updateNote, lyorg))

        updateNote = "8"            
        orgNote = "a'4("
        lyorg = lynote.LyNote(orgNote)
        lyorg.updateNote(updateNote)
        expUpdated = ("a", "'", "8", "(", None)
        self.checkLyResult( expUpdated, lyorg )
        print('testIncompleteNote "%s" updated with string "%s" OK, result: "%s"'% (orgNote, updateNote, lyorg))

        lyorg = lynote.LyNote(orgNote)
        lyupdate = lynote.LyNote(updateNote)
        lyorg.updateNote(lyupdate)
        self.checkLyResult( expUpdated, lyorg )
        print('testIncompleteNote "%s" updated with instance "%s" OK, result: "%s"'% (orgNote, lyupdate, lyorg))






        updateNote = r"c'8..\melisma"            
        orgNote = "b'4("
        lyorg = lynote.LyNote(orgNote)
        lyorg.updateNote(updateNote)
        expUpdated = ("c", "''", "8..", "(", [r"\melisma"])
        self.checkLyResult( expUpdated, lyorg )
        print('testIncompleteNote "%s" updated with "%s" OK, result: "%s"'% (orgNote, updateNote, lyorg))

        lyorg = lynote.LyNote(orgNote)
        lyupdate = lynote.LyNote(updateNote)
        lyorg.updateNote(lyupdate)
        self.checkLyResult( expUpdated, lyorg )
        print('testIncompleteNote "%s" updated with instance "%s" OK, result: "%s"'% (orgNote, lyupdate, lyorg))

    def testReBackslashedWord(self):
        r"""test \break, \melisma etc, but refuse \( and \)"""
        for s in ['', r'\)']:
            m = lynote.reBackslashedWord.match(s)
            self.assertEqual(None, m, 'string "%s" should not match reBackslashWord'% s)
            print('testReBackslashedWord: correct fail to match "%s"'% s)
        for s in [r'\break', r'\melismaEnd']:
            m = lynote.reBackslashedWord.match(s)
            if m is None:
                self.fail('string r"%s" should match reBackslashWord'% s)
            print('testReBackslashedWord: correct match of "%s"'% s)
            
    def testStrAndRepr(self):
        """check the correct str and repr result"""        
        for s in ["g,8.", "a,,8"]:
            expStr = s
            lyn = lynote.LyNote(s)
            self.assertEqual(expStr, str(lyn), 'str of "%s" fails ("%s")'% (s, str(lyn)))
            print('testStrAndRepr: correct str "%s" (being the same)'% s)
            expRepr = "lynote: " + s
            self.assertEqual(expRepr, repr(lyn), 'repr of "%s" fails ("%s")'% (s, repr(lyn)))
            print('testStrAndRepr: correct repr "%s" (of "%s")'% (s, repr(s)))
    
    def testAnalyseString(self):
        """check the analyseString function"""
        
        expWords = ['a4', ' ', 'b', ' ', 'c']
        expNotesIndexes =  [0, 2, 4]
        s = 'a4 b c'
        words, noteIndexes = lynote.analyseString(s)
        words = [str(n) for n in words]
        self.assertEqual(expWords, words, 'words of testAnalyseString (%s) not as expected\nexpected: %s\ngot: %s'%
                         (s, expWords, words))
        self.assertEqual(expNotesIndexes, noteIndexes, 'noteIndexes of testAnalyseString (%s) not as expected\nexpected: %s\ngot: %s'%
                         (s, expNotesIndexes, noteIndexes))

        # testing the beforeWord case:
        s = ' | b8\n'
        expWords= [' | ', 'b8', '\n']
        expNotesIndexes =  [1]
        words, noteIndexes = lynote.analyseString(s)
        words = [str(n) for n in words]
        self.assertEqual(expWords, words, 'words of testAnalyseString (%s) not as expected\nexpected: %s\ngot: %s'%
                         (s, expWords, words))
        self.assertEqual(expNotesIndexes, noteIndexes, 'noteIndexes of testAnalyseString (%s) not as expected\nexpected: %s\ngot: %s'%
                         (s, expNotesIndexes, noteIndexes))

        # testing the beforeWord case:
        s = 'c4\n\n\n\n | b'
        expWords= ['c4', '\n\n\n\n | ', 'b']
        expNotesIndexes =  [0, 2]
        words, noteIndexes = lynote.analyseString(s)
        words = [str(n) for n in words]
        self.assertEqual(expWords, words, 'words of testAnalyseString (%s) not as expected\nexpected: %s\ngot: %s'%
                         (s, expWords, words))
        self.assertEqual(expNotesIndexes, noteIndexes, 'noteIndexes of testAnalyseString (%s) not as expected\nexpected: %s\ngot: %s'%
                         (s, expNotesIndexes, noteIndexes))





        # lot of text after last note:
        expWords = ['ais', '  ', 'b8', '\n\\time 3/4\n', 'g4', ' ', 'a', '  ', 'b', ' ', 'c', ' \\bar "||"\n', 'c1']
        expNotesIndexes =   [0, 2, 4, 6, 8, 10, 12]
        s = 'ais  b8\n\\time 3/4\ng4 a  b c \\bar "||"\nc1'
        words, noteIndexes = lynote.analyseString(s)
        words = [str(n) for n in words]
        self.assertEqual(expWords, words, 'words of testAnalyseString (%s) not as expected\nexpected: %s\ngot: %s'%
                         (s, expWords, words))
        self.assertEqual(expNotesIndexes, noteIndexes, 'noteIndexes of testAnalyseString (%s) not as expected\nexpected: %s\ngot: %s'%
                         (s, expNotesIndexes, noteIndexes))

    def doTestGetNotesFromWordsList(self, maxWords, wordsList, notesIndexes,
             expWords, expNotesIndexes, expBeforeNotes, expAfterNotes, expAfterNoteComplete, reverse=False):
        """test the variants for the getting of notes from a wordslist
        
        normal, for next notes and reverse, for previous notes.
        
        is called from routines below. several notes are tested in one run
        
        """
        for expName in 'expWords', 'expNotesIndexes', 'expBeforeNotes', 'expAfterNotes', 'expAfterNoteComplete':
            exp = locals()[expName]
            self.assertEqual(maxWords, len(exp), 'doTestGetNotesFromWordsList, %s should be sequence of length %s, not %s\nwordsList: %s'%
                (expName, maxWords, len(expWords), repr(wordsList)))
            
        if reverse:
            # setting expBeforeNoteComplete:
            expBeforeNoteComplete = expAfterNoteComplete
            
        
        for i in range(maxWords):
            numWords = i + 1
            print('---testing %s words from %s'% (numWords, wordsList))
        
            if reverse:
                # tricky with calling names:        
                gotWordsList, gotNotesIndexes, afterNotes, beforeNotes, beforeNoteComplete = \
                        lynote.getNotesFromWordsList(numWords, wordsList, notesIndexes, reverse=reverse)
            else:        
                gotWordsList, gotNotesIndexes, beforeNotes, afterNotes, afterNoteComplete = \
                        lynote.getNotesFromWordsList(numWords, wordsList, notesIndexes)
            gotWords = [str(a) for a in gotWordsList]
        
            self.assertEqual(expWords[i], gotWords, 'words of getNotesFromWordsList (%s) not as expected\nexpected: %s\ngot: %s'%
                         (numWords, expWords[i], gotWords))
            self.assertEqual(expNotesIndexes[i], gotNotesIndexes, 'noteIndexes of getNotesFromWordsList (%s) not as expected\nexpected: %s\ngot: %s'%
                         (numWords, expNotesIndexes[i], gotNotesIndexes))
            if reverse:
                # for previous words:
                self.assertEqual(expBeforeNotes[i], beforeNotes, 'REVERSE: beforeNotes of getNotesFromWordsList (%s) not as expected\nexpected: %s\ngot: %s'%
                             (numWords, repr(expBeforeNotes[i]), repr(beforeNotes)))
                self.assertEqual(expAfterNotes[i], afterNotes, 'REVERSE: afterNotes of getNotesFromWordsList (%s) not as expected\nexpected: %s\ngot: %s'%
                             (numWords, repr(expAfterNotes[i]), repr(afterNotes)))
                self.assertEqual(expBeforeNoteComplete[i], beforeNoteComplete, 'REVERSE beforeNoteCompleteof getNotesFromWordsList (%s) not as expected\nexpected: %s\ngot: %s'%
                             (numWords, expBeforeNoteComplete[i], beforeNoteComplete))
            else:
                # normal case, next words:
                self.assertEqual(expBeforeNotes[i], beforeNotes, 'beforeNotes of getNotesFromWordsList (%s) not as expected\nexpected: %s\ngot: %s'%
                             (numWords, repr(expBeforeNotes[i]), repr(beforeNotes)))
                self.assertEqual(expAfterNotes[i], afterNotes, 'afterNotes of getNotesFromWordsList (%s) not as expected\nexpected: %s\ngot: %s'%
                             (numWords, repr(expAfterNotes[i]), repr(afterNotes)))
                self.assertEqual(expAfterNoteComplete[i], afterNoteComplete, 'afterNoteCompleteof getNotesFromWordsList (%s) not as expected\nexpected: %s\ngot: %s'%
                             (numWords, expAfterNoteComplete[i], afterNoteComplete))

                

    def tttestGetNotesFromWordsList(self):
        """check the getNotesFromWordsList function
        
        here are the "forward" next note tests, with reverse == False (default)
        See the function getNotesFromWordsList in lynote.py
        """

        # testing the beforeWord case:
        s = ' | b8\n'
        expWords= [' | ', 'b8', '\n']
        expNotesIndexes =  [1]
        # first redo the analyseString test:
        wordsList, notesIndexes = lynote.analyseString(s)
        gotWordsList = [str(a) for a in wordsList]
        self.assertEqual(expWords, gotWordsList, 'assertion test: words of analyseString (%s) not as expected\nexpected: %s\ngot: %s'%
                         (s, expWords, gotWordsList))
        self.assertEqual(expNotesIndexes, notesIndexes, 'assertion test: notesIndexes of testAnalyseString (%s) not as expected\nexpected: %s\ngot: %s'%
                         (s, expNotesIndexes, notesIndexes))
        # now the real test
        maxWords = 1
        expWords =(['b8'],)
        expNotesIndexes = ([0],)
        expBeforeNotes = (' | ',)
        expAfterNotes = ('\n',)
        expAfterNoteComplete = (False,)
        self.doTestGetNotesFromWordsList(maxWords, wordsList, notesIndexes,
             expWords, expNotesIndexes, expBeforeNotes, expAfterNotes, expAfterNoteComplete)
        
        expWords= ['a4', ' ', 'b', ' ', 'c']
        expNotesIndexes =  [0, 2, 4]
        s = 'a4 b c'
        # first redo the analyseString test:
        wordsList, notesIndexes = lynote.analyseString(s)
        gotWordsList = [str(a) for a in wordsList]
        self.assertEqual(expWords, gotWordsList, 'assertion test: words of analyseString (%s) not as expected\nexpected: %s\ngot: %s'%
                         (s, expWords, gotWordsList))
        self.assertEqual(expNotesIndexes, notesIndexes, 'assertion test: notesIndexes of testAnalyseString (%s) not as expected\nexpected: %s\ngot: %s'%
                         (s, expNotesIndexes, notesIndexes))
        # now the real test
        maxWords = 3
        expWords = ['a4'], ['a4', ' ', 'b'], ['a4', ' ', 'b', ' ', 'c']
        expNotesIndexes = [0], [0,2], [0,2,4]
        expBeforeNotes = '', '', ''
        expAfterNotes = ' ', ' ', ''
        expAfterNoteComplete = True, True, False
        self.doTestGetNotesFromWordsList(maxWords, wordsList, notesIndexes,
             expWords, expNotesIndexes, expBeforeNotes, expAfterNotes, expAfterNoteComplete)
        
        # lot of text after last note:
        expWords = ['f', '  ', 'b8', '\n\\time 3/4\n', 'g4', ' ', 'a', '  ', 'b', ' ', 'c', ' \\bar "||"\n', 'c1']
        expNotesIndexes =  [0, 2, 4, 6, 8, 10, 12]
        s = 'f  b8\n\\time 3/4\ng4 a  b c \\bar "||"\nc1'

        wordsList, notesIndexes = lynote.analyseString(s)
        gotWordsList = [str(n) for n in wordsList]
        self.assertEqual(expWords, gotWordsList, 'assertion test: wordsList of testAnalyseString (%s) not as expected\nexpected: %s\ngot: %s'%
                         (s, expWords, gotWordsList))
        self.assertEqual(expNotesIndexes, notesIndexes, 'assertion test: notesIndexes of testAnalyseString (%s) not as expected\nexpected: %s\ngot: %s'%
                         (s, expNotesIndexes, notesIndexes))

        maxWords = 4
        expWords = (['f'], ['f', '  ', 'b8'],
                        ['f', '  ', 'b8', '\n\\time 3/4\n', 'g4'],
                        ['f', '  ', 'b8', '\n\\time 3/4\n', 'g4', ' ', 'a'])
        expNotesIndexes = [0], [0,2], [0,2,4], [0, 2, 4, 6]
        expBeforeNotes = '', '', '', ''
        expAfterNotes = '  ', '\n\\time 3/4\n', ' ', '  '
        expAfterNoteComplete = True, True, True, True
        self.doTestGetNotesFromWordsList(maxWords, wordsList, notesIndexes,
             expWords, expNotesIndexes, expBeforeNotes, expAfterNotes, expAfterNoteComplete)
        
    def tttestGetNotesFromWordsListReverse(self):
        """check the getNotesFromWordsList function

        here are the "backward" PREVIOUS note tests, with reverse == True
        See the function getNotesFromWordsList in lynote.py
        """
        # testing the beforeWord case:
        # s = ' | b8\n'
        # expWords= [' ', '|', ' ', 'b8', '\n']
        # expNotesIndexes =  [3]
        # # first redo the analyseString test:
        # wordsList, notesIndexes = lynote.analyseString(s)
        # gotWordsList = [str(a) for a in wordsList]
        # self.assertEqual(expWords, gotWordsList, 'assertion test: words of analyseString (%s) not as expected\nexpected: %s\ngot: %s'%
        #                  (s, expWords, gotWordsList))
        # self.assertEqual(expNotesIndexes, notesIndexes, 'assertion test: notesIndexes of testAnalyseString (%s) not as expected\nexpected: %s\ngot: %s'%
        #                  (s, expNotesIndexes, notesIndexes))
        # # now the real test
        # maxWords = 1
        # expWords =(['b8'],)
        # expNotesIndexes = ([0],)
        # expBeforeNotes = (' | ',)
        # expAfterNotes = ('\n',)
        # expAfterNoteComplete = (False,)
        # self.doTestGetNotesFromWordsList(maxWords, wordsList, notesIndexes,
        #      expWords, expNotesIndexes, expBeforeNotes, expAfterNotes, expAfterNoteComplete, reverse=True)
        # 
        
        # previous words test:
        expWords= ['a4', ' |\n', 'b', ' ', 'c', ' ']
        expNotesIndexes =  [0, 2, 4]
        s = 'a4 |\nb c '
        # first redo the analyseString test:
        wordsList, notesIndexes = lynote.analyseString(s)
        gotWordsList = [str(a) for a in wordsList]
        self.assertEqual(expWords, gotWordsList, 'assertion test: words of analyseString (%s) not as expected\nexpected: %s\ngot: %s'%
                         (s, expWords, gotWordsList))
        self.assertEqual(expNotesIndexes, notesIndexes, 'assertion test: notesIndexes of testAnalyseString (%s) not as expected\nexpected: %s\ngot: %s'%
                         (s, expNotesIndexes, notesIndexes))
        # now the real test
        maxWords = 3
        expWords = ['c'], ['b', ' ', 'c'], ['a4', ' |\n', 'b', ' ', 'c']
        expNotesIndexes = [0], [0,2], [0,2,4]
        expBeforeNotes = ' ', ' |\n', ''
        expAfterNotes = ' ', ' ', ' '
        expAfterNoteComplete = True, True, False
        self.doTestGetNotesFromWordsList(maxWords, wordsList, notesIndexes,
             expWords, expNotesIndexes, expBeforeNotes, expAfterNotes, expAfterNoteComplete, reverse=True)
      
        
            
def log(t):
    print(t)

def run():
    log('starting unittestLyNote')
    # trick: if you only want one or two tests to perform, change
    # the test names to her example def tttest....
    # and change the word 'test' into 'tttest'...
    # do not forget to change back and do all the tests when you are done.
    suite = unittest.makeSuite(UnittestLyNote, 'test')
##    natconnectOption = 0 # no threading has most chances to pass...
    result = unittest.TextTestRunner().run(suite)
    print(result)
if __name__ == "__main__":
    run()
