# (unimacro - natlink macro wrapper/extensions)
# (c) copyright 2003 Quintijn Hoogenboom (quintijn@users.sourceforge.net)
#                    Ben Staniford (ben_staniford@users.sourceforge.net)
#                    Bart Jan van Os (bjvo@users.sourceforge.net)
#
# This file is part of a SourceForge project called "unimacro" see
# http://unimacro.SourceForge.net).
#
# "unimacro" is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License, see:
# http://www.gnu.org/licenses/gpl.txt
#
# "unimacro" is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; See the GNU General Public License details.
#
# "unimacro" makes use of another SourceForge project "natlink",
# which has the following copyright notice:
#
# Python Macro Language for Dragon NaturallySpeaking
#   (c) Copyright 1999 by Joel Gould
#   Portions (c) Copyright 1999 by Dragon Systems, Inc.
#
# June 2020: adapt for python3, Quintijn Hoogenboom
# Author: Bart Jan van Os, Version: 1.0
"""This file implements a dialog/window to browse and train NatLink
grammars

The browser is based upon a tree dialog, adapted from the hiertest demo

Note: You can only select and train items in the right pane to avoid
accidently training large collections of words

Simply start the python win gui and run this module, to see an example.
An explanation of how to use this browser with your own grammars can be
found in _grammarUtil.py, BrowseGrammar.py and natlinkutilsbj.py The
_grammarUtil module has a method for building the required grammar.bin
files.

This file is called when doing the command "Show All Grammars" from the
grammar "_control".

"""
import sys
import pickle
import win32ui
import win32con
import win32api
import commctrl
from pywin.mfc import dialog
from pywin.tools import hierlist
from pywin.framework import dlgappcore

import natlink
from natlink.natlinkutils import *
from natlinkutilsbj import SetMic,GrammarFileName
from operator import methodcaller
# hopelijk: QH
from natlinkutilsqh import getUnimacroDirectory
baseDirectory = getUnimacroDirectory()
print('baseDirectory: %s'% baseDirectory)

from BrowseGrammar import *
from listdialogs import ListDialog
import TrainDialog
import D_train


class GramHierList(hierlist.HierList):
    def __init__(self, root,Start, listBoxID = win32ui.IDC_LIST1):
        hierlist.HierList.__init__(self, root, win32ui.IDB_BROWSER_HIER, listBoxID)
        self.Start=Start

    def GetText(self, item):
        return item.GetName()
    
    def GetSubList(self, item):
        if item.GramType==RuleCode:
            InnerRules=item.GetInnerRules(0)
        else:
            InnerRules = None
        return InnerRules
    
    def IsExpandable(self, item):
        return (item.GramType==RuleCode) and not item.AreAllWords()
    
    def GetSelectedBitmapColumn(self, item):
        return self.GetBitmapColumn(item)+6 # Use different color for selection

    def TakeDefaultAction(self, item):
        # Restore original behavior :-)
        # better is to overwrite and restore original behavior of OnTreeItemDoubleClick
        if self.IsExpandable(item):
            self.Expand(self.GetSelectedItem(),commctrl.TVE_TOGGLE)

    def OpenNext(self,root,i,RulePath):
        if i<len(RulePath):
            for o in root.Included:
                if not IsText(o):
                    if id(o)==id(RulePath[i]):
                        if self.IsExpandable(o):
                            self.Expand(self.GetHandleOf(o),commctrl.TVE_EXPAND)                        
                        if i==len(RulePath)-1:
                            self.SelectItem(self.GetHandleOf(o))                            
                        else:
                            self.OpenNext(o,i+1,RulePath)

    def OpenRule(self,RulePath):
        self.OpenNext(self.root,0,RulePath)

    def OpenStart(self):
        if len(self.Start)==2:
            Rule,Path,objPath=self.root.FindRulePath(self.Start)
            for o in objPath:
                if not IsText(o):
                    self.OpenRule(objPath)

    def GetHandleOf(self,item):
        HandlesFor=InverseDict(self.itemHandleMap)
        if item in HandlesFor:
            return HandlesFor[item]
        else:
            return None


