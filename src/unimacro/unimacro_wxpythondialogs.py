
import wx


def InputBox(text, prompt="Unimacro Input", default=""):
    """this one kills Dragon"""
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
    result = InputBox("just testing")
    print(result, repr(result))
    