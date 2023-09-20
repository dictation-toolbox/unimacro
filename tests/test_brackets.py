import pytest
#boilerplate to copy the grammar ini file into the correct location
#just chagne grammar_ini to the name of the grammar ini file you want copied into
#unimacro user directory
grammar_ini= "_brackets.ini"
from conftest import make_copy_grammar_ini_fixture
#grammar_ini_fixture will depend on unimacro_setup, so you dont' need to specfiy unimacro_setup
#as a fixture in your tests.  Though you can
grammar_ini_fixture=make_copy_grammar_ini_fixture(grammar_ini)
#end of boilderplate to copy the gramar ini file into correct location

#leave these first two samples in as documentation in test_brackets.  confests docs say to look in this file for examples.
def test_sample_grammar_ini_fixture1(grammar_ini_fixture):
    assert True

def test_sample_grammar_ini_fixture2(grammar_ini_fixture,unimacro_setup):
    print(f"Unimacro setup sample: {unimacro_setup} grammar_ini_fixutre {grammar_ini_fixture} (should be the same)")
    assert True


import sysconfig,sys
if __name__ == "__main__":
    sysconfig._main()
    print("This is your Python system path sys.path:")
    print("-----------------------------------------")
    print(sys.path)

    pytest.main([f'test_brackets.py'])