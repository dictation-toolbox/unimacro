# _spokenforms.py 
#  written by: Quintijn Hoogenboom (QH softwaretraining & advies)
#  June 2011/March 2022
#
#pylint:disable=C0115, C0116, R0912, R0914, R0915, R0911
"""This module contains a class spokenforms that maintains spoken forms
for numbers, thus making it possible to use spoken forms for all numbers lists
in Unimacro grammars which need numbers 

tested with unittestSpokenForms.py (in unimacro_test directory of Unimacro)
"""
import re
import os
import os.path
import sys
import shutil
import string
import operator
from functools import reduce

from natlinkcore import natlinkstatus

from dtactions.unimacro import inivars
from dtactions.unimacro import utilsqh

class NumbersError(Exception):
    pass

status = natlinkstatus.NatlinkStatus()

# for generateMixedListOfSpokenForms:
reNonAlphaNumeric = re.compile(r'\W+')
reNumeric = re.compile(r'(\d+)')
reNumericUnderscore = re.compile(r'^([\d+]_+)')        # so 1_text results in text 
reNumericBracketsEnd = re.compile(r'\s*[(][0-9]+[)]\s*$') 
reLetterUnderscore = re.compile(r'^([a-zA-z]{1,2}[_])')  # so a_text only results in text, az_text also .
reVowelQuote = re.compile(r"([aeiou])'([sn])")
# for A or A. in spoken forms
reMatchUpperCaseLetter = re.compile(r'\b[A-Z]\b(?![.])')
reMatchUpperCaseLetterDot= re.compile(r'\b[A-Z]\.')
def addDot( match ):
    """for use in reMatchUpperCaseLetter"""
    return match.group() + '.'
def looseDot( match ):
    """for use in reMatchUpperCaseLetterDot"""
    return match.group()[0]

def fixSingleLetters(spoken, DNSVersion):
    """replace A by A. in Dragon <= 10 and A. in A in Dragon >= 11
    
    >>> fixSingleLetters("A. BC D", 10)
    'A. BC D.'
    >>> fixSingleLetters("C. DE. F", 11)
    'C DE. F'
    
    """
    if DNSVersion <= 10:
        m = reMatchUpperCaseLetter.search(spoken)
        if m:
            spoken= reMatchUpperCaseLetter.sub(addDot, spoken)
    else:
        # Dragon 11
        m = reMatchUpperCaseLetterDot.search(spoken)
        if m:
            spoken= reMatchUpperCaseLetterDot.sub(looseDot, spoken)
    return spoken


thisBaseDirectory = os.path.split(sys.modules[__name__].__dict__['__file__'])[0]

# special list names to be defined here:
number1to99stripped = list(range(1, 20)) +  list(range(20, 91, 10))


#####
##### get spokenforms.ini from baseDirectory or SampleDirectory into userDirectory:
status = natlinkstatus.NatlinkStatus()
# baseDirectory = status.getUnimacroDirectoryFromIni()
# if not baseDirectory:
#     baseDirectory = ""
#     #raise ImportError( 'no baseDirectory found while loading spokenforms.py, stop loading this module')
# sampleBases = [thisBaseDirectory.lower()]
# if thisBaseDirectory.lower() != baseDirectory.lower():
#     print 'actions module has ambiguous baseDirectory: |%s|, this: |%s|: take the latter one!'% (baseDirectory, thisBaseDirectory)
#     sampleBases.insert(0, baseDirectory.lower())
    
unimacroDirectory = status.getUnimacroDirectory().lower()
sampleBases = [unimacroDirectory]                   
sampleDirectories = [os.path.join(base, 'sample_ini') for base in sampleBases]
sampleDirectories = [p for p in sampleDirectories if os.path.isdir(p)]
      
if not sampleDirectories:
    print('\nNo Unimacro sample directory not found: %s\nCHECK YOUR CONFIGURATION!!!!!!!!!!!!!!!!\n')
#else:
#    print 'sample_directories: %s'% sampleDirectories
    
userDirectory = status.getUnimacroUserDirectory()

if not os.path.isdir(userDirectory):
    try:
        os.mkdir(userDirectory)
    except OSError:
        print('cannot make inifiles directory: %s'% userDirectory)
####

currentlanguage = None
inifile = None
ini = None

