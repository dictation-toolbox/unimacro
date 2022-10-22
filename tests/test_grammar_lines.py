#pylint:disable=E1101
from pathlib import Path
import pytest
import natlink
from unimacro.UnimacroGrammars import _lines
from natlinkcore import natlinkstatus
status = natlinkstatus.NatlinkStatus

thisDir = Path(__file__).parent

def test_getLineRelativeTo():
    """test the relative to (modulo 100 or modulo 10) trick for getting line numbers
    """
    modulo = 10
    current, relative, expect = 55, 2, 52
    result = _lines.getLineRelativeTo(relative, currentLine=current, modulo=modulo)
    assert result == expect

    current, relative, expect = 355, 1, 351
    result = _lines.getLineRelativeTo(relative, currentLine=current, modulo=modulo)
    assert result == expect

    current, relative, expect = 55, 0, 60
    result = _lines.getLineRelativeTo(relative, currentLine=current, modulo=modulo)
    assert result == expect

    current, relative, expect = 355, 0, 360
    result = _lines.getLineRelativeTo(relative, currentLine=current, modulo=modulo)
    assert result == expect

    modulo = 100
    current, relative, expect = 55, 3, 103
    result = _lines.getLineRelativeTo(relative, currentLine=current, modulo=modulo)
    assert result == expect

    current, relative, expect = 255, 9, 209
    result = _lines.getLineRelativeTo(relative, currentLine=current, modulo=modulo)
    assert result == expect

    current, relative, expect = 251, 1, 301
    result = _lines.getLineRelativeTo(relative, currentLine=current, modulo=modulo)
    assert result == expect v
    

if __name__ == "__main__":
    pytest.main(['test_grammar_lines.py'])
