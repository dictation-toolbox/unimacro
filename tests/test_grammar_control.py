#pylint:disable=E1101
from pathlib import Path
import pytest

from unimacro._control import UtilGrammar
from unimacro import natlinkutilsbj as natbj

thisDir = Path(__file__).parent

def do_nothing(*args, **kwargs):
    return None


class GramOn(natbj.IniGrammar):
    """simple grammar which is initially on
    """
    name = 'gramon'
    gramSpec = """<gramon> exported = 'grammar on';
        """
    def initialize(self):
        self.ini.set('general', 'initial on', "True")
        self.switchOnOrOff()
        if not self.isLoaded():
            # print(f'{self.name}: grammar is not loaded')
            return
    def gotResults_gramon(self, words, fullResults):
        print(f'got gramon: {words}')

class GramOff(natbj.IniGrammar):
    """simple grammar which is initially off
    """
    name = 'gramoff'
    gramSpec = """<gramoff> exported = 'grammar off';
        """
    def initialize(self):
        self.ini.set('general', 'initial on', "False")
        self.switchOnOrOff()
        if not self.isLoaded():
            # print(f'{self.name}: grammar is not loaded')
            return
    def gotResults_gramoff(self, words, fullResults):
        print(f'got gramoff: {words}')
        
def test_getAllGrammars(unimacro_setup):
    """see if we can get all the grammars
    """
    gramon = GramOn()
    gramon.initialize()
    gramoff = GramOff()
    gramoff.initialize()
    utilGrammar = UtilGrammar()
    # monkeypatch.setattr(utilGrammar, 'switchOnOrOff', do_nothing)
    utilGrammar.startInifile()
    utilGrammar.initialize()
    utilGrammar.gotResults_show(words=['show', 'all', 'grammars'], fullResults={})

if __name__ == "__main__":
    pytest.main(['test_grammar_control.py'])
