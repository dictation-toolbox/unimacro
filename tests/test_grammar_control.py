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
    gramSpec = """<gramon> exported = 'grammar on';
        """
    def initialize(self):
        self.ini.set('general', 'initial on', "True")
        self.switchOnOrOff()
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
    assert utilGrammar.LoadedControlGrammars[0] is utilGrammar
    assert gramon.LoadedControlGrammars[-1] is utilGrammar
    
    al = utilGrammar.getUnimacroGrammars()
    assert len(al) == 3

    loaded = {g for g, gram in al.items() if gram.isLoaded()}
    assert loaded == set(['control', 'grammaron'])
    active = {g for g, gram in al.items() if gram.isActive()}
    assert active == loaded
    
    gramoff.switchOn()
    loaded = {g for g, gram in al.items() if gram.isLoaded()}
    assert loaded == set(['control', 'grammaron', 'grammaroff'])
    active = {g for g, gram in al.items() if gram.isActive()}
    assert active == loaded
    
    gramoff.switchOff()
    loaded = {g for g, gram in al.items() if gram.isLoaded()}
    assert loaded == set(['control', 'grammaron'])     #   switchOff also unloads the grammar!
    active = {g for g, gram in al.items() if gram.isActive()}
    assert active == set(['control', 'grammaron'])
    
    # should ignore this command:
    utilGrammar.switchOff()
    loaded = {g for g, gram in al.items() if gram.isLoaded()}
    assert loaded == set(['control', 'grammaron']) 
    active = {g for g, gram in al.items() if gram.isActive()}
    assert active == set(['control', 'grammaron'])

    gramon.switchOn()
    loaded = {g for g, gram in al.items() if gram.isLoaded()}
    assert loaded == set(['control', 'grammaron'])     
    active = {g for g, gram in al.items() if gram.isActive()}
    assert active == set(['control', 'grammaron'])

    gramon.switchOn()
    loaded = {g for g, gram in al.items() if gram.isLoaded()}
    assert loaded == set(['control', 'grammaron'])     
    active = {g for g, gram in al.items() if gram.isActive()}
    assert active == set(['control', 'grammaron'])



    
def test_ExclusiveMode(unimacro_setup):
    """see if grammars can switch on and off exclusive mode, with _control following

    (when a grammar switches on exclusive mode, _control follows, because then the inspecting commands
    are still recognized)
    """
    gramon = GramOn(inifile_stem="_gramon")
    gramon.initialize()
    gramoff = GramOff(inifile_stem="_gramoff")
    gramoff.initialize()
    # just to be sure (should have been done when unloading _control (utilGrammar))
    gramon.UnregisterControlObject()
    assert gramon.isLoaded() is True
    assert gramon.isActive() is True
    assert gramoff.isLoaded() is False
    assert gramoff.isActive() is False
    # first test with utilGrammar (_control) not present.
    gramon.setExclusive(1)
    # set exclusive 
    gramon.setExclusive(1)
    exclGr = gramon.getExclusiveGrammars() 
    assert len(exclGr) == 1
    gramon.setExclusive(0)
    exclGr = gramon.getExclusiveGrammars()
    assert len(exclGr) == 0
    
    utilGrammar = UtilGrammar()
    # monkeypatch.setattr(utilGrammar, 'switchOnOrOff', do_nothing)
    utilGrammar.startInifile()
    utilGrammar.initialize()
    # utilGrammar.gotResults_show(words=['show', 'all', 'grammars'], fullResults={})
    assert utilGrammar.isLoaded() is True
    assert utilGrammar.isActive() is True
    assert utilGrammar.LoadedControlGrammars[0] is utilGrammar
    assert gramon.LoadedControlGrammars[-1] is utilGrammar
    
    exclGr = gramon.getExclusiveGrammars()
    assert len(exclGr) == 0
    utilGrammar.setExclusive(1)
    exclGr = gramon.getExclusiveGrammars()
    assert len(exclGr) == 1
    gramon.setExclusive(1)
    exclGr = gramon.getExclusiveGrammars()
    assert len(exclGr) == 2
    gramon.setExclusive(0)
    exclGr = gramon.getExclusiveGrammars()
    assert len(exclGr) == 0
    

    
    

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
    
def test_get_unimacro_grammars(unimacro_setup):
    """get modules from the active grammars
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

    gramnames = utilGrammar.getUnimacroGrammarNamesPaths()
    assert set(gramnames) == {'grammaron', 'grammaroff', 'control'}

    
    ### uncomment manually which you want to test:    
    # # try "show gramon"
    # # this one opens the info in a new window:
    # Words = ['show', 'grammaron']
    # FR = {}
    # utilGrammar.gotResults_show(Words, FR)
    # Words = ['show', 'grammaroff']
    # FR = {}
    # utilGrammar.gotResults_show(Words, FR)
    #    
    Words = ['switch', 'on', 'grammaroff']
    FR = {}
    utilGrammar.gotResults_switch(Words, FR)
    assert gramoff.isLoaded() is True
    assert gramoff.isActive() is True
    
    # newSet = set(self.getRegisteredGrammarNames())


if __name__ == "__main__":
    pytest.main(['test_grammar_control.py'])
