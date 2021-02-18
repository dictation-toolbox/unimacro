rem -e enable natlink
rem -n set userdirectory to path
rem -o sets the unimacro user directory (ini files)
rem -v enable vocola with user files in path
rem needs elevated mode
C:\python25\python.exe D:\natlink\natlink\confignatlinkvocolaunimacro\natlinkconfigfunctions.py -e -n D:\natlink\unimacro -v %HOME%/vocola_qh -o %HOME%\unimacro_qh -i -I
C:\python26\python.exe D:\natlink\natlink\confignatlinkvocolaunimacro\natlinkconfigfunctions.py -e -n D:\natlink\unimacro -v %HOME%/vocola_qh -o %HOME%\unimacro_qh -i -I

