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
# Author: Bart Jan van Os, Version: 0.1
"""This file implements a crude Training dialog to Train phrases

"""

import string,sys,pickle

import win32ui,win32con,win32api,commctrl
from pywin.mfc import dialog
from pywin.framework import dlgappcore

import natlink
from natlink.natlinkutils import *
from natlinkutilsbj import SetMic


# The training dialog gives a list at the bottum with each phrase to train. After training
# is started, each phrase to train is displayed at the top, any training results
# are displayed in the control in between. If the recognized results are different from
# the phrase to train, the phrase can be trained again until
MaxRepeat=3
# is reached. If the result is correct, the next phrase will be selected.

# You can stop training at any time by 'stop training'. This stops the training process, but leaves results
# for later batch processing. Switching to another window and saying something has the same result.
# Cancel will quit the dialog without batchprocessing. NOTE: any 'results obj.correction'
# changes are processed immediately, before possible quitting.
# Choosing Done will start processing the results in the batch training mode, and leave the dialog. 
# You can use ' skip phrase' or ' previous phrase' to go forth and back through the phrases to train,
# as wel as use the mouse/keyboard in the list at the bottom.

## Be careful with using this training process.  Because it uses the batch training
## mode,(I presume) it also affects the acoustic models. One may question whether
## the words to be trained are a good representation of your use of the system,
## and you have to be sure that the words are in your vocabulary.
## In the end, general training is probably much better for changing the acoustic
## models. However, it has helped me to train a lot of
## often misrecognized commands without having to type them.  I always do some
## general training afterwards.  Possibly, training mode should be changed to
## only use the obj.correction method.
## This can be accomplished by setting the next constant to zero.
TrainInBatchMode=1


# Things to do:
# - add a control for selecting the training mode.define method
# - add a control for selecting the maximum repeat count.

class TrainDialogGrammar(GrammarBase):


    gramSpec = """
        <dgndictation> imported;        #This must be the first rule      
        <TrainedWord> = {TrainedWord};  #This must be the second rule      
        <ChangePhrase> = previous phrase | skip phrase;
        <Buttons> = (start [training]| (stop|cancel) [training | this] | done );
        <TrainButtons> = click stop | click done | click cancel | ((stop |cancel) (training | this));
        <normalState> exported =  <Buttons>;
        <trainingState> exported =   <TrainButtons> | <ChangePhrase> |
                                     <TrainedWord> | <dgndictation>;
    """

    def initialize(self,dlg):
        self.dlg = dlg
        self.load(self.gramSpec,allResults=1)
        self.thisWindow=dlg.GetSafeHwnd()
        self.emptyList('TrainedWord')

    def terminate(self):
        self.dlg = None
        self.unload()

    def setMode(self):
        if not self.dlg.AreTraining:
            #self.activateSet(['normalState'],window=self.thisWindow,exclusive=0)
            self.activateSet(['normalState'],exclusive=0)
        else:
            self.activateSet(['trainingState'],exclusive=1)

    def gotBegin(self, moduleInfo):
        winHandle = matchWindow( moduleInfo, 'pythonw', 'Train Phrases' )
        if winHandle:
        #if winHandle==self.thisWindow:
            self.setMode()
        else:
            self.deactivateAll()
            if self.dlg.AreTraining: self.dlg.onStop(0,0)


# This processes the results within the training mode
    def gotResultsTraining(self,recogType,resObj):
        if recogType == 'reject':
            print('rejected')
        else:
            results= convertResults(resObj.getResults(0))
            rule=list(results.keys())[0]
            #print results.keys()
            if (rule<=2):
                self.dlg.trainedPhrases.append((resObj,self.dlg.phrase))
                results=' '.join(resObj.getWords(0))
                print(results)

                #go next or repeat
                lowResults=results.lower()
                lowSpokenForm=lowResults.split('\\')[-1]
                lowPhrase=self.dlg.phrase.lower()
                if (lowResults==lowPhrase) or (lowSpokenForm==lowPhrase):
                    self.dlg.nextWord()
                else:
                    self.dlg.Repeat=self.dlg.Repeat+1
                    if self.dlg.Repeat>MaxRepeat:
                        self.dlg.nextWord()
        

    # this callback is where we get the results object
    def gotResultsObject(self,recogType,resObj):
        if self.dlg.AreTraining:
            self.gotResultsTraining(recogType,resObj)

    def gotResults_Buttons(self,words,fullResults):
        if 'done' in words:
            key='{Alt+d}'
        elif 'start' in words:
            key='{Alt+s}'
        elif 'cancel' in words:
            key='{Alt+c}'
        elif 'stop' in words:
            key='{Alt+p}'
        natlinkutils.playString(key)

    def gotResults_TrainButtons(self,words,fullResults):
        self.gotResults_Buttons(words,fullResults)

    def gotResults_ChangePhrase(self,words,fullResults):
        if 'previous' in words:
            key='{Up}'
        elif 'skip' in words:
            key='{Down}'
        natlinkutils.playString(key)



