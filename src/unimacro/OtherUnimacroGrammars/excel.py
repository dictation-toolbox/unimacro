__version__ = "$Rev: 429 $ on $Date: 2011-05-31 16:21:03 +0200 (di, 31 mei 2011) $ by $Author: quintijn $"
# This file is part of a SourceForge project called "unimacro" see
# http://unimacro.SourceForge.net and http://qh.antenna.nl/unimacro
# (c) copyright 2003 see http://qh.antenna.nl/unimacro/aboutunimacro.html
#    or the file COPYRIGHT.txt in the natlink\natlink directory 
#
# Excel navigate in a sheet
"""
"""


import natlink
from dtactions.unimacro import unimacroutils
from natlinkcore import natlinkutils
from dtactions.unimacro import unimacroutils
import unimacro.natlinkutilsbj as natbj
import pprint
import types
from dtactions.unimacro.unimacroactions import doAction as action
from dtactions.unimacro.unimacroactions import doAction as action
from dtactions.unimacro import unimacroactions as actions
import win32com

# 
language = unimacroutils.getLanguage()
ancestor = natbj.DocstringGrammar
class ThisGrammar(ancestor):

    try:
        numberGram = natbj.numberGrammarTill999[language]
    except KeyError:
        print('take number grammar from "enx"')
        numberGram = natbj.numberGrammarTill999['enx']
        
    name = 'excel'
    iniIgnoreGrammarLists = ['sheets', 'books']
    gramSpec = """
<col> exported = column ({character}|{customcolumn}|back)[<excelcolumncommand>|<negativeaction>];
<date> exported = [<before>] date ({n1-31} | {n1-31}{month} | {n1-31}{month}{year})|
                        {datespecial};
<excelcolumncommand> = {excelcolumncommands};
<books> exported = (workbook) ({books}|show);
<sheets> exported = (sheet) ({sheets}|show);
<negative> exported = make number <negativeaction>;
<negativeaction> = negative | positive;
<before> = here;
#and the numbers grammar (0,...,999):                             
"""+numberGram
        
    def initialize(self):
        self.prevHandle = -1
        self.load(self.gramSpec)
        self.prevRows = []
        self.prevCols = []
        self.excel = None
        self.sheetsList = []
        self.booksList = []
        
    def gotBegin(self,moduleInfo):
        winHandle = moduleInfo[2]
        if self.prevHandle == winHandle:
            if not self.isActive():
                return
        else:
            self.prevHandle = winHandle
            if unimacroutils.matchModule('excel', modInfo=moduleInfo):
                #print 'activate firefox %s mode'% mode
                if self.checkForChanges:
                    print('excel (%s), checking the inifile'% self.name)
                    self.checkInifile()
                self.switchOnOrOff()
            elif self.isActive():
                #print 'deactivate Excel %s mode'% mode
                self.deactivateAll()
                if self.excel:
                    self.excel.disconnect()
                    self.excel = None
                return
        if self.isActive():
            # refreshes current position now as well:
            progInfo = unimacroutils.getProgInfo(moduleInfo)
            if self.excel is None:
                self.excel = actions.get_instance_from_progInfo(progInfo)
                if self.excel.app:
                    print('excel.app: %s'% self.excel.app)
                    print('Workbooks: %s'% self.excel.app.Workbooks.Count)
                else:
                    print('no instance for this Excel object available')
                    self.deactivateAll()
                    return
                    
            res = self.excel.checkForChanges(progInfo)
            #print 'res from changes: %s'% res
            if res:   
                self.refreshExcelSettings(res)
                self.printPositions('from gotBegin')

    #  Bij het initialiseren wordt de horizontale spatiejering uitgerekend.
    #    Er wordt van uitgegaan dat het venster niet te smal staat.
    def gotResultsInit(self,words,fullResults):
        """at start of actions"""
        # just in case a button was kept down (with show card commands)
        self.hadChoose = None
        self.chooseSpecification = ''
        self.number = ''
        self.hadRow = self.hadCol = None
        res = self.excel.checkForChanges()
        if res:
            self.refreshExcelSettings(res)
            self.printPositions('from gotResultsInit')

    def refreshExcelSettings(self, res):
        """here set settings of instance variables, when state has changed
        """
        if res <= 1:
            print('only position')
            return
        sheets = self.excel.getSheetsList()
        if not sheets:
            print('warning Excel: no sheets found in getSheetsList')
        if sheets != self.sheetsList:
            self.sheetsList = sheets
            self.sheetsDict = self.spokenforms.getDictOfMixedSpokenForms(sheets)
            self.sheetsList = list(self.sheetsDict.keys())
            self.setList('sheets', self.sheetsList)
            print('sheets: %s'% self.sheetsList)
        books = self.excel.getBooksList()
        if books != self.booksList:
            self.booksList = books
            self.booksDict = self.spokenforms.getDictOfMixedSpokenForms(books)
            self.booksList = list(self.booksDict.keys())
            self.setList('books', self.booksList)
            print('books: %s'% self.booksList)

    # several commands in Docstring format:
    def rule_backgroundcolor(self, words):
        """[here] background [color] {color}
        """
        app = self.excel.app
        if self.hasCommon(words[0], 'here'):
            action("MP 2,0,0;")
        colorCode = int(self.getFromInifile(words[-1], 'color'))
        if colorCode:
            app.ActiveCell.Interior.ColorIndex = colorCode
        else:
            app.ActiveCell.Interior.ColorIndex = None
    #                    
    #
    #        
    #def gotResults_row(self,words,fullResults):
    #    if self.hasCommon(words, 'back'):
    #        prevRow = self.popFromListIfDifferent(self.prevRows, self.currentRow)
    #        if prevRow:                
    #            self.gotoRow(prevRow)
    #        else:
    #            print 'no row to go back to'
    #        return
    #    self.hadRow = 1
    #    self.waitForNumber('number')


    def gotResults_books(self,words,fullResults):
        print('books: %s'% words)
        print(self.booksList)

    def gotResults_sheets(self,words,fullResults):
        print('sheets: %s'% words)
        print(self.sheetsList)
        self.excel.selectSheet(self.sheetsDict[words[1]])        

    def gotResults_negativeaction(self,words,fullResults):
        #print 'excel, make active cell negative'
        n = self.excel.app.ActiveCell.Value
        if type(n) == float:
            n = -n
            self.excel.app.ActiveCell.Value = n
        else:
            print('excel, not a float: %s (%s)'% (n, type(n)))

    def gotResults_col(self,words,fullResults):
        self.hadCol = 1
        if self.hasCommon(words[1], 'back'):
            prevCol = self.excel.getPreviousColumn()
            if prevCol:                
                self.gotoCol(prevCol)
            else:
                print('no column to go back to')
            return
        col = self.getCharacterFromSpoken(words[1])
        if col:
            self.gotoCol(col)
            return
        col = self.getFromInifile(words[1], 'customcolumn')
        if col:
            self.gotoCol(col)
        else:
            raise ValueError('excel, column: no valid column found: "%s" (all words: %s)'% (words[1], words))

    def gotResults_before(self,words,fullResults):
        if self.hasCommon(words, 'here'):
            if not self.doWaitForMouseToStop():
                print('excel, mouse does not stop, cancel command')
                return
            unimacroutils.buttonClick()

    def gotResults_date(self,words,fullResults):
        day = self.getNumberFromSpoken(words[1])
        if len(words) > 2:
            month = self.getFromInifile(words[2], 'month')
        else:
            month = 12
        keystroke('%s-%s{tab}'% (day, month))

    def gotoCol(self, col):
        """col should be a single letter
        """
        sheet = self.excel.sheet
        col = col.strip()
        if col == self.excel.currentColumn:
            print('column %s already selected'% col)
            return
        #print 'col: %s, curRow: %s'% (col, self.excel.currentRow)
        range = col + self.excel.currentRow
        sheet.Range(range).Select()
        cr = self.excel.savePosition()
        #print 'all current positions:'
        #pprint.pprint(self.excel.positions)

    def printPositions(self, comment=None):
        """print position info, for debugging purposes
        """
        if comment:
            print('----%s'% comment)
        print('colum info: %s'% self.excel.columns)
        print('row info: %s'% self.excel.rows)
        print('---------')
        

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

