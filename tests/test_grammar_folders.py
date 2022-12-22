#pylint:disable=E1101
from pathlib import Path
import pytest
import natlink
from natlinkcore import natlinkstatus
status = natlinkstatus.NatlinkStatus

thisDir = Path(__file__).parent

def mock_unimacro_user_dir(tmp_dir, _self):

    mock_folder= tmp_dir / "mock_unimacro_userdir"
    print(f"Mock unimacro folder {mock_folder} in {__file__}")   #just for understanding remove eventually
    if not mock_folder.is_dir():
        mock_folder.mkdir()
    return str(mock_folder)

def test_fill_folders_list():
    """see if (with debugging) the list folders  (foldersDict) is filled
    """
    # monkeypatch.setattr(status, "getUnimacroUserDirectory", mock_unimacro_user_dir)
    
    natlink.natConnect()
    try:
        from unimacro.UnimacroGrammars._folders import ThisGrammar
        thisGrammar = ThisGrammar()
        thisGrammar.startInifile() #modName = '_folders')
        thisGrammar.initialize()
    finally:
        natlink.natDisconnect()

if __name__ == "__main__":
    pytest.main(['test_grammar_folders.py'])
