#pylint:disable=E1101
from pathlib import Path
import pytest
import natlink
from unimacro.UnimacroGrammars._general import ThisGrammar
from natlinkcore import natlinkstatus
from dtactions.unimacro import unimacroutils
from dtactions.unimacro import unimacroactions
status = natlinkstatus.NatlinkStatus

thisDir = Path(__file__).parent

def do_nothing(*args, **kwargs):
    return None

def mock_unimacro_user_dir(tmp_dir,_self):

    mock_folder= tmp_dir / "mock_unimacro_userdir"
    print(f"Mock unimacro folder {mock_folder} in {__file__}")   #just for understanding remove eventually
    if not mock_folder.is_dir():
        mock_folder.mkdir()
    return str(mock_folder)

def test_getTopOrChild(monkeypatch):
    """see if (with debugging) coming into a grammar works
    """
    # monkeypatch.setattr(status, "getUnimacroUserDirectory", mock_unimacro_user_dir)
    
    natlink.natConnect()
    try:
        thisGrammar = ThisGrammar()
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
    finally:
        natlink.natDisconnect()


    


if __name__ == "__main__":
    pytest.main(['test_grammar_general.py'])
