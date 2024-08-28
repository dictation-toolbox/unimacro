# Unimacro
The Unimacro project aims to provide a rich set of command grammars, that can be configured by the users without programming knowledge. 
Read more at [Natlink, including Unimacro and Vocolaa](https://qh.antenna.nl/unimacro/index.html)

# Installing

Unimacro is reasonably stable, but still in alpha.  Check the [Unimacro Issues](https://github.com/dictation-toolbox/unimacro/issues) to see the problem
areas - probably nothing you can't live without.

A limited number of grammars are by default available when you install unimacro:

  _control.py
  _general.py 
  _folders.py
  _lines.py
  _brackets.py
  _tags.py
  _tasks.py
  _clickbyvoice.py
  _number simple.py

## Install unimacro

Install from the [Python Package Index](https://pypi.org/)
with the following.

`pip install unimacro`

But... when you install Natlink via the natlink installer, and proceed with "Configure Natlink via GUI" or "Configure Natlink via CLI", and choose to activate Unimacro, this "pip" action is automatically performed. 

If you want to install directly from github (say to install something between releases a developer is working on).

```
pip uninstall unimacro
pip install unimacro@git+https://github.com/dougransom/unimacro@d1cbfb0d9559b9ba656a1d1bb1579f1c2b2562ae
```
replacing "https://github.com/dougransom/unimacro"  with the repository in github you wish to install from and "d1cbfb0d9559b9ba656a1d1bb1579f1c2b2562ae" with the version commit you wish to install.    


# Location of Grammars

The Grammars listed above are installed with Unimacro in:
the Lib\site-packages\unimacro\UnimacroGrammars sub-directory of your 
Python installation.  

More about [Unimacro Grammars](https://qh.antenna.nl/unimacro/grammars/globalgrammars/folders/index.html)

# Developer instructions.

If you want to install your local unimacro development environment as the working unimacro:
`pip install -e .[dev,test] `.  

`py -m build` to build the Python package locally.

To publish a release to [Python Packaging Index](https://pypi.org/), [draft a new release](https://github.com/dictation-toolbox/unimacro/releases). 





