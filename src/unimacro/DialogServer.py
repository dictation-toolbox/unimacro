# This file implements a crude Training dialog to Train phrases
# Author: Bart Jan van Os, Version: 0.1
# adapted by QH, july 2006
# starts a process (copy of pythonwin) to implement choice lists

import sys
import pickle
import os.path

import win32ui
import win32con
import win32api
import commctrl
from pywin.mfc import dialog
from pywin.tools import hierlist
from pywin.framework import dlgappcore

import natlink
from natlink.natlinkutils import *
from natlinkutilsbj import SetMic
import listdialogs
import D_

RequestFileName=listdialogs.RequestFileName
ResultFileName=listdialogs.ResultFileName

# hopelijk: QH
from natlinkutilsqh import getUnimacroDirectory
baseDirectory = getUnimacroDirectory()


IDC_EDIT=1000
IDC_LD=1010


def Wait(t):
    time.sleep(t)

class ServerGrammar(GrammarBase):


    gramSpec = """
        <ListDialog> = List Dialog;
        <Requests> = Request (<ListDialog>);
        <normalState> exported =  <Requests>;
    """

    def initialize(self,dlg):
        self.dlg = dlg
        self.load(self.gramSpec)
        self.activateSet(['normalState'],exclusive=0)


    def terminate(self):
        self.dlg = None
        self.unload()


    def gotResults_ListDialog(self,words,fullResults):
        print(natlink.getCallbackDepth())
        print('Request List Dialog')
        win32ui.GetMainFrame().PostMessage(IDC_LD)
        SetMic('on')

class SelectGrammar(GrammarBase):

    selectSpec = """
        <SelectChooseItem> = (Select | Choose) {Count};
        <Spelling> = [{Special}+] [({Alpha}+ | {ICAlpha}+)];
        <normalState> exported =  <SelectChooseItem> | <Spelling>;
    """

    def initialize(self,dlg):
        self.dlg = dlg
        self.load(self.selectSpec)
        self.activateSet(['normalState'],exclusive=0)
        self.setList('Alpha',D_.Alphabet)
        self.setList('ICAlpha',D_.ICAlphabet)
        self.setList('Special',D_.SpecialCharacters)
        self.Counts=[]
        for i in range(1,100):
            self.Counts.append(str(i))
        #self.setList('Count',self.Counts)

    def terminate(self):
        self.dlg = None
        self.unload()

    def gotBegin(self, moduleInfo):
        text=self.dlg.GetWindowText()
        winHandle = matchWindow(moduleInfo, 'pserver1', text)
        if winHandle:
            self.activateAll(window=winHandle )
            NItems=self.dlg.NItemsVisible()
            self.setList('Count',self.Counts[:NItems])
        else:
            self.deactivateAll()        

    def gotResults_SelectChooseItem(self,words,fullResults):
        index=int(words[-1])
        if self.dlg:
            self.dlg.selectVisibleAtIndex(index,add=0)
            if words[0].lower()=='choose': self.dlg.OnOK()

    def gotResults_Spelling(self,words,fullResults):
        chars=''
        for w in words:
            c=w.split('\\')[0]
            if c=='':
                chars=chars+'\\'                
            else:
                chars=chars+c
        natlinkutils.playString(chars)
        if self.dlg:
            self.dlg.setCurrentAtTop()


class MainWindow(dlgappcore.AppDialog):

    def __init__ (self):
        dialog.Dialog.__init__ (self, self._maketemplate('Dialog Server'))
        self.Busy=0

    def _maketemplate(self, title):
        style = win32con.WS_DLGFRAME | win32con.WS_SYSMENU | win32con.WS_VISIBLE
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
        return [ [title, (0, 0, 200, 200), style, None, (8, "MS Sans Serif")],
            ["SysListView32", None, win32ui.IDC_LIST1, (0, 0, 200, 200), ls], 
            [128,   "OK", win32con.IDOK, (10, 0, 50, 14), bs | win32con.BS_DEFPUSHBUTTON],
            [128,   "Cancel",win32con.IDCANCEL,(110, 0, 50, 14), bs],
            ]



