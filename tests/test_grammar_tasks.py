#pylint:disable=E1101
from pathlib import Path
import pytest
import natlink
from unimacro.UnimacroGrammars._tasks import ThisGrammar
from natlinkcore import natlinkstatus
status = natlinkstatus.NatlinkStatus

thisDir = Path(__file__).parent

def mock_unimacro_user_dir(_self):
    mock_folder= thisDir / "mock_unimacro_userdir"
    if not mock_folder.is_dir():
        mock_folder.mkdir()
    return str(mock_folder)

def test_gototask(monkeypatch):
    """see if (with debugging) coming into a grammar works
    """
    monkeypatch.setattr(status, "getUnimacroUserDirectory", mock_unimacro_user_dir)
    
    natlink.natConnect()
    try:
        thisGrammar = ThisGrammar()
        thisGrammar.startInifile() #modName = '_tasks')
        thisGrammar.initialize()
        Words = ['task', 'three']
        # print(f'natbj.loadedGrammars: {natbj.loadedGrammars}')
        thisGrammar.rule_taskswitch(Words)
        # natlink.recognitionMimic(["task", "three"])  
    finally:
        natlink.natDisconnect()

if __name__ == "__main__":
    pytest.main(['test_gototask'])
