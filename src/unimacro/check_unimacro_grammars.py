"""check the current state of the unimacro grammar files with the released versions

"""
#pylint:disable=R0912, R0914
import os
import shutil
import difflib
import subprocess
from pathlib import Path        
from natlinkcore import natlinkstatus
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
            org_path_resolved = str(Path(org_path).resolve())
            print(f'****grammar "{name}" in (the active) UnimacroGrammars directory has been changed.')
            print(f'--------This new version "{py_path}" is copied to \n\t"{org_path_resolved}" and to\n\t"{txt_path}".')
            print(f'\tThe changes will be saved when you commit and push your git clone of unimacro, "{workDir}".')
            print(f'--------If you want to undo your changes, revert in git ("{workDir}"),\n\tand copy manually back "{org_path_resolved}"\n\tto "{py_path}".\n--------')
            shutil.copyfile(py_path, org_path_resolved)
            shutil.copyfile(org_path_resolved, txt_path)
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

def checkUnimacroGrammars():
    """see if there are any changed grammar files with respect to original file in release
    
    sync with ...
    """
    join, isdir, isfile, listdir = os.path.join, os.path.isdir, os.path.isfile, os.listdir
    u_dir = status.getUnimacroDirectory()
    # u_user_dir = status.getUnimacroUserDirectory()
    u_grammars_dir = status.getUnimacroGrammarsDirectory()
    u_original_grammars_dir = join(u_dir, "UnimacroGrammars")
    assert isdir(u_original_grammars_dir)
    originalPyFiles = [f for f in listdir(u_original_grammars_dir) if f.endswith('.py')]
    txtFiles = [f for f in listdir(u_grammars_dir) if f.endswith('.txt')]
    activePyFiles = [f for f in listdir(u_grammars_dir) if f.endswith('.py')]
    
    for f in originalPyFiles:
        org_path = join(u_original_grammars_dir, f)
        txt_file = f.replace('.py', '.txt')
        txt_path = join(u_grammars_dir, txt_file)
        py_path = join(u_grammars_dir, f)
        nice_name = f[:-3]   # strip off .py
        checkOriginalFileWithActualTxtPy(nice_name, org_path, txt_path, py_path)
        
    for f in txtFiles:
        f_py = f.replace('.txt', '.py')
        if f_py not in originalPyFiles:
            print(f'txt file "{f}" in ActiveGrammars, but py file {f_py} not in UnimacroGrammars')
            os.remove(f)
            
    for f in activePyFiles:
        f_txt = f.replace('.py', '.txt')
        if not isfile(f_txt):
            if f in originalPyFiles:
                nice_name = f[:-3]   # strip off .py
                org_path = join(u_original_grammars_dir, f)
                txt_path = join(u_grammars_dir, f_txt)
                py_path = join(u_grammars_dir, f)
                checkOriginalFileWithActualTxtPy(nice_name, org_path, txt_path, py_path)

        
if __name__ == "__main__":
    checkUnimacroGrammars()   

