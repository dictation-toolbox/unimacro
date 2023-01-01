#pylint:disable=E1101
from pathlib import Path
import pytest


thisDir = Path(__file__).parent

def test_fill_folders_list(unimacro_setup):
    """see if (with debugging) the list folders  (foldersDict) is filled
    """
    from unimacro.UnimacroGrammars._folders import ThisGrammar
    thisGrammar = ThisGrammar()
    thisGrammar.startInifile() #modName = '_folders')
    thisGrammar.initialize()

if __name__ == "__main__":
    pytest.main(['test_grammar_folders.py'])