##        style = (win32con.WS_DLGFRAME | win32con.WS_SYSMENU  | win32con.WS_VISIBLE |
##                 win32con.WS_MINIMIZEBOX )
##        child = win32con.WS_CHILD | win32con.WS_VISIBLE
##        return [ [title, (0, 0, 200, 100), style, None, (8, "MS Sans Serif")],
##            [129,"",win32ui.IDC_EDIT1,(0,0,0,0),child|win32con.ES_MULTILINE|win32con.WS_BORDER|
##                    win32con.ES_AUTOVSCROLL|win32con.WS_VSCROLL],
##            ]

    def OnInitDialog (self):
        rc = dialog.Dialog.OnInitDialog (self)
        self.HookMessage(self.onSize, win32con.WM_SIZE)
        self.HookMessage(self.ListDialog, IDC_LD)
        self.HookCommand(self.ListDialog, IDC_LD)        
        self.Output= self.GetDlgItem(IDC_EDIT)
        #self.Output= self.GetDlgItem(win32ui.IDC_EDIT1)
        size = self.GetWindowRect()
        self.LayoutControls(size[2]-size[0], size[3]-size[1])
        self.oldStdout = sys.stdout        
        sys.stdout = self
        self.message = ''
        self.grammar = ServerGrammar()
        self.grammar.initialize(self)
        self.CenterWindow()
        self.ShowWindow(win32con.SW_MINIMIZE)
        self.executeStartRequest()
        return rc

    def executeStartRequest(self):
        if len(sys.argv)>1:
            print('Request=',sys.argv[1])
            if sys.argv[1]=='/listdialog':
                win32ui.GetMainFrame().PostMessage(IDC_LD)
        

    def OnDestroy(self,msg):
        sys.stdout = self.oldStdout
        self.grammar.terminate()
        self.grammar = None
    
    def write(self,text):
        try:
            #self.Output.SetSel(-2)
            #self.Output.ReplaceSel(regsub.gsub('\n','\r\n',text))
            self.message = self.message + text.replace('\n','\r\n')
            self.SetDlgItemText(win32ui.IDC_EDIT1, self.message)
            self.GetDlgItem(win32ui.IDC_EDIT1).SendMessage(win32con.EM_SETSEL,0x7FFF,0x7FFF)
            self.GetDlgItem(win32ui.IDC_EDIT1).SendMessage(win32con.EM_SCROLLCARET,0,0)
        except:
            win32ui.OutputDebug("dlgapp - some wrong! >>\n%s\n<<\n" % text)
        

    def LayoutControls(self, w, h):
        self.Output.MoveWindow((1,1,w-1,h-1))                

    def onSize (self, params):
        lparam = params[3]
        w = win32api.LOWORD(lparam)
        h = win32api.HIWORD(lparam)
        self.LayoutControls(w, h)

    def GetRequestData():
        try:
            RequestFile=open(RequestFileName,'r')
        except:
            RequestFile=open(baseDirectory+'\\TestRequest.bin','r')
        Data=pickle.load(RequestFile)
        GrammarFile.close()
        return Data

    def ListDialog(self,id):
        if not self.Busy:
            #now handled by list dialog: self.ShowWindow(win32con.SW_RESTORE)
            self.Busy=1
            (List, Titles, defer, size)=listdialogs.GetDumpedData(RequestFileName)
            dlg=listdialogs.MultiListDialog(Titles[0], List, colHeadings=Titles[1:], size=size, resize=1)
            grammar = SelectGrammar()
            grammar.initialize(dlg)
            r=dlg.DoModal()
            grammar.terminate()
            if r==win32con.IDOK:
                SetMic('off')
                listdialogs.DumpData((defer[1],dlg.Selection),ResultFileName)
            self.Busy=0
            self.ShowWindow(win32con.SW_MINIMIZE)
            if r==win32con.IDOK:
                try:
                    natlink.recognitionMimic(defer[0])
                except:
                    pass


            

class ServerApp(dlgappcore.DialogApp):
    "BJ added: An application class, for an app with main dialog box"
    def InitInstance(self):
        win32ui.SetProfileFileName('dlgapp.ini')
        win32ui.LoadStdProfileSettings()
        win32ui.EnableControlContainer()
        win32ui.Enable3dControls()
        self.dlg = self.frame = self.CreateDialog()
    
        if self.frame is None:
            raise error("No dialog was created by CreateDialog()")
            return

        self._obj_.InitDlgInstance(self.dlg)
        self.PreDoModal()
        self.dlg.DoModal()
        self.PostDoModal()
    
    def CreateDialog(self):
        return MainWindow()

    def PreDoModal(self):
        try:
            natlink.natDisconnect()
            natlink.natConnect(1)
        except:
            pass

    def PostDoModal(self):
        natlink.natDisconnect()



def CheckCreateApp():
    if "pywin.framework.startup" in sys.modules:
        App=ServerApp()
        App.InitInstance()
    else:
        print('does not have "pywin.framework.startup" imported')

def demodlg ():
    dlg=MainWindow()
    dlg.DoModal()


if __name__=='__main__':
    natlink.natConnect()
    demodlg()
    natlink.natDisconnect()
    #demomodeless()
else:
    CheckCreateApp()                        
