# -*- coding: iso-8859-1 -*-
"""this module gives windows parameters, which can
be used in the messagefunctions (and the test unittestMessagefunctions.py),

and in the grammars which use DictObj, the NatLink version of the dictation control,
which must be kept in sync with the actual window it servers for.

Finding the appropriate window and control is done by
-app (string to start the application with os.startfile)
-caption (string which tests for (part of) the window title, case insensitive)
-class (className of the application)
-control (name of the control which hold the text to sync with)
-aftertext: possibly a space or '\n' or '\r\n' (or os.linesep) after the buffer (RichEdit) 
-linesep: the line separator. "EDIT" controls seem to expect '\n', "RichEdit" seems to expect '\r\n'
"""
import os
import win32gui
PROGS = dict(notepad={},
         wordpad={},
         komodo={},
         ultraedit={},
         dragonpad={},
         pythonwin={},
         word={})
PROGS['win32pad'] = {}
PROGS['python~1'] = {}  # ??? also pythonwin
PROGS['aligen']  = {}
# set defaults:
for p in PROGS:
    W = PROGS[p]
    W["apppath"] = p
    W["windowcaption"] = None
    W["windowclass"] = None
    W["editcontrol"] = None # these three
    W["edittext"] = None    # can identify the wanted control
    W["selectionfunction"] = None  # not tried this one yet
    W["aftertext"] = '\r'
    W["linesep"] = '\r'        # seems to be default for RichEdit...
    #W["joinchar"] = '\n'       # probably linesep = aftertext + joinchar, in other words
                                # the aftertext remains at each line got from the window
                                # and we need the joinchar to complete the linesep...
    W["controlhandle"] = None # for rare test purposes

# for testing with Edit control (notepad)
# this one sucks, it is not clear which linefeeds are for real and which ones
# are because of scrolling lines
W = PROGS["notepad"]       
W["windowclass"] = "Notepad"    # case sensitive, get with "Give window info" of
W["editcontrol"] = "Edit"     # name of the control where the text goes in
W["aftertext"] = ''
W["linesep"] = "\n"
#W["joinchar"] = "\n"      # if afterchar is empty, the linesep is equal to the join again character


# for testing in RichEdit control (Wordpad, note the language specific path)
W = PROGS["wordpad"]
# richedit control
# dutch xp system:
W["apppath"] = r"C:\Program Files\Windows NT\Bureau-accessoires\wordpad.exe" 
W["windowcaption"] = None      
W["windowclass"] = "WordPadClass"   
W["editcontrol"] = "RICHEDIT50W"     # name of the control where the text goes in


# for testing in RichEdit20 control (win32pad)
W = PROGS["win32pad"]
# richedit control
W["apppath"] = r"" 
W["windowcaption"] = "win32pad"
W["windowclass"] = "win32padClass"   
W["editcontrol"] = "RichEdit20A"     # name of the control where the text goes in


## future:
W = PROGS["komodo"]
W["apppath"] = r"C:\Program Files\ActiveState Komod IDE 5.1\lib\mozilla\komodo.exe"
W["windowcaption"] = "komodo ide"   
W["windowclass"] =   "MozillaUIWindowClass"
W["editcontrol"] = "Edit"     # name of the control where the text goes in
#W["aftertext"] = '\r\n'           # always after a text (richedit)
W["linesep"] = '\r\n'

W = PROGS["ultraedit"]
W["apppath"] = r"C:\Program Files\IDM Computer Solutions\UltraEdit-32\Uedit32.exe"
W["windowcaption"] = "ultraedit"   
W["windowclass"] =   "Afx"
W["editcontrol"] = "Edit"     # name of the control where the text goes in
#W["aftertext"] = '\r\n'           # always after a text (richedit)
W["linesep"] = '\r\n'

W = PROGS["pythonwin"]
W["apppath"] = r""
W["windowcaption"] = "pythonwin"   
W["windowclass"] =   None
W["editcontrol"] = None
#W["controlhandle"] = 68016

def getPythonwinEditControl(hwnd, actualText, actualClass):
    """get windows with first Afx and then Scintilla
    """
    if actualClass.startswith("Afx:") or actualClass == "Scintilla":
        return True

W["selectionfunction"] = getPythonwinEditControl

# name of the control where the text goes in
W["edittext"] = None      # expect a new file, unsaved
W["aftertext"] = '\r\n'           # always after a text (richedit)
W["linesep"] = '\r\n'


    


# ??
PROGS["python~1"] = PROGS["pythonwin"]


# for testing in application word (isVisible only)
W = PROGS["word"]
W["apppath"] = None
W["windowcaption"] = "Microsoft Word"      
W["windowclass"] = None
W["editcontrol"] = "RICHEDIT50W"     # name of the control where the text goes in
