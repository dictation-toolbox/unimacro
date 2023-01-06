
from string import Template
from pathlib import Path
import pytest
from distutils.dir_util import copy_tree
import natlink
from functools import cache
import importlib
from shutil import copy as file_copy
thisDir = Path(__file__).parent

@cache          #only needs to be called once
def unimacro_source_dir() ->Path:
    return Path(importlib.util.find_spec("unimacro").submodule_search_locations[0])

@cache 
def unimacro_sample_ini_dir() ->Path:
    return unimacro_source_dir()/"sample_ini"

 
def copy_grammar_ini(grammar_ini_file: str,unimacro_user_dir:Path):
    source_file=unimacro_sample_ini_dir()/"enx_inifiles"/grammar_ini_file
    target_file=unimacro_user_dir / "enx_inifiles"/grammar_ini_file
    return file_copy(source_file,target_file)
 
#a function to build the fixture to copy a grammar ini file to unimacro user directory.  see sample in test_brackets.py
#the fixture itself will return the same thing to the tests as the unimacro_setup fixture.

def make_copy_grammar_ini_fixture(grammar_ini_file : str):
    @pytest.fixture()
    def grammar_ini_fixture(unimacro_setup):
        copy_grammar_ini(grammar_ini_file,unimacro_setup[1])
        return unimacro_setup
    return grammar_ini_fixture




@pytest.fixture()
def unimacro_setup(tmpdir):
  
    tmp_test_root = tmpdir

    natlink_config_dir=tmp_test_root.mkdir('.natlink')
    unimacro_userdir=tmp_test_root.mkdir("unimacro_user_directory")
    natlink_config_file=natlink_config_dir/"natlink.ini"
    vocola_userdir=tmp_test_root.mkdir("vocola_user_directory")
    natlink_usergrammars_dir=tmp_test_root.mkdir("natlink_user_grammars")
    sub={
        'unimacrotestuserdirectory':unimacro_userdir,
        'vocolatestuserdirectory':vocola_userdir,
        'natlinktestuserdirectory':natlink_usergrammars_dir
    }
    natlinkini_source_folder=Path(__file__).parent / "unimacro_test_natlink_config.natlink"
    natlinkini_source_config = natlinkini_source_folder/"_natlink.ini"
    with open(natlinkini_source_config) as f:
        src=Template(f.read())
        config_file_text=src.substitute(sub)

    print(f"natlink_config_dir: {natlink_config_dir}")
    with open(natlink_config_file,'w') as fw:
        fw.write(config_file_text)
    
    #copy the unimacro user directory to the unimacro_user_directory
    copy_tree(str(thisDir/"test_sample_unimacro_userdir"),str(unimacro_userdir))

    pytest.MonkeyPatch().setenv("NATLINK_USERDIR",str(natlink_config_dir))
    oo=natlink.natConnect()
    yield [natlink_config_dir,unimacro_userdir,oo]
    natlink.natDisconnect()




def test_foo(unimacro_setup):
    pass
 
