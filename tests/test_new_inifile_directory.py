"""this one tests if an new .ini file is automatically made, when no examples are available...

Not very nice programmed, but for the moment it works (January 2024, Quintijn)

"""
import os
from pathlib import Path
import pytest
from unimacro import natlinkutilsbj as natbj
from natlinkcore import natlinkstatus
status = natlinkstatus.NatlinkStatus()
#boilerplate to copy the grammar ini file into the correct location
#just chagne grammar_ini to the name of the grammar ini file you want copied into
#unimacro user directory
# from conftest import make_copy_grammar_ini_fixture
grammar_ini= "_newbie.ini"
#grammar_ini_fixture will depend on unimacro_setup, so you dont' need to specfiy unimacro_setup
#as a fixture in your tests.  Though you can
# grammar_ini_fixture=make_copy_grammar_ini_fixture(grammar_ini)
#end of boilderplate to copy the gramar ini file into correct location

# #leave these first two samples in as documentation in test_brackets.  confests docs say to look in this file for examples.
# def test_sample_grammar_ini_fixture1(grammar_ini_fixture):
#     assert True
# 
# def test_sample_grammar_ini_fixture2(grammar_ini_fixture,unimacro_setup):
#     print(f"Unimacro setup sample: {unimacro_setup} grammar_ini_fixutre {grammar_ini_fixture} (should be the same)")
#     assert True


class Newbie(natbj.IniGrammar):
    """simple grammar which is initially on
    """
    gramSpec = """<gramon> exported = 'grammar on';
        """
    def initialize(self):
        self.ini.set('general', 'initial on', "True")
        self.switchOnOrOff()
    def gotResults_gramon(self, words, fullResults):
        print(f'got gramon: {words}')


def test_get_newbie_without_demo_inifile(unimacro_setup):
    """see if we can get all the grammars
    """
    # this works apparently in the normal unimacro_user_directory, first delete _newbie.ini
    inifile_stem = "_newbie"
    userDir = status.getUnimacroUserDirectory()
    commandDir = os.path.join(userDir, status.language +"_inifiles")
    inifile = Path(commandDir)/ f'{inifile_stem}.ini'
    if inifile.is_file():
          inifile.unlink()
       
    newbie = Newbie(inifile_stem="_newbie")
    newbie.initialize()
    assert newbie.ini


if __name__ == "__main__":
    pytest.main(['test_new_inifile_directory.py'])
    