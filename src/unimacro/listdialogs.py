#Bart Jan's work, needs testing presently
#pylint:disable = W0612, W0702, C0321, R0913, C0209
import time
import pickle   

from pywin.mfc import dialog
from pywin.framework import dlgappcore, app
import win32ui
import win32con
import commctrl
import win32api
from dtactions.unimacroutils import AppBringUp

from natlinkutilsbj import *
status = natlinkstatus.NatlinkStatus()
dataDirectory = status.getUnimacroDataDirectory()
# print(f'dataDirectory: {dataDirectory}')


IDC_NUMBERS=1010

class ListDialog (dialog.Dialog):  # Taken from the demo; adapted

    def __init__ (self, title, List, heading='item',size=(300,200),okButton='OK',resize=None):
        self.iconId = win32ui.IDR_MAINFRAME
##        print 'title: %s'% title
##        print 'List: %s'% List
        id = self._maketemplate(title, size, okButton, resize)
        print('id: %s'% id)
        dialog.Dialog.__init__ (self, id)
        self.Owner=None
        self.defer=None
        self.HookMessage (self.on_size, win32con.WM_SIZE)
        self.HookNotify(self.OnListItemChange, commctrl.LVN_ITEMCHANGED)
        self.HookCommand(self.OnListClick, win32ui.IDC_LIST1)
        self.heading=heading
        self.items = List
        self.size=size

    def _maketemplate(self, title, size, okButton="OK", resize=None):
        style = win32con.WS_DLGFRAME | win32con.WS_SYSMENU | win32con.WS_VISIBLE
        if resize:
            style=style | win32con.WS_MAXIMIZEBOX | win32con.WS_MINIMIZEBOX | win32con.WS_SIZEBOX
        ls = (
            win32con.WS_CHILD           |
            win32con.WS_VISIBLE         |
            commctrl.LVS_ALIGNLEFT      |
            commctrl.LVS_REPORT
            )
        bs = (
            win32con.WS_CHILD           |
            win32con.WS_VISIBLE
             )
        ns = (
            win32con.WS_CHILD           |
            win32con.WS_VISIBLE         |  
            commctrl.LVS_ALIGNLEFT      |
            commctrl.LVS_NOCOLUMNHEADER |
            commctrl.LVS_NOSCROLL |
            commctrl.LVS_REPORT
            )
        return [ [title, (0, 0, 200, 200), style, None, (8, "MS Sans Serif")],
            ["SysListView32", None, win32ui.IDC_LIST1, (0, 0, 200, 200), ls], 
            [128,   "OK", win32con.IDOK, (10, 0, 50, 14), bs | win32con.BS_DEFPUSHBUTTON],
            [128,   "Cancel",win32con.IDCANCEL,(100, 0, 50, 14), bs],
            ["SysListView32", None, IDC_NUMBERS, (0, 0, 450, 200), ns],                 
            ]
    

    def FillList(self):
        size = self.GetWindowRect()
        width = size[2] - size[0] - (10)
        itemDetails = (commctrl.LVCFMT_LEFT, width, self.heading, 0)
        self.itemsControl.InsertColumn(0, itemDetails)
        index = 0
        for item in self.items:
            #preceding spaces are stripped to facilitate list completion
            itemText=str(item).lstrip()
            index = self.itemsControl.InsertItem(index+1, itemText, 0)

    def OnListClick(self, id, code):
        if code==commctrl.NM_DBLCLK:
            self.EndDialog(win32con.IDOK)
        return 1

    def OnListItemChange(self,std, extra):
        (hwndFrom, idFrom, code), (itemNotify, sub, newState, oldState, change, point, lparam) = std, extra
        oldSel = (oldState & commctrl.LVIS_SELECTED)!=0
        newSel = (newState & commctrl.LVIS_SELECTED)!=0
        if oldSel != newSel:
            try:
                if newSel:
                    self.SelItems.append(itemNotify)
                else:
                    if itemNotify in self.SelItems:
                        self.SelItems.remove(itemNotify)
                self.butOK.EnableWindow(1)
            except win32ui.error:
                self.SelItems=[]

    def OnInitDialog (self):
        rc = dialog.Dialog.OnInitDialog (self)
        self.itemsControl = self.GetDlgItem(win32ui.IDC_LIST1)
        self.butOK = self.GetDlgItem(win32con.IDOK)
        self.butCancel = self.GetDlgItem(win32con.IDCANCEL)
        self.numbersControl = self.GetDlgItem(IDC_NUMBERS)
        self.numbersControl.EnableWindow(0)
        w=self.numbersControl.GetStringWidth('22')+6
        itemDetails = (commctrl.LVCFMT_LEFT, w, '', 0)
        self.numbersControl.InsertColumn(0, itemDetails)

        self.SelItems=[]
        self.MoveWindow((0,0,self.size[0],self.size[1]))
        self.CenterWindow()
        size = self.GetWindowRect()
        self.LayoutControls(size[2]-size[0], size[3]-size[1])
                 
        self.FillList()
        #Select First Item
        self.itemsControl.SetItemState(0,commctrl.LVNI_SELECTED+commctrl.LVNI_FOCUSED,255)

        #ShowWindow(win32con.SW_RESTORE)
        try:
            parent=win32ui.GetMainFrame()
        except:
            parent=None
        if parent: parent.ShowWindow(win32con.SW_RESTORE)
        return rc

    def ItemHeight(self):
        try:
            (x0,y0,x1,y1)=self.itemsControl.GetItemRect(1,0)
            return 3+y1-y0
        except:
            return 20

    def NItemsVisible(self):
        itemsLeft=self.itemsControl.GetItemCount()-self.itemsControl.GetTopIndex()
        return min(self.itemsControl.GetCountPerPage(),itemsLeft)
        
    def LayoutControls(self, w, h):
        nw=self.numbersControl.GetColumnWidth(0)
        self.itemsControl.MoveWindow((4+nw,15,w-2,h-30))
        self.numbersControl.MoveWindow((2,15+self.ItemHeight(),2+nw,h-(30)))
        NItems=self.NItemsVisible()
        self.numbersControl.DeleteAllItems()        
        for i in range(1,NItems+1):
            self.numbersControl.InsertItem(i, '%2i'%i, 0)
        self.butCancel.MoveWindow((w-60, h-24, w-10, h-4))
        self.butOK.MoveWindow((w-120, h-24, w-70, h-4))

    def on_size (self, params):
        lparam = params[3]
        w = win32api.LOWORD(lparam)
        h = win32api.HIWORD(lparam)
        self.LayoutControls(w, h)

    def selectVisibleAtIndex(self,index,add=0):
        if not add:
            current=self.SelItems[:]
            for i in current:
                self.itemsControl.SetItemState(i,0,commctrl.LVNI_SELECTED+commctrl.LVNI_FOCUSED)
        selectAt=self.itemsControl.GetTopIndex()+index-1
        self.itemsControl.SetItemState(selectAt,commctrl.LVNI_SELECTED+commctrl.LVNI_FOCUSED,255)
        self.itemsControl.EnsureVisible(selectAt, 0)
        self.itemsControl.SetFocus()

    def setCurrentAtTop(self):
        currentItems=self.SelItems[:]
        currentItems.sort()
        #for multiple selection set the first at the top, if it fits
        if (currentItems[-1]-currentItems[0])<self.itemsControl.GetCountPerPage():
            item=currentItems[0]
        else: #otherwise take the last one added
            item=self.SelItems[-1]
        bottom=item+self.itemsControl.GetCountPerPage()
        bottom=min(bottom,self.itemsControl.GetItemCount())
        self.itemsControl.EnsureVisible(bottom, 0)
        self.itemsControl.EnsureVisible(item, 0)
        self.itemsControl.SetFocus()

    def EndDialog(self, rc):
        self.StoreSelection()
        self._obj_.EndDialog(rc)
        return

    def StoreSelection(self):
        self.Selection=[]
        for i in self.SelItems:
            self.Selection.append(self.items[i])

    def OnOK(self):
        #self.setCurrentAtTop()
        #self.selectVisibleAtIndex(5)
        self.StoreSelection()
        self._obj_.OnOK()


