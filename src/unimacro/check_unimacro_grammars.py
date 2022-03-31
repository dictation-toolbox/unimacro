"""check the current state of the unimacro grammar files with the released versions



"""
import os
import shutil
import filecmp
from pathlib import Path        
from natlink import natlinkstatus
try:
    from unimacro.__init__ import get_site_packages_dir
except ModuleNotFoundError:
    print('Run this module after "build_package" and "flit install --symlink"\n')

status = natlinkstatus.NatlinkStatus()
sitePackagesDir = get_site_packages_dir(__file__)
workDir = str(Path(sitePackagesDir).resolve())
have_symlinks = (workDir != sitePackagesDir)
    

def checkOriginalFileWithActualTxtPy(name, org_path, txt_path, py_path):
    """check if grammar has been copied, and changed, with copy of .txt as intermediate
    
    org_path: path to python file in UnimacroGrammars, the original grammars
    txt_path: initially copy of org_path, user area, ActiveGrammars, handled if new release has changes
    py_path:  actual state of active grammar, noted if changes are made
    
    """
    isfile = os.path.isfile
    if not isfile(txt_path):
        shutil.copyfile(org_path, txt_path)
    org_txt_equal = filecmp.cmp(org_path, txt_path)
    
    if not isfile(py_path):
        if not org_txt_equal:
            print(f'new release of not activated grammar {name}\n\tcopy {org_path} to {txt_path}')
        # print(f'not activated grammar "{name}"')
        return 
    txt_py_equal = filecmp.cmp(txt_path, py_path)
    if txt_py_equal:
        if org_txt_equal:
            # all equal
            return
        print(f'\tnew release of grammar file, copy to ActiveGrammars {name}')
        shutil.copyfile(org_path, txt_path)
        shutil.copyfile(txt_path, py_path)
        return
    # txt_py not equal
    if org_txt_equal:
        if have_symlinks:
            print(f'grammar {name} in ActiveGrammars changed, copy to UnimacroGrammars\n\t{py_path} to {org_path}\n\tand {py_path} to {txt_path}')
            shutil.copyfile(py_path, org_path)
            shutil.copyfile(org_path, txt_path)
        else:
            print(f'grammar {name} in ActiveGrammars changed, cannot copy to UnimacroGrammars because you are not developing in symlink mode (with "flit install --symlink")')
        return
    # changes AND new release:
    print(f'changes of grammar {name}, both in UnimacroGrammars and ActiveGrammars')
    print(f'check (yours): {py_path} and (release) {org_path}')

def _test_grammar_files():
    join, listdir = os.path.join, os.listdir
    udir = status.getUnimacroDirectory()
        # uuserdir = status.getUnimacroUserDirectory()
    ugrammarsdir = status.getUnimacroGrammarsDirectory()
    uoriginalgrammarsdir = join(udir, "UnimacroGrammars")
    originalPyFiles = [f for f in listdir(uoriginalgrammarsdir) if f.endswith('.py')]
    
    
    # txtFiles = [f for f in listdir(ugrammarsdir) if f.endswith('.txt')]
    # activePyFiles = [f for f in listdir(ugrammarsdir) if f.endswith('.py')]
        
    for f in originalPyFiles:
        orgpath = join(uoriginalgrammarsdir, f)
        txtfile = f.replace('.py', '.txt')
        txtpath = join(ugrammarsdir, txtfile)
        pypath = join(ugrammarsdir, f)
        nicename = f[:-3]   # strip off .py
        checkOriginalFileWithActualTxtPy(nicename, orgpath, txtpath, pypath)


        
if __name__ == "__main__":
    _test_grammar_files()   

