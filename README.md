# Unimacro
The Unimacro project aims to provide a rich set of command grammars, that can be configured by the users without programming knowledge. 
Read more at [Natlink, including Unimacro and Vocolaa](https://qh.antenna.nl/unimacro/index.html)

# Installing

Unimacro is reasonably stable, but still in alpha.  Check the [Unimacro Issues](https://github.com/dictation-toolbox/unimacro/issues) to see the problem
areas - probably nothing you can't live without.


## Install unimacro

Install from the [Python Package Index](https://pypi.org/)
with the following.

`pip install unimacro`



# Location of Grammars

Grammars installed with Unimacro will be installed in:
the Lib\site-packages\unimacro\UnimacroGrammars sub-directory of your 
Python installation.  Good ones to start with include _folders.py and _clickbyvoice.py 
as most users will  find web and file system navigation by voice useful.

More about [Unimacro Grammars](https://qh.antenna.nl/unimacro/grammars/globalgrammars/folders/index.html)

# Developer instructions.

If you want to install your local unimacro development environment as the working unimacro:
`pip install -e . `.  

`py -m build` to build the Python package locally.

Publishing to PyPi is done through the [trusted publisher mechanism](https://docs.pypi.org/trusted-publishers/using-a-publisher/) when a release is created on github using github actions. 

BEFORE YOU PUBLISH review the version number of dependencies in pyproject.toml, see if you require newer ones.





