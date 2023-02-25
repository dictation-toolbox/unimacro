#pylint:disable=E1101
from pathlib import Path
import pytest
from unimacro.UnimacroGrammars._folders import ThisGrammar

thisDir = Path(__file__).parent

def test_fill_folders_list(unimacro_setup):
    """see if (with debugging) the list folders  (foldersDict) is filled
    """
    # from unimacro.UnimacroGrammars._folders import ThisGrammar
    thisGrammar = ThisGrammar()
    thisGrammar.startInifile() #modName = '_folders')
    thisGrammar.initialize()

def test_folder_remember(unimacro_setup):
    """go through folder remember functions
    """
    # from unimacro.UnimacroGrammars._folders import ThisGrammar
    thisGrammar = ThisGrammar()
    thisGrammar.startInifile() #modName = '_folders')
    thisGrammar.initialize()
    words = ['this', 'folder', 'remember']
    FR = {}
    thisGrammar.catchRemember = 'folder'
    thisGrammar.wantedFolder = r'C:\Windows'
    
    thisGrammar.gotResults_remember(words, FR)
    


if __name__ == "__main__":
    pytest.main(['test_grammar_folders.py'])
