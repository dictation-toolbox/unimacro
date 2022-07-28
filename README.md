# Unimacro
The Unimacro project aims to provide a rich set of command grammars, that can be configured by the users without programming knowledge. 
Read more at [Natlink, including Unimacro and Vocolaa](https://qh.antenna.nl/unimacro/index.html)

# Installing

Unimacro is reasonably stable, but still in alpha.  Check the [Unimacro Issues](https://github.com/dictation-toolbox/unimacro/issues) to see the problem
areas - probably nothing you can't live without.



## Install a prerelease of [Python for Win 32](https://github.com/mhammond/pywin32) 
The latest the version of [Python for Win 32](https://github.com/mhammond/pywin32)  in the Python Packing Index (300) has some bugs that affect Unimacro.
So you need to install a later version.

You can download can updated pywin32 from https://github.com/mhammond/pywin32/pull/1622/checks, click on Artifacts,  download the artifacts, extract the files to your computer somehwhere.  

In a shell with administrator privileges, 
`pip install --force-reinstall .\pywin32-300.1-cp38-cp38-win32.whl`.

## Install unimacro

Install from the [Test Python Package Index](https://test.pypi.org/)
with the following.

`pip install --no-cache --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple unimacro`


# Location of Grammars

Grammars installed with Unimacro will be installed in:
the Lib\site-packages\unimacro\UnimacroGrammars sub-directory of your 
Python installation.  Good ones to start with include _folders.py and _clickbyvoice.py 
as most users will  find web and file system navigation by voice useful.

More about [Unimacro Grammars](https://qh.antenna.nl/unimacro/grammars/globalgrammars/folders/index.html)

# Developer instructions.

Follow the instructions for [Natlink](https://test.pypi.org/project/natlinkpy/), replacing 'natlink' with 'unimacro'.
The same commands for building packages and publishing are available in the unimacro root.

If you wish to build or publish a package, there are:

- build_package.ps1 and build_package.ps1 to build the packages.  
- publish_package_pypi.ps1/.cmd to upload the package to the  [Python Packaging Index](https://pypi.org/)
- publish_package_testpypi.ps1/.cmd to upload the packkage to the [Test Python Packaging Index](https://test.pypi.org/)

 
BEFORE YOU PUBLISH review the version number of dependencies in pyproject.toml, see if you require newer ones.





