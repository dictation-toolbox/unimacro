#pylint:disable=E1101
from pathlib import Path
import pytest
import natlink
from unimacro.UnimacroGrammars import _brackets
from natlinkcore import natlinkstatus
status = natlinkstatus.NatlinkStatus

thisDir = Path(__file__).parent
 

def test_testpleftpright(unimacro_setup):
    """check the split of a brackets string in left and right
    
    "" should return " and "
    asymmetric strings like f'|'  (with a | as split) should return f' and '
    
    """
    gram = _brackets.BracketsGrammar()
    gram.startInifile() #modName = '_tasks')
    gram.initialize()
    
    # test one
    words = ['brackets', 'quotes']
    fr = {}
    gram.gotResultsInit(words, fr)
    # print(f'natbj.loadedGrammars: {natbj.loadedGrammars}')
    gram.rule_brackets(words)
    assert gram.pleft == '("'
    assert gram.pright == '")'
    
    # test two:
    words = ['quotes']
    gram.gotResultsInit(words, fr)
    # print(f'natbj.loadedGrammars: {natbj.loadedGrammars}')
    gram.rule_brackets(words)
    assert gram.pleft == '"'
    assert gram.pright == '"'

def test_testactivebracketrules(unimacro_setup):
    """do all the active words in the bracket rules accordin to the inifile
    
    """
    gram = _brackets.BracketsGrammar()
    gram.startInifile() #modName = '_tasks')
    gram.initialize()
    
    # test one
    all_words = gram.ini.get('brackets')
    for i, word in enumerate(all_words):
        n = i + 1
        words = [word]
        result = gram.ini.get('brackets', word)
        print(f'test {word}, expect {result}')
        fr = {}
        gram.gotResultsInit(words, fr)
        # print(f'natbj.loadedGrammars: {natbj.loadedGrammars}')
        gram.rule_brackets(words)
    assert n == len(all_words)
        
    
if __name__ == "__main__":
    pytest.main(['test_grammar_brackets.py'])
