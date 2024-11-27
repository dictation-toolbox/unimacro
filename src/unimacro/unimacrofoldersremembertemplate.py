"""template for _folders grammar, remember function.
This template is filled with the actual values and fired. It asks for a spoken form to "remember a given file", this value
is put in the _folders.ini config file.
"""
#pylint:disable=W0621
import time
import PySimpleGUI as sg      
from dtactions import inivars

prompt = """$prompt$"""  # readable text
text = """$text$"""          # input text, the key of the 
inifile = "$inifile$"
section = "$section$"
value = "$value$"
title = "test"
default = "$default$"
pausetime = "$pausetime$"  # should be replaced by 0 or a positive int value



def InputBox(text, prompt, title, default):
    """the dialog, which returns the wanted spoken form"""
    layout = [[sg.Text(prompt)],      
                     [sg.InputText(default)],      
                     [sg.OK(), sg.Cancel()]]      
    
    window = sg.Window(title, layout)    
    
    _event, values = window.read()    
    window.close()
    
    return values[0]    

if __name__ == "__main__":
    result = InputBox(text, prompt, title, default)
    if result:
        key = result
        ini = inivars.IniVars(inifile)
        ini.set(section, key, value)
        ini.write()
        print(f'Wrote "{key} = {value}" to inifile')
        print('Call "edit folders" to edit or delete')
    else:
        print("Action canceled, no change of ini file")
    # if pausetime is given, launch as .py, otherwise launch as .pyw:
    if pausetime:
        # print "sleep: %s"% pausetime
        time.sleep(pausetime)
    