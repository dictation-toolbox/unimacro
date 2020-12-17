rem this set settings to kaiser_dictation test configuration
rem settings Hawai (C drive for natlink)
rem -e enable natlink
rem -n set userdirectory to path (subdirectory of unimacro)
rem -V disable Vocola
rem -O reset Unimacro User Directory (taking default)
rem -o ~\unimacro for distributed strategy
rem -i (info, can add -I, registry info)
C:\python25\python.exe C:\natlink\natlink\confignatlinkvocolaunimacro\natlinkconfigfunctions.py -e -n C:\natlink\unimacro\kaiser_dictation -O -V -i -o U:\%USERNAME%\natlink

