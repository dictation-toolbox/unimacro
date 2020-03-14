
import win32ui
from pywin.mfc.dialog  import Dialog

    
def setDialog():
    """setting a dialog which is tested in pythonwin_dict.py, for dictation control
    
    first example from "Python, programming on win32", O'Reilly, by Mark Hammond and Andy Rhetobinson
    chapter 20, page 402

    second example comes with IDD_LARGE_EDIT, which gives a multiline control.    
    (No idea how to collect the results, only for testing inside now)

    """    
##    d = Dialog(win32ui.IDD_SIMPLE_INPUT)
##    IDD_SIMPLE_INPUT (15044) has controls:
##    IDC_PROMPT1: 15014
##    IDC_EDIT1: 15008

## also to be called with: win32ui.IDC_PROMPT1, giving 15014
## in the grammar:
##       Cwnd = win32ui.GetForegroundWindow() 
##       self.txt=Cwnd.GetDlgItem(15008)  # edit box
##i: 15008, it: object 'PyCEdit' - assoc is 01089070, vi=<None>, notify=0,ch/u=0/0, mh=0, kh=0
##i: 15014, it: object 'PyCWnd' - assoc is 010DF420, vi=<None>, notify=0,ch/u=0/0, mh=0, kh=0
    

    d = Dialog(win32ui.IDD_LARGE_EDIT)
##i: 1, not working it: object 'PyCButton' - assoc is 01077A70, vi=<None>, notify=0,ch/u=0/0, mh=0, kh=0
##i: 2, not working it: object 'PyCButton' - assoc is 00BCEC60, vi=<None>, notify=0,ch/u=0/0, mh=0, kh=0
##i: 15008, it: object 'PyCEdit' - assoc is 00BCECA8, vi=<None>, notify=0,ch/u=0/0, mh=0, kh=0

##    print 'dir of Dialog: %s'% dir(d)
##dir of Dialog: ['AddDDX', 'CreateWindow', 'DoModal', 'EndDialog', 'GotoDlgCtrl',
##                'HookCommands', 'MapDialogRect', 'OnAttachedObjectDeath', 'OnCancel',
##                'OnDestroy', 'OnInitDialog', 'OnOK', '__del__', '__doc__', '__getattr__',
##                '__getitem__', '__init__', '__len__', '__module__', '__nonzero__',
##                '__setitem__', '_obj_', 'bHaveInit', 'close', 'dll', 'has_key',
##                'items', 'keys', 'values']
    d.CreateWindow()
    print('keys: %s'% list(d.keys()))
    print('values: %s'% list(d.values()))
    print('items: %s'% list(d.items()))

    # search for dialog items in this window:    
    for i in range(100000):
        try:
            it = d.GetDlgItem(i)
            print('i: %s, it: %s'% (i, it))
        except:
            pass
##    print 'IDC_PROMPT2: %s'% win32ui.IDC_PROMPT2
##    print 'IDC_EDIT 2: %s'% win32ui.IDC_EDIT2
##    button = d.GetDlgItem(win32ui.IDC_PROMPT1)
##    button.SetWindowText('Hello natpython test dictation grammar')

    
if __name__ == '__main__':
    setDialog()

