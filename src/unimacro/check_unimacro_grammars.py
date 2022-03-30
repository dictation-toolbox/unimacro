"""check the current state of the unimacro grammar files with the released versions



"""
import os
import shutil
import filecmp
from natlink import natlinkstatus
status = natlinkstatus.NatlinkStatus()

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
        print(f'new release of grammar file, copy to ActiveGrammars {name}')
        shutil.copyfile(org_path, txt_path)
        shutil.copyfile(txt_path, py_path)
        return
    # txt_py not equal
    if org_txt_equal:
        print(f'grammar file {name} in ActiveGrammars changed, please copy to UnimacroGrammars if you are a developer\n\t{py_path} to {org_path}\n\tand {py_path} to {txt_path}')
        return
    # changes AND new release:
    print(f'changes of grammar file {name}, both in UnimacroGrammars and ActiveGrammars')
    print(f'check (yours): {py_path} and {org_path}')
    
        


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