IDC_EDIT=1000
IDC_SYNTAX=1010
IDC_TRAIN=1011
IDC_TRAINSPECIAL=1012
IDC_EDITITEM=1013
IDC_NEWITEM=1014

class GrammarDialog(dialog.Dialog):
#    def __init__(self, title, hierList, bitmapID = win32ui.IDB_HIERFOLDERS, dlgID = win32ui.IDD_TREE, dll = None, childListBoxID = win32ui.IDC_LIST1):
    def __init__(self, title, hierList):
        dialog.Dialog.__init__ (self, self._maketemplate(title))
        self.hierList=hierList
        self.colHeadings=['Name','Definition']
        self.items=[]
        self.LastFocused=0
        self.SyntaxItem=0

    def _maketemplate(self,title):
        style = (win32con.WS_DLGFRAME | win32con.WS_MAXIMIZEBOX |
                win32con.WS_MINIMIZEBOX | win32con.WS_SIZEBOX |
                win32con.WS_SYSMENU | win32con.WS_VISIBLE |
                 win32con.WS_EX_TOPMOST 
                 )
        cs = (win32con.WS_CHILD           | win32con.WS_TABSTOP |
            win32con.WS_VISIBLE         | commctrl.CCS_NOMOVEY |
            commctrl.TVS_HASLINES       | commctrl.TVS_SHOWSELALWAYS |
            commctrl.TVS_LINESATROOT    | win32con.WS_BORDER |
            commctrl.TVS_HASBUTTONS)
        ls = (
            win32con.WS_CHILD           | win32con.WS_BORDER |
            win32con.WS_VISIBLE         | win32con.WS_TABSTOP |
            commctrl.LVS_ALIGNLEFT      |
            commctrl.LVS_REPORT         | LVS_EDITLABELS
            )
        t = [ [title, (0, 0, 500, 300), style, None, (8, "MS Sans Serif")],
            ["SysTreeView32", None, win32ui.IDC_LIST1, (0, 0, 1, 1), cs],
            ["SysListView32", None, IDC_SYNTAX, (0, 0, 1, 1), ls],
            ]
        return t

    #(only for DlgAppCore)
    def PreDoModal(self):
        sys.stdout = sys.stderr = self


    def OnInitDialog(self):
        self.CenterWindow()                    
        self.hierList.HierInit(self)
        rc=dialog.Dialog.OnInitDialog(self)
        self.HookMessage (self.on_size, win32con.WM_SIZE)
        self.HookNotify(self.SyntaxItemChange, commctrl.LVN_ITEMCHANGED)
        self.HookNotify(self.TreeItemChange, commctrl.TVN_SELCHANGED)
        self.HookNotify(self.GotFocus, commctrl.NM_SETFOCUS)
        self.HookCommand(self.OnSyntaxClick, IDC_SYNTAX)
        self.Tree = self.GetDlgItem(win32ui.IDC_LIST1)
        self.Syntax = self.GetDlgItem(IDC_SYNTAX)
        self.FillList()
        size = self.GetWindowRect()
        self.LayoutControls(size[2]-size[0], size[3]-size[1])
        self.hierList.OpenStart()
        self.SetFocus()
        return rc

    def ExpandSyntaxItem(self,ItemNr):
        Item=self.items[ItemNr]
        Name=Item[0]
        State=self.Syntax.GetItemState(ItemNr,commctrl.LVIS_SELECTED)        
        if (Name!='<SpokenForm>') and (Name!='<Syntax>') and (State!=0):
            # force parent Tree item to expand, adding the sublist to the itemHandle map
            hItem=self.hierList.GetSelectedItem()
            oItem=self.hierList.ItemFromHandle(hItem)            
            if self.hierList.IsExpandable(oItem):
                self.hierList.Expand(hItem,commctrl.TVM_EXPAND)
            # If it exists, select the Tree item corresponding to the Syntax item
            h=self.hierList.GetHandleOf(Item[2])
            if h: self.Tree.SelectItem(h)

    def OnSyntaxClick(self, id, code):
        if code==commctrl.NM_DBLCLK:
            self.ExpandSyntaxItem(self.SyntaxItem)
        return 1

    def OnOK(self):
        if (self.LastFocused==IDC_SYNTAX):
            self.ExpandSyntaxItem(self.SyntaxItem)

    def GotFocus(self,std, extra):
        (hwndFrom, idFrom, code)= std
        self.LastFocused=idFrom

    def on_size (self, params):
        lparam = params[3]
        w = win32api.LOWORD(lparam)
        h = win32api.HIWORD(lparam)
        self.LayoutControls(w, h)
    
    def LayoutControls(self, w, h):
        d=w/4
        self.Tree.MoveWindow((0,0,d,h))
        self.Syntax.MoveWindow((d,0,w,h))

    def SyntaxItemChange(self,std, extra):
        (hwndFrom, idFrom, code), (itemNotify, sub, newState, oldState, change, point, lparam) = std, extra
        oldSel = (oldState & commctrl.LVIS_SELECTED)!=0
        newSel = (newState & commctrl.LVIS_SELECTED)!=0
        if oldSel != newSel:
            self.SyntaxItem=itemNotify


    def SetRuleItems(self,Rule,InnerRules):
        IsGrammar=Rule.IsRuleContainer()
        FoldedContents=Rule.GetContents(1,Unfold=0)
        IsSimple=Rule.AreAllWords(FoldedContents)
        Items=[]
        if not (IsGrammar or IsSimple): Items.append(('<Syntax>',FoldedContents,Rule))
        for IR in InnerRules:
            if IR.IsAltOrList():
                Items.append((IR.GetName(),IR.GetContents(1,Unfold=1),IR))
            else:
                Items.append((IR.GetName(),IR.GetContents(1,Unfold=0),IR))
        if not IsGrammar:
            Items.append(('<SpokenForm>',Rule.GetContents(2,Unfold=1),Rule))
        self.items=Items

    def SetAlternativesItems(self,Rule,InnerRules):
        Items=[]
        Alternatives=Rule.Included
        Alternatives.sort(key=str.lower)
        IgnoreBracketsParen=re.compile('\[|\]|\(|\)')        
        for a in Alternatives:
            s=a.strip()
            s=IgnoreBracketsParen.sub('',s)
            if s in Rule.AlternativesDict:
                Items.append((s,Rule.AlternativesDict[s],Rule,1))
            else:
                Items.append((s,'',Rule,1))
        self.items=Items


    def SetListItems(self,Rule):
        Items=[]
        Elements=Rule.Included
        Elements.sort(key=str.lower)
        for a in Elements:
            if a in Rule.AlternativesDict:
                Items.append((a,Rule.AlternativesDict[a],Rule,1))
            else:
                Items.append((a,'',Rule,1))
        if Elements==[]:
            Items.append(('{Unknown list items}','',Rule))
        self.items=Items
        
        
    def TreeItemChange(self,std, extra):
        hwndFrom, idFrom, code=std
        Action,ItemOld,ItemNew,Point=extra
        Rule=self.hierList.ItemFromHandle(self.Tree.GetSelectedItem())
        InnerRules=Rule.GetInnerRules(0)
        if Rule.GramType==RuleCode:
            self.SetRuleItems(Rule,InnerRules)
        elif Rule.IsLongAlternative():
            self.SetAlternativesItems(Rule,InnerRules)
        elif Rule.GramType==ListCode:
            self.SetListItems(Rule)
        else:
            pass
        self.InsertItems()
       

    def InsertItems(self):
        self.Syntax.DeleteAllItems()
        index=0
        for items in self.items:
            index = self.Syntax.InsertItem(index+1, str(items[0]), 0)
            for itemno in range(1,len(self.colHeadings)):
                item = items[itemno]
                self.Syntax.SetItemText(index, itemno, str(item))
        try:
            self.Syntax.SetItemState(0, commctrl.LVIS_FOCUSED+commctrl.LVNI_SELECTED, 255)
        except:
            pass
        
    def FillList(self):
        size = self.GetWindowRect()
        width = 2*(size[2] - size[0])/3 - win32api.GetSystemMetrics(win32con.SM_CXVSCROLL)
        colw=[0.35,2.80]
        numCols = len(self.colHeadings)
        index = 0
        for col in self.colHeadings:
            itemDetails = (commctrl.LVCFMT_LEFT, width*colw[index], col, 0)
            self.Syntax.In
            sertColumn(index, itemDetails)
            index = index + 1
        index = 0


