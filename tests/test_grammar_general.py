#pylint:disable=E1101
from pathlib import Path
import pytest
from unimacro.UnimacroGrammars._general import ThisGrammar
from dtactions import unimacroutils
from dtactions import unimacroactions

thisDir = Path(__file__).parent

def do_nothing(*args, **kwargs):
    return None

def test_getTopOrChild(unimacro_setup,monkeypatch):
    """see if (with debugging) coming into a grammar works
    """
     

    thisGrammar = ThisGrammar()
    thisGrammar.info("test")
    monkeypatch.setattr(thisGrammar, 'switchOnOrOff', do_nothing)
    thisGrammar.startInifile() #modName = '_general')
    thisGrammar.initialize()
    hndle = 10

    ##(progpath, prog, title, toporchild, classname, hndle)
    ## ProgInfo(progpath, prog, title, toporchild, classname, HNDLE)
    
    progInfo = unimacroutils.ProgInfo('path/to/program.exe', 'program', 'window title', 'top', 'classname', hndle)
    
    # thisGrammar.gotBegin(modInfo)
    thisGrammar.progInfo = progInfo
    assert thisGrammar.getTopOrChild(progInfo=progInfo, childClass=None) is True
    assert thisGrammar.getTopOrChild(progInfo=progInfo, childClass='classname') is False    
 


    


if __name__ == "__main__":
    pytest.main(['test_grammar_general.py'])