def resetSpokenformsGlobals():
    """utility function for unittest, to ensure there is a fresh start
    """
    #pylint:disable=W0603
    global currentlanguage, ini, inifile
    currentlanguage = ini = inifile = None
    
def checkSpokenformsInifile(language):
    """copy if needed the correct inifile into the userDirectory
    
    print message if no valid file found and return False 
    """
    #pylint:disable=W0603
    global currentlanguage, ini, inifile
    if language and language == currentlanguage and ini:
        return inifile # all OK
    ini = None
    currentlanguage = language
    filename = '%s_spokenforms.ini'% language
    if language == 'test':
        testDirectory = os.path.join(unimacroDirectory, 'unimacro_test', 'test_inifiles')
        print('test spokenforms.ini from %s'% testDirectory)
        inifile = os.path.join(testDirectory, '%s_spokenforms.ini'% language)
        print('spokenforms, test inifile: %s'% inifile)
    else:
        inifile = os.path.join(userDirectory, '%s_spokenforms.ini'% language)

    if not os.path.isfile(inifile):
        # now try to copy from the samples:
        print('---try to find spokenforms.ini file in old version (UserDirectory) or sample_ini directory')
        for sample in sampleDirectories:
            sampleinifile = os.path.join(sample, filename)
            if os.path.isfile(sampleinifile):
                print('---copy spokenforms.ini from\nsamples directory: %s\nto %s\n----'% (sampleinifile, inifile))
                shutil.copyfile(sampleinifile, inifile)
                if os.path.isfile(inifile):
                    break
                print('cannot copy sample spokenforms inifile to: "%s"'% inifile)
                inifile = None
                return None
        else:
            print('no valid sample "%s" file found in one of %s sample directories:\n|%s|'% \
                      (filename, len(sampleDirectories), sampleDirectories))
            return None
    # now assume valid inifile:
    try:
        ini = inivars.IniVars(inifile)
    except inivars.IniError:
        print('Error in spokenforms inifile: "%s"'% inifile)
        m = str(sys.exc_info()[1])

        print('message: %s'% m)
        print('\n\n===please edit %s (open by hand)'% inifile)
        #win32api.ShellExecute(0, "open", inifile, None , "", 1)    
    else:
        return inifile
    return None

def openInifile(inifilepath):
    #pylint:disable=W0603
    global inifile, ini
    if not os.path.isfile(inifilepath):
        ini = inifile = None
        print('no inifile spokenforms.ini found. Please repair')
        return None
    try:
        ini = inivars.IniVars(inifilepath)
    except inivars.IniError:
        
        print('Error in numbers inifile: %s'% inifilepath)
        m = str(sys.exc_info()[1])
        print('message: %s'% m)
        # pendingMessage = 'Please repair spokenforms.ini file\n\n' + m
        ini = None
        print('please edit %s (open by hand)'% inifilepath)
        return None
        #win32api.ShellExecute(0, "open", inifile, None , "", 1)
    else:
        return ini

def editSpokenForms(comingFrom=None, name=None, language=None):
    """show the spokenforms.ini file in a editor
    """
    if not language:
        print('editSpokenForms: call with language is required!')
        return
    
    inifilepath = checkSpokenformsInifile(language)
    if not inifilepath:
        print('editSpokenForms: no valid spokenforms inifile for language "%s" available'% language)
        return        
    if comingFrom:
        name=name or ""
        comingFrom.openFileDefault(inifilepath, name=name)
    else:
        print('inifile: ', inifilepath)
        print('please edit (open by hand): %s'% inifilepath)
    #win32api.ShellExecute(0, "open", inifile, None , "", 1)
    print('note: you need to restart Dragon after editing the spoken forms inifile.')
    

showSpokenForms = editSpokenForms

