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





