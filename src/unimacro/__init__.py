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


__version__ = '4.1.4.1'   
 