class MultiListDialog(ListDialog):
    def __init__(self, title, List, colHeadings = None, size=(300,200,None), okButton='OK', resize=None):
        ListDialog.__init__(self, title, List, size=size[0:2],okButton=okButton, resize=resize)
        self.RefList = List
        if len(size)>2:
            self.colWidths=size[2]
        else:
            self.colWidths=None
        if colHeadings:
            self.colHeadings = colHeadings
        else:
            self.colHeadings = []
            for i in range(1,len(List[0])+1):
                self.colHeadings.append('item '+str(i))

    def StoreSelection(self):
        self.Selection=[]
        for i in self.SelItems:
            self.Selection.append(self.RefList[i][0])
        
    def FillList(self):
        index = 0
        size = self.GetWindowRect()
        width = size[2] - size[0] - (10) - win32api.GetSystemMetrics(win32con.SM_CXVSCROLL)
        numCols = len(self.colHeadings)        
        if self.colWidths:
            colw=self.colWidths
        else:
            colw=[0.20]
            for i in range(1,numCols): colw.append((1-colw[0])/(numCols-1))
        for col in self.colHeadings:
            itemDetails = (commctrl.LVCFMT_LEFT, width*colw[index], col, 0)
            self.itemsControl.InsertColumn(index, itemDetails)
            index = index + 1
        index = 0
        for items in self.items:
            #preceding spaces are stripped to facilitate list completion            
            itemText=str(items[0]).lstrip()
            index = self.itemsControl.InsertItem(index+1, itemText, 0)
            for itemno in range(1,numCols):
                item = items[itemno]
                self.itemsControl.SetItemText(index, itemno, str(item))


