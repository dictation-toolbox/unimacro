#pylint:disable=E1101
from pathlib import Path
import pytest
import natlink
from unimacro.UnimacroGrammars import _lines
from natlinkcore import natlinkstatus
status = natlinkstatus.NatlinkStatus

thisDir = Path(__file__).parent

def do_nothing(*args, **kwargs):
    return None

@pytest.mark.parametrize(
    "current, relative, expect",
    [ (55, 2, 52),
      (355, 1, 351),
    ],
)
def test_getLineRelativeToModulo10(current, relative, expect):
    """test the relative to (modulo 10) trick for getting line numbers
    """
    modulo = 10
    result = _lines.getLineRelativeTo(relative, currentLine=current, modulo=modulo)
    assert result == expect


@pytest.mark.parametrize(
    "current, relative, expect",
    [ (55, 3, 103),
      (55, 3, 103),
      (255, 9, 209),
      (255, 29, 229),
      (251, 1, 301),
      (358, 7, 407),
      (358, 47, 347),
    ],
)
def test_getLineRelativeToModulo100(current, relative, expect):
    """test the relative to (modulo 100) trick for getting line numbers
    """
    modulo = 100
    result = _lines.getLineRelativeTo(relative, currentLine=current, modulo=modulo)
    assert result == expect
    
def test_get_accented_numbers_info(unimacro_setup,monkeypatch):
    """problem with the numbers spoken forms of accented characters
    """
     
    thisGrammar = _lines.ThisGrammar()
    monkeypatch.setattr(thisGrammar, 'switchOnOrOff', do_nothing)
    thisGrammar.startInifile() #modName = '_lines')
    thisGrammar.initialize()
    thisGrammar.showInifile()
    # the showInifile did not show accented characters before, but seems ok now.
    


if __name__ == "__main__":
    pytest.main(['test_grammar_lines.py'])
  