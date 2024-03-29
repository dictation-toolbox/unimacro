#pylint:disable=E1101
from pathlib import Path
import pytest
from unimacro._control import UtilGrammar
from unimacro.UnimacroGrammars._brackets import BracketsGrammar
from unimacro import natlinkutilsbj as natbj
thisDir = Path(__file__).parent

def do_nothing(*args, **kwargs):
    return None

# test with _control.py, _brackets.py (a very simple grammar), and two grammars that are defined in this file, gramon and gramoff


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
    assert utilGrammar in utilGrammar.LoadedControlGrammars
    
    al = utilGrammar.getUnimacroGrammars()
    assert len(al) == 4

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

def test_getAllGrammarsSwitchingOnAlternative(unimacro_setup):
    """see if we can get all the grammars, as control switches on in a different way, should also work...
    
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
    assert utilGrammar in utilGrammar.LoadedControlGrammars
    
    al = utilGrammar.getUnimacroGrammars()
    assert len(al) == 4

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


def test_switching_on_off_brackets(unimacro_setup):
    """try if brackets grammar switches on and off
    """
    gram = BracketsGrammar()
    gram.initialize()
    assert gram.isLoaded() is True
    assert gram.isActive() is True
    gram.switchOff()
    assert gram.isLoaded() is False
    assert gram.isActive() is False
    gram.switchOn()
    assert gram.isLoaded() is True
    assert gram.isActive() is True
    
    
    
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
    assert utilGrammar in utilGrammar.LoadedControlGrammars
    
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
    
    
    
def test_get_unimacro_grammars(unimacro_setup):
    """get modules from the active grammars
    
    This test is only very partial, because here some test grammars are involved.
    In the normal case, each unimacro grammar is in its own file, module,
    which are registered at startup time (in allGrammarXObjects)
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
    unimacro_grammars = utilGrammar.getUnimacroGrammars()
    # _brackets not loaded in this test
    assert len(unimacro_grammars) == 3
    # does not function here, as the grammars are not in separate files:
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
       
    # this one does not work in this test, because at initialize time
    # the grammar is hardcoded switched off....
    # Words = ['switch', 'on', 'grammaroff']
    # FR = {}  
    # utilGrammar.gotResults_switch(Words, FR)
    # assert gramoff.isLoaded() is True
    # assert gramoff.isActive() is True

    


if __name__ == "__main__":
    pytest.main(['test_grammar_control.py'])
