"""input box, in use with the _folders grammar

"""
#pylint:disable=E1101
import wx


def InputBox(text, prompt="Unimacro Input", default=""):
    """this one kills Dragon"""
    _app = wx.App()
    dialog = wx.TextEntryDialog(None,
                text, prompt, default, style=wx.OK|wx.CANCEL)
    if dialog.ShowModal() == wx.ID_OK:
        result = dialog.GetValue()
    else:
        result = None
    dialog.Destroy()
    return result

if __name__ == "__main__":
    _result = InputBox("just testing")
    print(_result, repr(_result))
    