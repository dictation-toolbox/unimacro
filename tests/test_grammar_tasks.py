#pylint:disable=E1101
from pathlib import Path
import pytest
import natlink
from unimacro.UnimacroGrammars._tasks import ThisGrammar
from natlinkcore import natlinkstatus
status = natlinkstatus.NatlinkStatus

thisDir = Path(__file__).parent
 

def test_gototask(unimacro_setup):
    """see if (with debugging) coming into a grammar works
    """
    # TODO Doug - get this working with the mock folder.
    # challenge is all a bunch extra stuff is loaded or doesn't work when imported.
    thisGrammar = ThisGrammar()
    thisGrammar.startInifile() #modName = '_tasks')
    thisGrammar.initialize()
    Words = ['task', 'three']
    # print(f'natbj.loadedGrammars: {natbj.loadedGrammars}')
    thisGrammar.rule_taskswitch(Words)
    # natlink.recognitionMimic(["task", "three"])  

if __name__ == "__main__":
    pytest.main(['test_grammar_tasks.py'])