IDC_EDIT=1000
IDC_PHRASE=1010
IDC_START=1011
IDC_STOP=1012


class TrainDialog(dialog.Dialog):
#    def __init__(self, title, hierList, bitmapID = win32ui.IDB_HIERFOLDERS, dlgID = win32ui.IDD_TREE, dll = None, childListBoxID = win32ui.IDC_LIST1):

    def __init__ (self, title, phrases, MicStart):
        #self.iconId = win32ui.IDR_MAINFRAME
        dialog.Dialog.__init__ (self, self._maketemplate(title))
        self.colHeadings=['Phrase']
        self.items = phrases
        self.MicStart=MicStart
        self.AreTraining=0
        self.CurItem=0
        self.phrase=''
        self.Repeat=0
        self.Batch=0

    def _maketemplate(self, title):
        style = (win32con.WS_DLGFRAME | 
                win32con.WS_SYSMENU | win32con.WS_VISIBLE )
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
        child = win32con.WS_CHILD | win32con.WS_VISIBLE
        return [ [title, (0, 0, 200, 200), style, None, (8, "MS Sans Serif")],
            ["SysListView32", None, win32ui.IDC_LIST1, (0, 0, 450, 200), ls],
            [128,   "&Start", IDC_START, (10, 0, 50, 14), bs | win32con.BS_DEFPUSHBUTTON],
            [128,   "Sto&p", IDC_STOP, (10, 0, 50, 14), bs ],                 
            [128,   "&Done", win32con.IDOK, (10, 0, 50, 14), bs],
            [128,   "&Cancel",win32con.IDCANCEL,(0, 0, 450, 200), bs],
            [129,"",IDC_EDIT,(0,0,0,0),child|win32con.ES_MULTILINE|win32con.WS_BORDER|
                    win32con.ES_AUTOVSCROLL|win32con.WS_VSCROLL],
            [130,"",IDC_PHRASE,(7,60,80,8),child|win32con.SS_LEFT],                 
            ]

    def OnInitDialog (self):
        rc = dialog.Dialog.OnInitDialog (self)
        self.HookMessage (self.on_size, win32con.WM_SIZE)
        self.HookNotify(self.OnListItemChange, commctrl.LVN_ITEMCHANGED)
        self.HookCommand(self.onStart, IDC_START)
        self.HookCommand(self.onStop, IDC_STOP)        
        self.itemsControl = self.GetDlgItem(win32ui.IDC_LIST1)
        self.butOK = self.GetDlgItem(win32con.IDOK)
        self.butCancel = self.GetDlgItem(win32con.IDCANCEL)
        self.butStart = self.GetDlgItem(IDC_START)
        self.butStop = self.GetDlgItem(IDC_STOP)        
        self.Output= self.GetDlgItem(IDC_EDIT)
        self.Phrase= self.GetDlgItem(IDC_PHRASE)
        self.SelItems=[]

        self.FillList()

        size = self.GetWindowRect()
        self.LayoutControls(size[2]-size[0], size[3]-size[1])
        self.butOK.EnableWindow(0) # wait for first selection
        self.butStop.EnableWindow(0) # wait for first selection
        self.SetFocus()
        #Select First Item
        self.itemsControl.SetItemState(0,commctrl.LVNI_SELECTED+commctrl.LVNI_FOCUSED,255)

        self.oldStdout = sys.stdout        
        sys.stdout = self
        self.message = ''
        self.grammar = TrainDialogGrammar()
        self.grammar.initialize(self)
        self.trainedPhrases=[]        
        natlink.setChangeCallback(self.changeCallback)
        SetMic(self.MicStart)        
        return rc

    def changeCallback(self,what,param):
        if what == 'user':
            print('User changed.  New user is', param[0])
            self.onStop(0,0)
        elif what == 'mic':
            print('Microphone is ', param)
            if param=='off':
                self.onStop(0,0)

    def OnDestroy(self,msg):
        sys.stdout = self.oldStdout
    
    def write(self,text):
        self.message = self.message + text.replace('\n','\r\n')
        self.SetDlgItemText(IDC_EDIT,self.message)
        self.GetDlgItem(IDC_EDIT).SendMessage(win32con.EM_SETSEL,0x7FFF,0x7FFF)
        self.GetDlgItem(IDC_EDIT).SendMessage(win32con.EM_SCROLLCARET,0,0)

    def FillList(self):
        size = self.GetWindowRect()
        width = size[2] - size[0] - (10)
        itemDetails = (commctrl.LVCFMT_LEFT, width, "Phrase", 0)
        self.itemsControl.InsertColumn(0, itemDetails)
        index = 0
        for item in self.items:
            index = self.itemsControl.InsertItem(index+1, str(item), 0)

    def SetPhraseToTrain(self):
        self.Repeat=1
        if self.AreTraining:
            self.phrase=self.items[self.CurItem]
            self.SetDlgItemText(IDC_PHRASE,self.phrase.center(90))
            self.grammar.setList('TrainedWord',[self.phrase])
        else:
            self.SetDlgItemText(IDC_PHRASE,'')
            #self.setList('TrainedWord',[])            
                

    def OnListItemChange(self,std, extra):
        (hwndFrom, idFrom, code), (itemNotify, sub, newState, oldState, change, point, lparam) = std, extra
        oldSel = (oldState & commctrl.LVIS_SELECTED)!=0
        newSel = (newState & commctrl.LVIS_SELECTED)!=0
        if oldSel != newSel:
            try:
                if newSel:
                    self.CurItem=itemNotify
                    self.SetPhraseToTrain()
            except win32ui.error:
                pass


    def LayoutControls(self, w, h):
        self.Phrase.MoveWindow((0,10,w,27))                
        self.Output.MoveWindow((0,30,w,97))                
        self.itemsControl.MoveWindow((0,100,w,h-30))
        self.butStart.MoveWindow((10, h-24, 60, h-4))
        self.butStop.MoveWindow((70, h-24, 120, h-4))                
        self.butCancel.MoveWindow((w-60, h-24, w-10, h-4))
        self.butOK.MoveWindow((w-120, h-24, w-70, h-4))


    def on_size (self, params):
        lparam = params[3]
        w = win32api.LOWORD(lparam)
        h = win32api.HIWORD(lparam)
        self.LayoutControls(w, h)

                        
    def onStart(self,nID,code):
        print('training started')
        self.AreTraining=1
        if TrainInBatchMode:
            if not self.Batch:
                natlink.startTraining('batchadapt')
                self.Batch=1
                print('batch training started')
            else:
                print('wat')
        self.butOK.EnableWindow(1) 
        self.butStop.EnableWindow(1) 
        self.butStart.EnableWindow(0)
        self.CurItem = self.CurItem - 1
        self.itemsControl.SetFocus()
        self.nextWord()

    def onStop(self,nID,code):
        print('training stopped')
        self.AreTraining=0
        self.butStop.EnableWindow(0) 
        self.butStart.EnableWindow(1)
        self.SetPhraseToTrain()
        self.itemsControl.SetFocus()

    def correctResults(self):
        if len(self.trainedPhrases)>0:
            print('correcting results')
            for (resObj,phrase) in self.trainedPhrases:
                results=' '.join(resObj.getWords(0))
                if not resObj.correction(phrase):
                    if resObj.correction(phrase.lower()):
                        print('correcting %s by lowercase %s.' % (results,phrase))
                    else:
                        print('correcting %s by %s rejected.' % (results,phrase))
            self.trainedPhrases=[]        
        

    def OnOK(self):
        self.onStop(0,0)
        self.correctResults()
        if TrainInBatchMode and self.Batch:
            print('batch processing results')
            try:
                natlink.finishTraining()
                print('results processed')
            except:
                print('results processing not possible')
            self.Batch=0
        else:
            print('Done')
        #self._obj_.OnOK()


    def EndDialog(self, rc):
        self.trainedPhrases=[]
        if TrainInBatchMode and self.Batch:       
            natlink.finishTraining(0)
            print('results not processed')
        self._obj_.EndDialog(rc)
        return


    def nextWord(self):
        if self.CurItem < len(self.items)-1:
            self.itemsControl.SetFocus()
            self.itemsControl.SetItemState(self.CurItem,0,commctrl.LVNI_SELECTED+commctrl.LVNI_FOCUSED)            
            self.CurItem = self.CurItem + 1
            self.itemsControl.SetItemState(self.CurItem,0,commctrl.LVNI_SELECTED+commctrl.LVNI_FOCUSED)                        
            self.itemsControl.SetItemState(self.CurItem,commctrl.LVNI_SELECTED+commctrl.LVNI_FOCUSED,255)
            self.itemsControl.EnsureVisible(self.CurItem, 0)
        else:
            self.onStop(0,0)
  


def demodlg ():
    Title='Train Phrases'
    p=[('word 1'),('word 2'),('word 3')]
    dlg=TrainDialog(Title, p, 1)
    try:
        natlink.natConnect(1)
    except:
        return
    dlg.DoModal()
    natlink.natDisconnect()    


if __name__=='__main__':
    #pass
    demodlg()
    #demomodeless()

