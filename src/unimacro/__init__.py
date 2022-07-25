"""Unimacro __init__

utility functions, to get calling directory of module (in site-packages),

...and to check the existence of a directory, for example .natlink in the home directory.

Note: -as user, having pipped the package, the scripts run from the site-packages directory
      -as developer, you have to clone the package, then `build_package` and,
       after a `pip uninstall unimacro`, `flit install --symlink`.
       See instructions in the file README.md in the source directory of the package.

get_site_packages_dir: can be called in the calling module like:

```
try:
    from unimacro.__init__ import get_site_packages_dir
except ModuleNotFoundError:
    print('Run this module after "build_package" and "flit install --symlink"\n')

sitePackagesDir = get_site_packages_dir(__file__)
```
"""
import os
import sys

__version__ = '4.1.0'   
 
def get_site_packages_dir(fileOfModule):
    """get directory of calling module, if possible in site-packages
    
    call at top of module with "get_site_packages_dir(__file__)
    
    Check for symlink and presence in site-packages directory (in this case work is done on this repository)
    """
    thisFile = fileOfModule
    thisDir = os.path.split(thisFile)[0]
    thisDir = findInSitePackages(thisDir)
    return thisDir

def findInSitePackages(cloneDir):
    """get corresponding directory in site-packages
    
    If you are developing with `build_package.ps1` (or `build_package.cmd`),
    and this `flit install --symlink`, the directory should be a symlink,

    GOOD: When the package is "flit installed --symlink", so you can work in your clone and
    see the results happen in the site-packages directory. Only for developers

    Otherwise, you just use a pip installed version of this directory, and
    the input directory is returned.
    

    """
    cloneDir = str(cloneDir)
    if cloneDir.find('\\src\\') < 0:
        if cloneDir.find('site-packages') < 0:
            print(f'__init__.findInSitePackages: cloneDir not in "src" area or in "site-packages":\n\t{cloneDir}')
        return cloneDir
    commonpart = cloneDir.split('\\src\\')[-1]
    spDir = os.path.join(sys.prefix, 'Lib', 'site-packages', commonpart)
    if os.path.isdir(spDir):
        spResolve = os.path.realpath(spDir)
        if spResolve == spDir:
            print(f'corresponding site-packages directory is not a symlink: {spDir}.\nPlease use "flit install --symlink" when you want to test this package')
        elif spResolve == cloneDir:
            # print(f'directory is symlink: {spDir} and resolves to {cloneDir} all right')
            return spDir
        else:
            print(f'directory is symlink: {spDir} but does NOT resolve to {cloneDir}, but to {spResolve}')
    else:
        print('findInSitePackages, not a valid directory in site-packages, no "flit install --symlink" yet: {spDir}')
    return cloneDir        
                      