
from string import Template
from pathlib import Path
import pytest
from distutils.dir_util import copy_tree
import natlink

thisDir = Path(__file__).parent

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
    natlinkini_source_config = natlinkini_source_folder/"natlink.ini"
    with open(natlinkini_source_config) as f:
        src=Template(f.read())
        config_file_text=src.substitute(sub)

    print(f"natlink_config_dir: f{natlink_config_dir}")
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
 
