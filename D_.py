__version__ = "$Revision: 606 $, $Date: 2019-04-23 14:30:57 +0200 (di, 23 apr 2019) $, $Author: quintijn $"
# -*- coding: latin-1 -*-
import string

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

Directories={
       "Abstracts":          "D:\\Data\\Txt\\AbstractsSheets",
       "b j":                "D:\\Data\\Txt\\Misc\\Bj",
       "Bib":                "D:\\Data\\Txt\\Bib",
       "Declarations":       "D:\\Data\\Txt\\Declaraties",
       "DP partitioning":    "D:\\Data\\Txt\\Papers\\DPPart",
       "fortran":            "D:\\Data\\Fortran",
       "datasets":           "D:\\Data\\sets",
       "papers":             "D:\\Data\\Txt\\Papers",       
       "heuristic":          "D:\\Data\\Txt\\Papers\\Heuristic",
       "D. P. H. C.":        "D:\\Data\\Txt\\Papers\\DPHC",
       "miscellaneous":      "D:\\Data\\Txt\\Misc",
       "notes":              "D:\\Data\\Txt\\Notities",
       "partitioning":       "D:\\Data\\Fortran\\part",
       "pioneer":            "D:\\Data\\Txt\\Pioneer",
       "receive":            "C:\\Comm\\Receive",
       "spell":              "D:\\Data\\Txt\\Misc\\Spell",
       "tasks":              "D:\\Data\\Txt\\Taken",
       "text":               "D:\\Data\\Txt",
       "fortran clus var":   "D:\\Data\\Fortran\\part\\ClusVar",
       "clus var":           "D:\\Data\\Txt\\Papers\\ClusVar",       
       "thesis":             "D:\\Data\\Txt\\Thesis",
       "trees":              "D:\\Data\\Txt\\Papers\\Trees",
       "receive":            "D:\\Shared App\\Receive",
       "macros":             "D:\\Shared App\\Macros",
       "NatLink":            "D:\\Shared App\\NatLink\\MacroSystem",
       "natlink macros":     "D:\\Shared App\\NatLink\\MacroSystem",
       "results":            "D:\\Data\\Fortran\\part\\ClusVar\\Results",
       "debug":              "D:\\Data\\Fortran\\part\\ClusVar\\Debug",
       "release":            "D:\\Data\\Fortran\\part\\ClusVar\\Release",
       "data":               "D:\\Data",
       "Python":             "D:\\Data\\Python",
       "source":             "D:\\Data\\Fortran\\part\\ClusVar\\Source",
       "MDS test":           "D:\\Data\\Fortran\\part\\ClusVar\\Results\\MDSTest",
       "libraries":          "D:\\Data\\Fortran\\Libraries",
       "random":             "D:\\Data\\Fortran\\Libraries\\Random",
       "Review":             "D:\\Data\\Txt\\Review",
}

ExcelExe = ("EXCEL","C:\\Program Files\\Microsoft Office\\Office\\EXCEL.EXE")
TextpadExe = ("TEXTPAD","C:\\Program Files\\TextPad 4\\TextPad.exe")
Documents = {
        "Expenses":         ("D:\Data\Txt\Notities\Uit2001.xls",ExcelExe),
        "Hierarchical":     ("D:\DATA\TXT\Papers\DPHC\DPHC.tex",TextpadExe),
        "Workspace Hierarchical":     ("D:\DATA\TXT\Papers\DPHC\DPHC.tws",TextpadExe),
        "Current Tasks":     ("D:\DATA\TXT\Taken\ToDo201101.txt",TextpadExe),
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