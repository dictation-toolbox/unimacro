rem this set settings to kaiser_dictation test configuration
rem settings QH, for testing kaiser (D drive for natlink)
rem -e enable natlink
rem -n set userdirectory to path (subdirectory of unimacro)
rem -O reset Unimacro User Directory (taking default)
rem -V disable Vocola
rem -i (info, can add -I, registry info)
C:\python25\python.exe D:\natlink\natlink\confignatlinkvocolaunimacro\natlinkconfigfunctions.py -e -n D:\projects\kaiser_dictation -V -O -i -I 
C:\python26\python.exe D:\natlink\natlink\confignatlinkvocolaunimacro\natlinkconfigfunctions.py -e -n D:\projects\kaiser_dictation -V -O -i -I 
