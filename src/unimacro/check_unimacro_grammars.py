"""check the current state of the unimacro grammar files with the released versions

"""
#pylint:disable=R0912
import os
import shutil
import difflib
import subprocess
from pathlib import Path        
from natlink import natlinkstatus
try:
    from unimacro.__init__ import get_site_packages_dir
except ModuleNotFoundError:
    print('Run this module after "build_package" and "flit install --symlink"\n')

k3diffapp = r'C:\Program Files\KDiff3\kdiff3.exe'
if not os.path.isfile(k3diffapp):
    k3diffapp = None

status = natlinkstatus.NatlinkStatus()
sitePackagesDir = get_site_packages_dir(__file__).lower()
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
    org_txt_equal = not bool( get_diff(org_path, txt_path) )
    
    if not isfile(py_path):
        if not org_txt_equal:
            print(f'\tnew release of not activated grammar {name}\n\t\tcopy {org_path} to {txt_path}')
            shutil.copyfile(org_path, txt_path)
        return 
    txt_py_equal = not bool( get_diff(txt_path, py_path) )
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
            print(f'****grammar {name} in ActiveGrammars changed, copy to UnimacroGrammars\n\t{py_path} to {org_path}\n\tand {py_path} to {txt_path}')
            print(f'--------if you want to revert, revert in git,\n\tand copy manually back "{org_path}"\n\tto "{py_path}"\n--------')
            shutil.copyfile(py_path, org_path)
            shutil.copyfile(org_path, txt_path)
        else:
            print(f'****grammar {name} in ActiveGrammars changed, cannot copy to UnimacroGrammars because you are not developing in symlink mode (with "flit install --symlink")')
        return
    # changes AND new release:
    # one more possibility: org_path and py_path are identical, but txt_path is different:
    org_py_equal = not bool( get_diff(org_path, py_path) )
    if org_py_equal:
        shutil.copyfile(org_path, txt_path)
        return
    
    if have_symlinks:
        print(f'****changes of grammar {name}, both in UnimacroGrammars and ActiveGrammars\n\tcheck (yours): {py_path} and (release) {org_path}')
    else:
        print(f'****changes of grammar {name}, both in UnimacroGrammars and ActiveGrammars,\n\tbut beware, you are not in "symlink" mode (with "flit install --symlink")\n\t\tcheck (yours): {py_path} and (release) {org_path}')
    output_dir = Path(py_path).parent
    output_stem = "====" + Path(py_path).stem + "_diff"
    output_name = output_stem + ".txt"
    if k3diffapp:
        print_diff(org_path, py_path)
    else:
        diff_file = str(Path(output_dir)/output_name)
        print_diff(org_path, py_path, output_file=diff_file)


def get_diff(org_path, new_path):
    """print the diff of org and new
    """
    with open(org_path, 'r') as org:
        with open(new_path, 'r') as new:
            diff = difflib.unified_diff(
                org.readlines(),
                new.readlines(),
                fromfile=f'org: {org_path}',
                tofile=f'new: {new_path}',
            )
            return list(diff) or False

def print_diff(org_path, new_path, output_file=None):
    """do a diff and handle the result"""
    diff = get_diff(org_path, new_path)
    if not diff:
        return
            
    if output_file is None:
        if k3diffapp:
            subprocess.call([k3diffapp, org_path, new_path])
            return
        for line in diff:
            print(line)
        return
    open(output_file, 'w').writelines(diff)
    print(f'----diff in {output_file}')

def cleanup_files(activedir):
    """remove diff files starting with "===="
    """
    cleanupFiles = [f for f in os.listdir(activedir) if f.startswith('====')]
    for f in cleanupFiles:
        os.remove(os.path.join(activedir, f))


def _test_grammar_files():
    join, listdir = os.path.join, os.listdir
    udir = status.getUnimacroDirectory().lower()
    uactivegrammarsdir = status.getUnimacroGrammarsDirectory()

    if udir != sitePackagesDir:
        raise ValueError(f'UnimacroDirectory "{udir}" should be equal to {sitePackagesDir}')
    if have_symlinks:
        uoriginalgrammarsdir = join(workDir, "UnimacroGrammars")
    else:
        uoriginalgrammarsdir = status.getUnimacroGrammarsDirectory()

    originalPyFiles = [f for f in listdir(uoriginalgrammarsdir) if f.endswith('.py')]
    # txtFiles = [f for f in listdir(ugrammarsdir) if f.endswith('.txt')]
    # activePyFiles = [f for f in listdir(ugrammarsdir) if f.endswith('.py')]

    cleanup_files(uactivegrammarsdir)        
        
    for f in originalPyFiles:
        orgpath = join(uoriginalgrammarsdir, f)
        txtfile = f.replace('.py', '.txt')
        txtpath = join(uactivegrammarsdir, txtfile)
        pypath = join(uactivegrammarsdir, f)
        nicename = f[:-3]   # strip off .py
        checkOriginalFileWithActualTxtPy(nicename, orgpath, txtpath, pypath)


        
if __name__ == "__main__":
    _test_grammar_files()   
