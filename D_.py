# -*- coding: latin-1 -*-

Digits = ['0','1','2','3','4','5','6','7','8','9','10']
Counts = ['1','2','3','4','5','6','7','8','9','10','11','12','13',
          '14','15','16','17','18','19','20','25','30','35','40','45','50',
          '55','60','65','70','75','80']

Alphabet = ["a\\a", "b\\b", "c\\c", "d\\d", "e\\e", "f\\f", "g\\g", "h\\h", "i\\i",
                "j\\j", "k\\k", "l\\l", "m\\m", "n\\n", "o\\o", "p\\p", "q\\q", "r\\r",
                "s\\s", "t\\t", "u\\u", "v\\v", "w\\w", "x\\x", "y\\y", "z\\z"]
ICAlphabet = ["a\\alpha", "b\\bravo", "c\\Charlie",  "d\\delta", "e\\echo", "f\\foxtrot",
                  "g\\golf", "h\\hotel", "i\\India","j\\Juliet","k\\kilo","l\\Lima","m\\Mike",
                  "n\\November","o\\Oscar","p\\papa",u"q\\Qu\xe9bec","r\\Romeo","s\\sierra",
                  "t\\tango","u\\uniform","v\\Victor","w\\whiskey","x\\X ray",
                  "y\\Yankee","z\\Zulu"]

SpecialCharacters = ["!\\exclamation-mark",'"\\double-quote',"#\\number-sign",
                     "$\\dollar-sign","%\\percent-sign","&\\ampersand","'\\single-quote",
                     "*\\asterisk","+\\plus",",\\comma","-\\hyphen","-\\minus",
                     ".\\dot","/\\slash","\\colon",";\\semicolon","<\\less-than",
                     "=\\equals",">\\greater-than","?\\question-mark","@\\at-sign",
                     "[\\open-bracket","\\backslash","]\\close-bracket","^\\hat",
                     "'\\backquote","|\\verticalbar","~\\tilde"]

Extensions={
        "fortran 90":           "f90",
        "f 90":                 "f90",
        "fortran":              "for",
        "fortran fixed":        "for",
        "f":                    "f",        
        "TeX":                  "tex",
        "output":               "out",
        "text":                 "txt",
        "input":                "in",
        "data":                 "dat",
        "Matlab":               "m",
        "Python":               "py",
        "Python command":       "pyc",
        "stripped":             "stripped",
        "selected":             "sel",
        "project":              "prj",
}

def BuildICDict(ICAlphabet):
    ICDict={}
    for x in ICAlphabet:
        xx=x.split(u'\\')
        ICDict[xx[0]]=xx[1]
    return ICDict

ICDict=BuildICDict(ICAlphabet)
#for x in ICDict.keys():
#	print x,ICDict[x]