#############global functions######################
# def caseIndependentSort(something, other):
#     something, other= repr(something).lower(),repr(other).lower()
#     return cmp(something, other)
    
def BuildDlgList(Refs,reverse=0):
# takes a dictionary and builds a list with tuples for listcontrol construction
# first the key, then the value
    RL = []
    RefKeys=list(Refs.keys())
    if not reverse: RefKeys.sort(key=str.lower)
    for x in RefKeys:
        if reverse:
            RL.append((Refs[x],x))
        else:
            RL.append((x,Refs[x]))
    if reverse: RL.sort(key=str.lower)            
    return RL


defaultSize=(400,200)
#Globally define request id's 
RQID_References=1
RQID_Symbols=2
RQID_TCom=3
RQID_TEnv=4
RQID_FVarList=5
RQID_FVar=6
RQID_FRoutineList=7
RQID_FRoutine=8
RQID_FFunctionList=9
RQID_FFunction=10
RQID_FStatementList=11
RQID_FStructureList=12
RQID_FIntrinsicList=13
RQID_FAttributeList=14
RQID_FOperatorList=15
RQID_FParameterList=16
RQID_FModuleList=17


# QHQH
RequestFileName=dataDirectory+'\\request.bin'
ResultFileName=dataDirectory+'\\result.bin'

def DumpData(Data,FileName):
    File=open(FileName,'w')
    pickle.dump(Data, File)
    File.close()

def GetDumpedData(FileName):
    try:
        File=open(FileName,'r')
    except:
        return None
    Data=pickle.load(File)
    File.close()
    return Data


def DeferredSelectFromListDialog(List, Titles, defer, size=defaultSize):
    import natlink
    DumpData((List, Titles, defer, size), RequestFileName)
    SetMic('off')
    AppBringUp('Server',Exec=PythonServerExe,Args='/app DialogServer.py /listdialog')
    time.sleep(2)
    #try:
    #    print 3
    #does no longer generate an error when Serverapp not running? DNS 5?
    natlink.recognitionMimic(['Request','List','Dialog']) 
    #    print 32
    #except:
    #    print 4
    #    AppBringUp('Server',Exec=PythonServerExe,Args='/app DialogServer.py /listdialog')
    #    SetMic('on')                


def SelectFromListDialog(List, Titles, size=defaultSize, defer=None):
    if defer:
        r=GetDumpedData(ResultFileName)
##        if r and (r[0]==defer[1]):
##            os.remove(ResultFileName)
##            SetMic('on')
##            return r[1]
##        else:
        DeferredSelectFromListDialog(List, Titles, defer, size=size)
        return None
    dlg = MultiListDialog(str(Titles[0]), List, colHeadings=Titles[1:], size=size, resize=1)
    #SwitchToDD()        
    r=dlg.DoModal()
    #SwitchToNat()        
    if r==win32con.IDOK:
        return dlg.Selection
    return None

def SelectFromDictionary(Dictionary, Titles, size=defaultSize, reverse=0, defer=None):
    return SelectFromListDialog(BuildDlgList(Dictionary, reverse), Titles, size=size, defer=defer)


def ExtractofDictionary(Indices, Keys, Dictionary):
    Selected={}
    for i in Indices: Selected[Keys[i]]=Dictionary[Keys[i]]
    return Selected

def SelectFromPartDictionary(Indices, Keys, Dictionary, Titles, size=defaultSize, reverse=0, defer=None):
    Extracted=ExtractofDictionary(Indices, Keys, Dictionary)
    return SelectFromDictionary(Extracted, Titles, size=size, reverse=reverse, defer=defer)



def test2():
##    import D_TeX
##    RefList = BuildDlgList(D_TeX.Refs)
##  multilist from strange dictionary, example taken up by Quintijn
    import D_
    RefList = BuildDlgList(D_.Directories)
    dlg = MultiListDialog('Select', RefList, size=(400,200),okButton='Train', resize=1)
    if dlg.DoModal()==win32con.IDOK:
        return dlg.Selection
    return None

def test():
##    List=[(1),(2),(3),(4),(5)]#,(6),(7),(8),(9),(10),(11)]
    List=["foo", "bar two", "eggs three", "times four"]
    dlg = MultiListDialog('Select Special Grammars', List, 'Grammar')
    if dlg.DoModal()==win32con.IDOK:
        return dlg.Selection
    return None

def test_natspeak_on():
    #result = SelectFromListDialog(["foo","bar"], ["title 1", "title 2"], defer=1)
    result = SelectFromListDialog([["foo",1],["bar",2]], ["window title","title 1", "title 2"], defer=0)

def test_folders_list():
    """only display, background"""
    List=[r"C:\natlink\\unimacro", r"C:\documenten"]
    dlg = MultiListDialog('Say "recent file #"', List, ['directory'])
    hndle = dlg.CreateWindow()
    print('hnlde: %s'% hndle)

if __name__=='__main__':
    print(test())
