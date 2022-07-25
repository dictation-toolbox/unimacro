"""template for _folders grammar, remember function.
This template is filled with the actual values and fired. It asks for a spoken form to "remember a given file", this value
is put in the _folders.ini config file.
"""

import wx
import time
from natlinkcore import inivars

prompt = """$prompt$"""  # readable text
text = """$text$"""          # input text, the key of the 
inifile = "$inifile$"
section = "$section$"
value = "$value$"
title = "test"
default = "$default$"
pausetime = "$pausetime$"  # should be replaced by 0 or a positive int value



def InputBox(text, prompt, title, default):
    """the dialog, which returns the spoken form"""
    app = wx.App()
    dialog = wx.TextEntryDialog(None,
    text, prompt, default, style=wx.OK|wx.CANCEL)
    if dialog.ShowModal() == wx.ID_OK:
        result = dialog.GetValue()
    else:
        result = None
    dialog.Destroy()
    return result

if __name__ == "__main__":
    result = InputBox(text, prompt, title, default)
    if result:
        key = result
        ini = inivars.IniVars(inifile)
        ini.set(section, key, value)
        ini.write()
        print('Wrote "%s = %s" to inifile'% (key, value))
        print('Call "edit folders" to edit or delete')
    else:
        print("Action canceled, no change of ini file")
    # if pausetime is given, launch as .py, otherwise launch as .pyw:
    if pausetime:
        # print "sleep: %s"% pausetime
        time.sleep(pausetime)
    