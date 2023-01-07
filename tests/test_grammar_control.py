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

class GramOff(natbj.DocstringGrammar):
    """simple grammar which is initially off
    """
    name = 'gramoff'
    # gramSpec = """<gramoff> exported = 'grammar off';
    #     """
    def initialize(self):
        self.ini.set('general', 'initial on', "False")
        self.switchOnOrOff()
        if not self.isLoaded():
            # print(f'{self.name}: grammar is not loaded')
            return
    def rule_gramoff(self, words):
        """grammar off"""
        print(f'got gramoff: {words}')
        
def test_getAllGrammars(unimacro_setup):
    """see if we can get all the grammars
    """
    gramon = GramOn(inifile_stem="_gramon")
    gramon.initialize()
    gramoff = GramOff(inifile_stem="_gramoff")
    gramoff.initialize()
    assert gramon.isLoaded() is True
    assert gramon.isActive() is True
    assert gramoff.isLoaded() is False
    assert gramoff.isActive() is False
    utilGrammar = UtilGrammar()
    # monkeypatch.setattr(utilGrammar, 'switchOnOrOff', do_nothing)
    utilGrammar.startInifile()
    utilGrammar.initialize()
    # utilGrammar.gotResults_show(words=['show', 'all', 'grammars'], fullResults={})
    assert utilGrammar.isLoaded() is True
    assert utilGrammar.isActive() is True
    
    al = utilGrammar.getUnimacroGrammars()
    assert len(al) == 3

    loaded = {g for g in al if al[g].isLoaded()}
    assert loaded == set(['control', 'gramon'])
    active = {g for g in al if al[g].isActive()}
    assert active == loaded
    
    gramoff.switchOn()
    loaded = {g for g in al if al[g].isLoaded()}
    assert loaded == set(['control', 'gramon', 'gramoff'])
    active = {g for g in al if al[g].isActive()}
    assert active == loaded
    
    gramoff.switchOff()
    loaded = {g for g in al if al[g].isLoaded()}
    assert loaded == set(['control', 'gramon'])     #   switchOff also unloads the grammar!
    active = {g for g in al if al[g].isActive()}
    assert active == set(['control', 'gramon'])
    
    gramon.switchOff()
    loaded = {g for g in al if al[g].isLoaded()}
    assert loaded == set(['control'])     
    active = {g for g in al if al[g].isActive()}
    assert active == set(['control'])

    utilGrammar.switchOff()
    loaded = {g for g in al if al[g].isLoaded()}
    assert loaded == set(['control'])     
    active = {g for g in al if al[g].isActive()}
    assert active == set(['control'])

    gramon.switchOn()
    loaded = {g for g in al if al[g].isLoaded()}
    assert loaded == set(['control', 'gramon'])     
    active = {g for g in al if al[g].isActive()}
    assert active == set(['control', 'gramon'])

    gramon.switchOn()
    loaded = {g for g in al if al[g].isLoaded()}
    assert loaded == set(['control', 'gramon'])     
    active = {g for g in al if al[g].isActive()}
    assert active == set(['control', 'gramon'])


def test_show_all_grammars(unimacro_setup):
    gramon = GramOn(inifile_stem="_gramon")
    gramon.initialize()
    gramoff = GramOff(inifile_stem="_gramoff")
    gramoff.initialize()
    assert gramon.isLoaded() is True
    assert gramon.isActive() is True
    assert gramoff.isLoaded() is False
    assert gramoff.isActive() is False
    utilGrammar = UtilGrammar()
    # monkeypatch.setattr(utilGrammar, 'switchOnOrOff', do_nothing)
    utilGrammar.startInifile()
    utilGrammar.initialize()
    Words = ['show', 'all', 'grammars']
    FR = {}
    utilGrammar.gotResults_show(Words, FR)
    
        
    

if __name__ == "__main__":
    pytest.main(['test_grammar_control.py'])