class SpokenForms:
    """maintain a (class wide) dict of numbers -> spoken forms and vice versa
    a language is required at __init__ time.
    
    Also characters (a, b, etc) to spoken and vice versa
    
    It is assumed only one language can be active at the same time, so the dicts
    are kept global in the class
    """
    n2s = {}
    s2n = {}
    char2spoken = {} # characters of radio alphabet possibly extended
    spoken2char = {}
    abbrev2spoken = {} # lists of spoken forms
    spoken2abbrev = {}
    ext2spoken = {}    # file extensions (without the dot) (section "extensions")
    spoken2ext = {}    
    punct2spoken = {}  # punctuation, from section punctuationreverse (other way round!)
    spoken2punct = {}
    
  
    language = None
    
    def __init__(self, language, DNSVersion):
        # global in this module, does not extra work if language did not change:
        checkSpokenformsInifile(language)
        self.DNSVersion = DNSVersion
        
        if self.language is None or self.language != language:
            self.__class__.language = None
            if self.filldicts(language):
                self.__class__.language = language
                
                
    def filldicts(self, language):
        """fill the base dictionaries for the class
        """
        self.n2s.clear()
        self.s2n.clear()
        if ini is None:
            print('no inifile for numbers spoken forms')
            return False
        # section in spokenforms.ini file:
        section = "numbers"
        if not section in ini.get():
            print('no section in spokenforms.ini for language: %s'% section)
            return False
        for k in ini.get(section):
            v = ini.get(section, k)
            try:
                n = int(k)
            except ValueError:
                print('invalid entry in spokenforms.ini for language: %s\n' \
                      '%s = %s  (key must be a integer)'% (language, k, v))
                continue
            for splitChar in ",;|":
                if v.find(splitChar) > 0:
                    V = [s.strip() for s in v.split(splitChar)]
                    break
            else:
                V = [v]
            for w in V:
                self.s2n[w] = n
            self.n2s[n] = V
        
        section = 'alphabet'
        for k in ini.get(section):
            v  = ini.get(section, k)
            if not v:
                continue
            for splitChar in ",;|":
                if v.find(splitChar) > 0:
                    V = [s.strip() for s in v.split(splitChar)]
                    break
            else:
                V = [v]
            for w in V:
                self.spoken2char[w] = k
            self.char2spoken[k] = V
            
        section = 'abbrevs'
        for kk in ini.get(section):
            ## all convert to lowercase:
            k = kk.lower()
            v  = ini.get(section, k)
            
            if not v:
                v = ' '.join(l.upper() for l in k)
            for splitChar in ",;|":
                if v.find(splitChar) > 0:
                    V = [s.strip() for s in v.split(splitChar)]
                    break
            else:
                V = [v]
            V = [fixSingleLetters(s, self.DNSVersion) for s in V]
            for w in V:
                self.spoken2abbrev[w] = k
            self.abbrev2spoken[k] = V

        section = 'extensions'
        for k in ini.get(section):
            v  = ini.get(section, k)
            if not v:
                v = ' '.join(l.upper() for l in k)
            for splitChar in ",;|":
                if v.find(splitChar) > 0:
                    V = [s.strip() for s in v.split(splitChar)]
                    break
            else:
                V = [v]
            V = [fixSingleLetters(s, self.DNSVersion) for s in V]
            for w in V:
                # extensions can point back to more extensions, eg excel to .xls and to .xlsx
                self.spoken2ext.setdefault(w, []).append(k)
            self.ext2spoken[k] = V

        section = 'punctuationreverse'
        for k in ini.get(section):
            try:
                v  = ini.get(section, k)
            except inivars.IniError:
                print('Error in ["%s"] section of spokenforms.ini files'% section)
                m = str(sys.exc_info()[1])
                print('message: %s'% m)
                v = None
                
            if not v:
                continue
                # extensions can point back to more extensions, eg excel to .xls and to .xlsx
            self.spoken2punct[k] = v
            self.punct2spoken.setdefault(v, []).append(k)
        
        return True
    
    def correctLettersForDragonVersion(self, spoken):
        """convert A to A. in NatSpeak <= 10 and B. int B for Dragon 11
        """
        return fixSingleLetters(spoken, self.DNSVersion)
    
    def getSpokenFormsList(self, n):
        """return a list of spoken forms, also for numbers larger than filldicts gave
        
        this one goes one way, only fills n2s if not available yet. Larger numbers may be included
        for future references.
        """
        if n in self.n2s:
            return self.n2s[n]
        spokenforms = self.generateSpokenFormsFromNumber(n)
        if spokenforms:
            self.n2s[n] = spokenforms
            return spokenforms
        return None
    
    def getMixedCharactersList(self, ListOfChars=None):
        """return a list of strings with either the number or the spoken forms
        """
        if ListOfChars is None:
            ListOfChars = string.ascii_lowercase
        L = []
        for s in ListOfChars:
            if s in self.char2spoken:
                L.extend(self.char2spoken[s])
            else:
                L.append(s)
        return L
    
    def getMixedList(self, ListOfNumbers):
        """return a list of strings with either the number or the spoken forms
        """ 
        L = []
        for s in ListOfNumbers:
            i = int(s) # in case we started with a string
            spokenforms = self.getSpokenFormsList(i)
            if spokenforms:
                L.extend(spokenforms)
                for name in spokenforms:
                    # needed for retrieving the numbers
                    # spokenforms back to the numbers:
                    if not name in self.s2n:
                        self.s2n[name] = i
            else:
                print('no spoken forms found for %s'% i)
                L.append(str(i))
        return L

    def generateSpokenFormsFromNumber(self, n):
        """return a list of possible spoken forms strings
        """
        for i in 100, 1000, 0, 1:
            if not i in self.n2s:
                print('spokenforms.ini should have entry or entries for %s'%i)
                return [str(n)]
        hundred = self.n2s[100][0]
        thousand = self.n2s[1000][0]
        oh = self.n2s[0][0]
        one = self.n2s[1][0]
    
        s = str(n)

        if n < 100:
            print('should not come here for %s, all numbers below 100 should be in ini file'%n)
            return None
        if n < 1000:
            if n == 100:
                print('should %s take from n2s'% n)
                return s
            if s.endswith('00'):
                digitstrings = self.n2s[int(s[0])]
                return [d+' '+hundred for d in digitstrings]
            if s[1] == '0':
                # one oh three 103 etc
                sp1 = self.n2s[int(s[0])]
                sp2 = self.n2s[int(s[2])]
                spList =['%s %s %s'% (s1, oh, s2) for s1 in sp1 for s2 in sp2]
                if s[0] == '1':
                    sp1 = self.n2s[100]
                else:
                    sp1 = ['%s %s'% (d, hundred) for d in self.n2s[int(s[0])]]
                spList.extend(['%s %s'% (s1, s2) for s1 in sp1 for s2 in sp2])
                return spList
            if s[0] == '1':
                # hundred ... or  one ...
                sp = self.n2s[int(s[1:])]
                spList = ['%s %s'% (hundred, s) for s in sp]
                spList.extend(['%s %s'% (one, s) for s in sp])
                return spList
            sp1 = self.n2s[int(s[0])]
            sp2 = self.n2s[int(s[1:])]
            spList = ['%s %s %s'% (s1, hundred, s2) for s1 in sp1 for s2 in sp2]
            spList.extend(['%s %s'% (s1, s2) for s1 in sp1 for s2 in sp2])
            return spList
        if n < 10000:
            if n == '1000':
                print('should %s take from n2s'% n)
                return s
            if s.endswith('000'):
                digitstrings = self.n2s[int(s[0])]
                return [d+' '+thousand for d in digitstrings]
            if s[1:3] == '00':
                # one oh three 103 etc
                sp1 = self.n2s[int(s[0])]
                sp2 = self.n2s[int(s[3])]
                spList =['%s %s %s %s'% (s1, oh, oh, s2) for s1 in sp1 for s2 in sp2]
                if s[0] == '1':
                    sp1 = self.n2s[1000]
                else:
                    sp1 = ['%s %s'% (d, thousand) for d in self.n2s[int(s[0])]]
                spList.extend(['%s %s'% (s1, s2) for s1 in sp1 for s2 in sp2])
                return spList
                    
            if s[1] == '0':
                # thousand ... or  ten ...
                if s[0] == '1':
                    sp1 = self.n2s[1000]
                else:
                    sp1 = ['%s %s'% (d, thousand) for d in self.n2s[int(s[0])]]
                sp2 = self.n2s[int(s[2:])]
                spList = ['%s %s'% (s1, s2) for s1 in sp1 for s2 in sp2]
                
                # twenty eleven:
                sp1 = self.n2s[int(s[0:2])]
                spList.extend(['%s %s'% (s1, s2) for s1 in sp1 for s2 in sp2])
                return spList
            sp1 = self.n2s[int(s[0:2])]
            if s[2] == '0':
                sp2 = ['%s %s'% (oh, d) for d in self.n2s[int(s[3])]]
            else:
                sp2 = self.n2s[int(s[2:4])]
            spList = ['%s %s'% (s1, s2) for s1 in sp1 for s2 in sp2]
            return spList
        return None
    
    def generateMixedListOfSpokenForms(self, s):
        """return spoken forms with at number places spoken forms replaced
            use for filenames with numbers in it
            
        if name startswith number_ skip it optionally
        if name endswith (number) skip it optionally
            
        if name startswith letter_ skip it optionally    
            
        """
        # make number _ at start and numbers in brackets at end of name optional
        # by recursing this function
        # eg 1_testing and website test (2)
        #
        s = reVowelQuote.sub(r'\1\1\2', s)  # no doubling from foto's to fotoos
        t = reNumericUnderscore.sub('', s)
        t = reNumericBracketsEnd.sub('', t)
        t = reLetterUnderscore.sub('', t)

        if t == s:
            prevResult = None
        else:
            prevResult = self.generateMixedListOfSpokenForms(t)
            #print 'intermediate: %s'% prevResult   
            
        Result = None # end result
        result = []   # intermediate result
        
        # dutch: e acute = ee etc.
        s = utilsqh.unifyaccentedchars(s)
        if not s.isalnum():
            sList = []
            for c in s:
                if c.isalnum():
                    sList.append(c)
                else:
                    sList.append(" ")
            s = ''.join(sList)
            s = s.replace('  ', ' ')
        # 
        # s = reNonAlphaNumeric.sub(' ', s)
        s = reNumeric.split(s)
        s = [_f for _f in s if _f]
        for i, phrase in enumerate(s):
            if phrase.find(' ') > 0:
                phraseList = phrase.split()
                s[i:i+1] = phraseList
        for item in s:
            item = item.strip()
            if not item:
                continue
            try:
                n = int(item)
            except ValueError:
                ## to all lowercase???:
                if item.lower() in self.abbrev2spoken:
                    result.append(self.abbrev2spoken[item.lower()])
                else:
                    result.append(item)
            else:
                spok = self.getSpokenFormsList(n)
                if spok:
                    result.append(spok)
        for item in result:
            if isinstance(item, list):
                if Result:
                    Result = ['%s %s'% (i,j) for i in result for j in item]
                else:
                    Result = item
            else:
                if Result:
                    Result = ['%s %s'% (r, item) for r in result]
                else:
                    Result = [item]
        if prevResult:
            Result = prevResult + Result
        ## all lower case (?)
        return Result
    
    def getDictOfMixedSpokenForms(self, Values):
        """return a dict with spoken forms (multiple) as keys, and the Values as values
        (in grammar excel)
        """
        if not Values:
            return {}
        D = {}
        for v in Values:
            L = self.generateMixedListOfSpokenForms(v)
            if not L:
                continue
            for key in L:
                if key in D:
                    if D[key] == v:
                        continue
                    print("warning, double entry %s (%s and %s), take latter"% (key, D[key], v))
                D[key] = v
        return D
    
    def getCharFromSpoken(self, spoken, originalList=None):
        """try to retrieve the called character from the dict spoken2char in this class

        check result with originalList, 
        """
        first = self.spoken2char.get(spoken, None)
        if originalList is None:
            return first
        if first in originalList:
            return first
        return None
    
    def getPunctuationFromSpoken(self, spoken, originalList=None):
        """try to retrieve the called character from the dict spoken2char in this class

        check result with originalList, which may be any sequence
        """
        first = self.spoken2punct.get(spoken, None)
        if originalList:
            if first in originalList:
                return first
        else:
            return first
        return None

    def getNumberFromSpoken(self, spoken, originalList=None, asStr=None):
        """try to retrieve the called number from the dict s2n in this class

        check result with originalList, or try to make a number from spoken
        if asInt == True, return as str, otherwise return a int

        passing a list of words is handled in natlinkutilsbj.        
        """
        first = self.s2n.get(spoken, None)
        if originalList:
            orig = list(map(int, originalList))
            if first is None:
                try:
                    first = int(spoken)
                except ValueError:
                    pass
            if first is not None and first in orig:
                if asStr:
                    first = str(first)
                return first
        else:
            # take result anyway:
            if first is not None:
                if asStr:
                    first = str(first)
                return first
            # try is spoken represents a int:
            try:
                n = int(spoken)
                if asStr:
                    return str(n)
                return n
            except ValueError:
                pass
        return None
    
    def filldictsAboveHundred(self, num):
        """make spoken forms for numbers above 100
        eg 360 returns ['three sixty', 'three hundred sixty']
        """
        if num <= 100:
            raise ValueError('numbers, fillDictsAboveHundred call with number > 100, not: %s'% num)
        if num > 1000:
            raise ValueError('numbers, fillDictsAboveHundred call with number <= 1000, not: %s'% num)
        prefixSection = 'prefixes'
        numbersSection = 'numbers'
        if num == 1000:
            thousand = ini.getList(prefixSection, 'thousand') or ['thousand']
            self.n2s[1000] = thousand
            for t in thousand:
                self.s2n[t] = 1000
            return None

        snum = str(num)
        self.n2s[num] = [snum]
        self.s2n[snum] = num
        return None
        ## TODO QH
        h, rest = num / 100, num%100
        hundred = ini.getList(prefixSection, 'hundred', None) or ['hundred']
        if rest:
            srest = str(rest)
            restspoken = ini.getList(numbersSection, srest, None)
            if not restspoken:
                snum = str(num)
                return [snum]
        else:
            restspoken = ['']
        if num == 100:
            s100 = str(100)
            hspoken = ini.getList(numbersSection, s100, None) or hundred
        elif h == 1:
            s100 = str(100)
            hspoken = ini.getList(numbersSection, s100, None) or hundred
        else:
            hundredspoken = hundred[0]
            numspoken = ini.getList(numbersSection, str(h), None)
            if numspoken:
                # numbers + hundred or numbers:
                hspoken = [n + ' ' + hundredspoken for n in numspoken] + numspoken
            else:
                return [str(num)]
        spokenlist = [(a+ ' ' + b).strip() for a in hspoken for b in restspoken]
        self.n2s[num] = spokenlist
        for sp in spokenlist:
            self.s2n[sp] = num
        return None
            
    def sortedByNumbersValues(self, grammarsList, valueSpokenDict=None):
        """return sorted list if this is a numbers list (sorted by the number value)
        
        if valueSpokenDict == True: return the dict, like {1: ['one'], }
        otherwise return only the spoken forms like [ 'one', ...]
        
        If list contains items that do not go back to a number, return None
        TODOQH ik snap hier niets meer van.
        """
        dec = {}
        for g in grammarsList:
            value = self.getNumberFromSpoken(g)
            if value is None:
                return None
            dec.setdefault(value, []).append(g)
        if valueSpokenDict:
            return dec
        return reduce(operator.add, list(dec.values()))
        

    ## function to give numerical list:
    def getNumberList(self, listName):
        """returns the list of numbers for inserting in a grammar
    
        The list can be predefined here, and even be specific for different
        language versions.
    
        If the list is not predefined, it is extracted here.
    examples:
        number1to3 gives: [1, 2, 3]
        0-20 gives: [0, 1, ..., 20]
        
        but number10to99 gives [10, 11, ..., 99]
        
    Note:
        0-360 or number1to360 gives [0, 10, ..., 360]
        """
        #pylint:disable=R0201
        #print 'try to fill numbers list: "%s"'% listName
        try:
            return globals()[listName]
        except KeyError:
            pass
        
        # not found in predefined names, extract automatically:
        if listName[:6] == 'number':
            numbersSpec = listName[6:]
        elif listName[0] == 'n':
            numbersSpec = listName[1:]
        if numbersSpec.find('to') > 0:
            L = numbersSpec.split('to')
        elif '-' in numbersSpec:
            L = numbersSpec.split('-')
        if len(L) != 2:
            print('getNumbersList, (1) seems not to be a valid definition of a numbers list: %s'% listName)
            return []
        try:  
            n1 = int(L[0])
            n2 = int(L[1])
        except ValueError:
            print('getNumbersList, (1) seems not to be a valid definition of a numbers list: %s'% listName)
            return []
        
        if n1 == 0 and n2 == 0:
            print('getNumbersList, (2) seems not to be a valid definition of a numbers list: %s'% listName)
            return []
            
        if n1%10 == 0 and n2%10==0 and (n2 > 100 or n1 >= 10):
            L = list(range(n1, n2+1, 10))
        else:
            L = list(range(n1, n2+1))
        #return [str(i) for i in L]
        return L

def _test():
    #pylint:disable=C0415
    import doctest
    doctest.testmod()

if __name__ == '__main__':
    _test()
