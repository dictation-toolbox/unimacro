#pylint:disable=E1101
from pathlib import Path
import pytest

#IMPORTANT
#patching of environment to point to correct natlink.ini needs to happen before loading nay natlink related code

natlink_folder=str(Path(__file__).parent / "unimacro_test_natlink_config.natlink")
print(f"{__file__}  natlink folder {natlink_folder}")
pytest.MonkeyPatch().setenv("NATLINK_USERDIR",natlink_folder)

import natlink
from unimacro._control import UtilGrammar
from unimacro import natlinkutilsbj as natbj
from natlinkcore import natlinkstatus
status = natlinkstatus.NatlinkStatus

thisDir = Path(__file__).parent
@pytest.fixture 
def status():
    from natlinkcore import natlinkstatus
    status = natlinkstatus.NatlinkStatus
    return status

def do_nothing(*args, **kwargs):
    return None

def mock_unimacro_user_dir(tmp_dir,_self):

    mock_folder= tmp_dir / "mock_unimacro_userdir"
    print(f"Mock unimacro folder {mock_folder} in {__file__}")   #just for understanding remove eventually
    if not mock_folder.is_dir():
        mock_folder.mkdir()
    return str(mock_folder)

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
        
def test_getAllGrammars(monkeypatch):
    """see if we can get all the grammars
    """
    
    
    natlink.natConnect()
    try:
        gramon = GramOn()
        gramon.initialize()
        gramoff = GramOff()
        gramoff.initialize()
        utilGrammar = UtilGrammar()
        # monkeypatch.setattr(utilGrammar, 'switchOnOrOff', do_nothing)
        utilGrammar.startInifile()
        utilGrammar.initialize()
        utilGrammar.gotResults_show(words=['show', 'all', 'grammars'], fullResults={})
    finally:
        natlink.natDisconnect()

if __name__ == "__main__":
    pytest.main(['test_grammar_control.py'])