class TrainGrammarDialog(GrammarDialog):
#    def __init__(self, title, hierList, bitmapID = win32ui.IDB_HIERFOLDERS, dlgID = win32ui.IDD_TREE, dll = None, childListBoxID = win32ui.IDC_LIST1):
    def __init__(self, title, hierList):
        dialog.Dialog.__init__ (self, self._maketemplate(title))
        self.hierList=hierList
        self.colHeadings=['Name','Definition']
        self.items=[]
        self.LastFocused=0
        self.SelItems=[]
        

    def _maketemplate(self,title):
        style2 = win32con.WS_OVERLAPPEDWINDOW | win32con.WS_VISIBLE        
        style = (win32con.WS_DLGFRAME | win32con.WS_MAXIMIZEBOX |
                win32con.WS_MINIMIZEBOX | win32con.WS_SIZEBOX |
                win32con.WS_SYSMENU | win32con.WS_VISIBLE |
                 win32con.SW_SHOW | win32con.WS_EX_TOPMOST 
                 )
        child = win32con.WS_CHILD | win32con.WS_VISIBLE
        cs = (child           |
            win32con.WS_TABSTOP         | commctrl.CCS_NOMOVEY |
            commctrl.TVS_HASLINES       | commctrl.TVS_SHOWSELALWAYS |
            commctrl.TVS_LINESATROOT    | win32con.WS_BORDER |
            commctrl.TVS_HASBUTTONS)
        ls = (
            win32con.WS_CHILD           | win32con.WS_BORDER |
            win32con.WS_VISIBLE         | win32con.WS_TABSTOP |
            commctrl.LVS_ALIGNLEFT      |
            commctrl.LVS_REPORT         | commctrl.LVS_EDITLABELS
            )
        bs = (
            win32con.WS_CHILD           |
            win32con.WS_VISIBLE
             )
        t = [ [title, (0, 0, 500, 300), style, None, (8, "MS Sans Serif")],
            ["SysTreeView32", None, win32ui.IDC_LIST1, (0, 0, 1, 1), cs],
            ["SysListView32", None, IDC_SYNTAX, (0, 0, 1, 1), ls],
            [128, "Exit", win32con.IDCANCEL, (10, 0, 50, 14), bs ],
            [128, "Train Special", IDC_TRAINSPECIAL, (10, 0, 50, 14), bs ],                                          
            [128, "&Train", IDC_TRAIN, (10, 0, 50, 14), bs | win32con.BS_PUSHBUTTON],
            [128, "&Edit", IDC_EDITITEM, (10, 0, 50, 14), bs ],              
            [128, "&New", IDC_NEWITEM, (10, 0, 50, 14), bs ],              
            [129,"",IDC_EDIT,(7,72,250,85),child|win32con.ES_MULTILINE|win32con.WS_BORDER|
                    win32con.ES_AUTOVSCROLL|win32con.WS_VSCROLL],
            ]
        return t

    def OnInitDialog(self):
        self.CenterWindow()                    
        self.hierList.HierInit(self)
        rc=dialog.Dialog.OnInitDialog(self)
        self.HookMessage (self.on_size, win32con.WM_SIZE)
        self.HookNotify(self.SyntaxItemChange, commctrl.LVN_ITEMCHANGED)
        self.HookNotify(self.TreeItemChange, commctrl.TVN_SELCHANGED)
        self.HookNotify(self.GotFocus, commctrl.NM_SETFOCUS)
        self.HookCommand(self.OnSyntaxClick, IDC_SYNTAX)
        self.HookCommand(self.onTrain, IDC_TRAIN)
        self.HookCommand(self.onTrainSpecial, IDC_TRAINSPECIAL)
        self.HookCommand(self.onNew, IDC_NEWITEM)
        self.HookCommand(self.onEdit, IDC_EDITITEM)
        self.Tree = self.GetDlgItem(win32ui.IDC_LIST1)
        self.Syntax = self.GetDlgItem(IDC_SYNTAX)
        self.butTrainSpecial = self.GetDlgItem(IDC_TRAINSPECIAL)
        self.butTrain = self.GetDlgItem(IDC_TRAIN)
        self.butCancel = self.GetDlgItem(win32con.IDCANCEL)
        self.butEdit = self.GetDlgItem(IDC_NEWITEM)
        self.butNew = self.GetDlgItem(IDC_EDITITEM)        
        self.Output= self.GetDlgItem(IDC_EDIT)
        self.oldStdout = sys.stdout        
        sys.stdout = self
        self.message = ''
        
        self.FillList()
        size = self.GetWindowRect()
        self.LayoutControls(size[2]-size[0], size[3]-size[1])
        self.hierList.OpenStart()
        self.SetFocus()
        rc=GrammarDialog.OnInitDialog(self)
        return rc

    def OnDestroy(self,msg):
        sys.stdout = self.oldStdout
    
    def write(self,text):
        self.message = self.message + text.replace('\n','\r\n')
        self.SetDlgItemText(IDC_EDIT,self.message)
        self.GetDlgItem(IDC_EDIT).SendMessage(win32con.EM_SETSEL,0x7FFF,0x7FFF)
        self.GetDlgItem(IDC_EDIT).SendMessage(win32con.EM_SCROLLCARET,0,0)

    def LayoutControls(self, w, h):
        d=w//4
        self.Tree.MoveWindow((0,0,d,h-100))
        self.Syntax.MoveWindow((d,0,w,h-100))
        self.Output.MoveWindow((0,h-97,w,h-30))
        self.butCancel.MoveWindow((w-60, h-24, w-10, h-4))
        self.butTrain.MoveWindow((w-120, h-24, w-70, h-4))
        self.butEdit.MoveWindow((w-180, h-24, w-130, h-4))
        self.butNew.MoveWindow((w-240, h-24, w-190, h-4))                
        self.butTrainSpecial.MoveWindow((10, h-24, 90, h-4))

    def GotFocus(self,std, extra):
        (hwndFrom, idFrom, code)= std
        self.LastFocused=idFrom
        if idFrom==IDC_SYNTAX:
            self.butTrain.EnableWindow(1)
            self.butEdit.EnableWindow(0)
            self.butNew.EnableWindow(0)            
        else:
            self.butTrain.EnableWindow(0)
            self.butEdit.EnableWindow(0)
            self.butNew.EnableWindow(0)            
            

    def SyntaxItemChange(self,std, extra):
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
            except win32ui.error:
                self.SelItems=[]

    def OnSyntaxClick(self, id, code):
        if code==commctrl.NM_DBLCLK:
            if len(self.SelItems)==1:
                self.ExpandSyntaxItem(self.SelItems[0])
        return 1

    def InsertItems(self):
        GrammarDialog.InsertItems(self)
        self.SelItems=[0]

    def OnOK(self):
        if (self.LastFocused==IDC_SYNTAX):
            if len(self.SelItems)==1:
                self.ExpandSyntaxItem(self.SelItems[0])

    def GetTextChunks(self):
        InnerRules=[]
        ToTrain=[]
        Rule=self.items[0][2]
        for Nr in self.SelItems:
            if len(self.items[Nr])>3:
                ToTrain.append(self.items[Nr][0])
            else:
                Rule=self.items[Nr][2]
                InnerRules.append(Rule)
                InnerRules.extend(Rule.GetInnerRules(10))
        InnerRules=Rule.RemoveDuplicates(InnerRules)
        for Rule in InnerRules:
            ToTrain.extend(Rule.GetTextChunks())
        ToTrain.sort(key=str.lower)
        RemoveDuplicatesOfSortedList(ToTrain)
        if ToTrain[0]=='<imported>': ToTrain.remove('<imported>')
        return ToTrain
    

    def onTrain(self,nID,code):
        #natlink.recognitionMimic(['Print','Module','Info'])
        #return
        if (self.LastFocused==IDC_SYNTAX) and len(self.SelItems)>0:
            Name1=self.items[self.SelItems[0]][0]
            if (Name1!='<Syntax>'):
                ToTrain=self.GetTextChunks()
                self.goTrain(ToTrain)

    def onTrainSpecial(self,nID,code):
        return  ## just disable...
        Names=[]
        Keys=list(D_train.SpecialTraining.keys())
        for name in Keys:
            Names.append((name))
        (x,y)=natlink.getScreenSize()
        Size=(int(x*0.20),int(y*0.30))
        dlg = ListDialog('Select Special Training', Names, 'Grammar',size=Size,okButton='Train')
        if dlg.DoModal()==win32con.IDOK:
            Selection=dlg.Selection
            ToTrain=[]
            for k in Selection:
                ToTrain.extend(D_train.SpecialTraining[k])
            ToTrain.sort(key=str.lower)
            RemoveDuplicatesOfSortedList(ToTrain)
            self.goTrain(ToTrain)

    def onNew(self,nID,code):
        pass

    def onEdit(self,nID,code):
        pass
        return
        if (self.LastFocused==IDC_SYNTAX):
            if len(self.SelItems)==1:
                print(self.SelItems[0])
                self.EditControl=self.Syntax.EditLabel(0)
                #self.Syntax.SetFocus()
                #self.Syntax.EditLabel(self.SelItems[0])        
    

    def goTrain(self,ToTrain):
        Title='Train Phrases'
        Phrases=[]
        for p in ToTrain:
            Phrases.append((p))
        try:
            natlink.natConnect(1)
        except:
            return
        MicState=natlink.getMicState()
        dlg=TrainDialog.TrainDialog(Title,Phrases,MicState)
        SetMic('off')
        dlg.DoModal()
        natlink.natDisconnect()    

                        
class BrowseDialogApp(dlgappcore.DialogApp):
    "BJ added: An application class, for an app with main dialog box"
    def InitInstance(self):
#       win32ui.SetProfileFileName('dlgapp.ini')
#        win32ui.LoadStdProfileSettings()
        win32ui.EnableControlContainer()
        win32ui.Enable3dControls()
        self.dlg = self.frame = self.CreateDialog()
        if self.frame is None:
            raise error("No dialog was created by CreateDialog()")
            return
        self.PreDoModal()
        self.dlg.PreDoModal()
        self.dlg.DoModal()
        self.PostDoModal()
    
    def CreateDialog(self):
        return CreateBrowseDialog()

    def PreDoModal(self):
        pass
        #natlink.natConnect(1) #presently handled in TrainDialog

    def PostDoModal(self):
        pass
        #natlink.natDisconnect()

def CreateBrowseDialog():
    try:
        GrammarFile=open(GrammarFileName,'rb')
    except:
        GrammarFile=open(baseDirectory+'\\TestGrammar.bin','rb')
    (Grammars,Start,All,Exclusive)=pickle.load(GrammarFile)
    GrammarFile.close()
    Grammars.Sort()
    if Exclusive: Name='Exclusive Grammars (Active Rules)'
    elif All: Name='All Grammars'
    else:   Name='Active Grammars'
    # dlg=GrammarDialog(Name,GramHierList(Grammars,Start))
    dlg=TrainGrammarDialog(Name,GramHierList(Grammars,Start))
    return dlg


def demomodeless():
    dlg=CreateBrowseDialog()
    dlg.CreateWindow()

def demodlg ():
    dlg=CreateBrowseDialog()    
    dlg.DoModal()


def CheckCreateApp():
    if "pywin.framework.startup" in sys.modules:
        App=BrowseDialogApp()


if __name__=='__main__':
    pass
    demodlg()
    #demomodeless()
else:
    CheckCreateApp()