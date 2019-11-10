__version__ = "$Rev: 610 $ on $Date: 2019-09-02 09:47:47 +0200 (ma, 02 sep 2019) $ by $Author: quintijn $"
# This file is part of a SourceForge project called "unimacro" see
# https://unimacro.SourceForge.net and https://qh.antenna.nl/unimacro
# (c) copyright 2003 see https://qh.antenna.nl/unimacro/aboutunimacro.html
#    or the file COPYRIGHT.txt in the natlink\natlink directory 
#
#  grammar: _folders.py
# Written by: Quintijn Hoogenboom (QH softwaretraining & advies)
# starting 2003, revised QH march 2011
#
"""with this grammar, you can reach folders, files and websites from any window.
From some windows (my computer and most dialog windows) the folders and files
can be called directly by name if they are in the foreground.

If you are in a child window (often a file dialog window) the specified
folder is put into the filename text box, if you are in the Windows
Explorer or in the Internet Explorer file or drive is put in the
address text box, and otherwise a new window is opened with the
specified folder.

This grammar now makes use of ini files, to show and edit the contents
of the lists used.

Several "meta actions" are used, eg <<    # f = r'C:\Documenten\Quintijn'
    # remote = r'C:\DocumentenOud'
    # print getValidPath(f, remote)
nameenter>> and <<filename
exit>> when entering were exiting the file name text box in a file
dialog. These actions can be tailored for specific programs, like
some office programmes to behave different, or for WinZip. See examples
in actions.ini (call with "Edit Actions"/"Bewerk acties")

In the inifile also the commands for start this computer or start
windows explorer must be given. Correct these commands ("Edit
Folders"/"Bewerk folders") if they do not work correct.
New feature: if you want to use xxexplorer (can be used hands-free very
easy, look in https://www.netez.com/xxExplorer), in section [general]
you can put a variable

xxexplorer = path to exe or false ('')

This explorer is then taken if you are in or if Explorer is explicitly asked for.

The strategy for "New" and "Explorer" (when you say "new", "nieuw",
"explorer" in the folder command, are complicated, look below

The site part is only used if you enter a valid folder in siteRoot below.
With this command you can quickly enter a complicated set of there we go agains.

The subversion additional commands are only valid if you specify a valid subversion
client in the ini file general section. (subversion executable, I (Quintijn) use TortoiseSvn)
The git additional commands are only valid if you specify a valid git client in the ini file general section
(git executable) (I (Quintijn) take git, although I use TortoiseGit manually)

"""            
import six
import types
import re
import copy
import natlink
import nsformat # for "remember as"
import os
import sys
import time
import fnmatch
import win32gui, win32con
from win32com.client import Dispatch
import pywintypes
import inivars  # for IniError
import utilsqh
from utilsqh import path
import readwritefile
import messagefunctions as mess
import natlinkclipboard
#, win32com
import natlinkcorefunctions # getExtendedEnv
from actions import doAction as action
from actions import doKeystroke as keystroke
from utilsqh import getValidPath
from actions import do_YESNO as YesNo
from actions import Message, UnimacroBringUp
from unimacro_wxpythondialogs import InputBox

import webbrowser
import urllib
natut = __import__('natlinkutils')
natqh = __import__('natlinkutilsqh')
natbj = __import__('natlinkutilsbj')

# for getting unicode explorer window titles:
import ctypes
GetWindowText = ctypes.windll.user32.GetWindowTextW
GetWindowTextLength = ctypes.windll.user32.GetWindowTextLengthW
import win32clipboard

# for substituting environment variable like %HOME% in a file path:
# and %DESKTOP% in a file path.
# %HOME% defaults to your my documents folder, but can be in the system environment variables.
reEnv = re.compile('%([A-Z_]+)%')
reOnlyLowerCase = re.compile(r'^[a-z]+$')
reLettersSpace = re.compile(ur'^[ \w]+$', re.UNICODE)
###########################################################
# for alternatives in virtual drive definitions:
reAltenativePaths = re.compile(r"(\([^|()]+?(\|[^|()]+?)+\))")

# classes for this computer and windows explorer:
Classes = ('ExploreWClass', 'CabinetWClass')

# extra for sites (QH)
try:
    siteRoot = getValidPath('(C|D):\\projects\\sitegen')
except IOError:
    siteRoot = None
if siteRoot:
    print "grammar _folder: do specific site commands (QH private)"
    if not siteRoot.normpath() in sys.path:
        print 'append to sys.path: %s'% siteRoot
        sys.path.append(siteRoot)


# together with track folders history:
doRecentFolderCommand = True
# some child windows have to behave as top window (specified in ini file):
# note: title is converted to lowercase, only full title is recognised

ancestor = natbj.IniGrammar
class ThisGrammar(ancestor):
    """grammar for quickly going to folders, files and websites
    """    

    language = natqh.getLanguage()
    name = "folders"
    iniIgnoreGrammarLists = ['subfolders', 'subfiles'] # on the fly in CabinetWClass
    
    # commands with special status, must correspond to a right hand side
    # of a ini file entry (section foldercommands or filecommands)
    # remote, subversion, openwith have hardcoded details.
    optionalfoldercommands = ['new', 'explorer', 'paste', 'copy', 'remote', 'subversion', 'git']
    optionalfilecommands = ['copy', 'paste', 'edit', 'paste', 'remote', 'subversion', 'openwith', 'git']

    # only used if siteRoot is a valid folder
    optionalsitecommands = ['input', 'output', 'local', 'online']
    
    gramSpec = """
<folder> exported = folder ({folders}[<foldercommands>]);
<subfolder> exported = subfolder {subfolders}[<foldercommands>|<remember>];
<disc> exported = drive {letters} [<foldercommands>];  # add + later again
<thisfolder> exported = ((this|here) folder) (<foldercommands>|<remember>);
<foldercommands> = {foldercommands}| on ({letters}|{virtualdrivesspoken}) |
                    (subversion) {subversionfoldercommands}|
                    (git) {gitfoldercommands}|
                    <namepathcopy>;
                   
<folderup> exported = folder up|folder up {n1-10};
<file> exported = file ({files}|{subfiles})[<filecommands>|<remember>];  # add dot {extensions} later again
<thisfile> exported = ((here|this) file) (<filecommands>|<remember>); 
<filecommands> = {filecommands}| on ({letters}|{virtualdrivesspoken}) |
                ('open with') {fileopenprograms}|
                (subversion) {subversionfilecommands}|
                (git) {gitfilecommands}|
                <namepathcopy>;

<website> exported = website {websites} [<websitecommands>]; 
<thiswebsite> exported = (this website) (<websitecommands>|<remember>);
<websitecommands> = ('open with') {websiteopenprograms}|
                    <namepathcopy>;
<remember> = remember;
<namepathcopy> = (copy (name|path)) | ((name|path) copy);
## set all environment variables into the folders list...
<setenvironmentfolders> exported =  set environment folders;

"""
    # specific part in use by Quintijn:
    if siteRoot:
        print 'extend grammar with site specific (QH private) commands'
        gramSpec = gramSpec + """
<site> exported = site ({sites}|{sites} <sitecommands>);
<siteshort> exported = site <sitecommands>;
<sitecommands> = {sitecommands} | {sitecommands} (<foldercommands>|<websitecommands>) |
                    <foldercommands> | <websitecommands>;
        """
        
    if doRecentFolderCommand:
        gramSpec += """<recentfolder> exported = recent folders;"""

    def initialize(self):
        if not self.language:
            print "no valid language in grammar "+__name__+" grammar not initialized"
            return
        
        self.load(self.gramSpec)
        self.lastSite = None
        self.switchOnOrOff() # initialises lists from inifile, and switches on
                             # if all goes well (and variable onOrOff == 1)
        self.envDict = natlinkcorefunctions.getAllFolderEnvironmentVariables()   # for (generalised) environment variables
        self.subfiles = self.subfiles = self.activeFolder = None  # for catching on the fly in explorer windows (CabinetClassW)
        self.className = None
        self.recentFoldersList = [] # for auto tracking active folders...
        self.dialogWindowTitle = "" # for recent folders dialog, grammar in natspeak.py
        self.dialogNumberRange = [] # ditto
        self.catchRemember = ""
        self.activeFolder = None
        
    def gotBegin(self,moduleInfo):
        if self.checkForChanges:
            self.checkInifile() # refills grammar lists and instance variables
                                # if something changed.
            if type(self.checkForChanges) == types.IntType and self.checkForChanges > 0:
                self.checkForChanges -= 1
              
        if self.mayBeSwitchedOn == 'exclusive':
            print "exclusive (_folders), do switchOnOrOff"
            self.switchOnOrOff()
        hndle = moduleInfo[2]
        try:
            className = win32gui.GetClassName(hndle)
        except pywintypes.error, details:
            print "no classname found"
            className = ""

        activeFolder = self.getActiveFolder(hndle, className)
        if self.trackAutoFiles or self.trackAutoFolders:
            activeFolder = self.getActiveFolder(hndle, className)
            if activeFolder:
                self.handleTrackFilesAndFolders(activeFolder)
        
        if hndle and self.trackFoldersHistory:
            self.manageRecentFoldersList(hndle)
            
    def gotResultsInit(self,words,fullResults):
        if self.mayBeSwitchedOn == 'exclusive':
            print 'recog folders, switch off mic'
            natbj.SetMic('off')
        self.wantedFolder = self.wantedFile = self.wantedWebsite = None
        self.catchRemember = None
        self.gotFolder = self.gotFile = self.gotWebsite = False ## for catching 

    def handleTrackFilesAndFolders(self, activeFolder):
        """set or empty lists for activeFolder and set/reset self.activeFolder
        """
        if self.activeFolder == activeFolder:
            return
        if self.activeFolder:
            self.emptyListsForActiveFolder()
            # print 'empty lists for active folder %s, now: %s'% (self.activeFolder, activeFolder)
            self.activeFolder = None

        if activeFolder and os.path.isdir(activeFolder):
            self.fillListsForActiveFolder(activeFolder)
            print 'set %s (sub)files and %s subfolders'% (len(self.subfilesDict), len(self.subfoldersDict))


    def fillList(self, listName):
        """fill a list in the grammar from the data of the inifile

        overload, because the list sites is special:reversed
        the section [site] must exist,on the right side is to spoken form.
        """
        #print 'fill list', listName
        if listName == 'sites':
            if not siteRoot:
                print 'sites rules ignored'
                self.emptyList(listName)
                return #  skip the site part
            self.sitesDict = self.getListOfSites(siteRoot)
            items = self.sitesDict.keys()
            self.setList(listName, items)
            self.ini.writeIfChanged()
            self.sitesInstances = {}  # to be filled with instance of a site
            return items
            
        elif listName == 'folders':
            if self.foldersDict:
                items = self.foldersDict.keys()
                self.setList('folders', items)
                return items
            else:
                print 'no folders to set list to'
                self.emptyList('folders')
        elif listName == 'subfolders':
            if self.subfoldersDict:
                items = self.subfoldersDict.keys()
                self.setList('subfolders', items)
                return items
            else:
                print 'no subfolders to set list to'
                self.emptyList('subfolders')

        elif listName == 'files':
            if self.filesDict:
                items = self.filesDict.keys()
                self.setList('files', items)
                return items
            else:
                print 'no files to set list to, edit _folders.ini if you wish to call individual files...'
                self.emptyList('files')
        elif listName in ['subversionfilecommands', 'subversionfoldercommands']:
            if self.doSubversion:
                return ancestor.fillList(self, listName)
            else:
                self.emptyList(listName)
        elif listName in ['gitfilecommands', 'gitfoldercommands']:
            if self.doGit:
                return ancestor.fillList(self, listName)
            else:
                self.emptyList(listName)
        else:
            return ancestor.fillList(self, listName)

    def fillInstanceVariables(self):
        """fills the necessary instance variables
          take the lists of folders, virtualdrives (optional) and remotedrives (optional).
        
        """
        self.citrixApps = self.ini.getList('general', 'citrix apps')
        if self.citrixApps:
            print '_folders does special action for citrixApps: %s'% self.citrixApps
        self.xxExplorer = self.ini.get('general', '2xexplorer')
        self.useOtherExplorer = self.ini.get('general', 'use other explorer')
        if self.useOtherExplorer:
            if os.path.isfile(self.useOtherExplorer):
                print '_folders, use as default explorer: "%s"'% self.useOtherExplorer
            else:
                print '_folders, variable "use other explorer" set to: "%s" (use data from "actions.ini")'% self.useOtherExplorer
            
        ## automatic tracking of recent folders :
        self.trackFoldersHistory = self.ini.getInt('general', 'track folders history')
        if self.trackFoldersHistory:
            print 'maintain a list of %s recent folders (Explorer of File Dialog) at every utterance and every second'% self.trackFoldersHistory
            natlink.setTimerCallback(self.manageRecentFoldersList, 1000)  # every 1000 milliseconds
        # extract special variables from ini file:
        self.virtualDriveDict = {}
        wantedVirtualDriveList = self.ini.get('virtualdrives')
        if wantedVirtualDriveList:
            self.resolveVirtualDrives(wantedVirtualDriveList)
        self.virtualDriveList = self.virtualDriveDict.keys()
        # print '_folders, virtual drives from dict: %s'% repr(self.virtualDriveDict)
        # print '_folders, virtual drives from list: %s'% ', '.join(self.virtualDriveList)

        #  checking the passes of all folders:
        foldersList = self.ini.get('folders')
        self.foldersDict = {}
        for f in foldersList:
            folder = self.substituteFolder(self.ini.get('folders', f))
            if not os.path.isdir(folder):
                print 'warning _folders,  folder "%s" does not exist (move away): "%s"'% (f, folder)
                self.ini.delete('folders', f)
                self.ini.set('obsolete folders', f, folder)
                continue
            f = utilsqh.convertToBinary(f)
            self.foldersDict[f] = folder
        
        # track virtual drives if in ini file:
        self.trackFolders = self.ini.getList('general', 'track folders virtualdrives')
        self.trackFiles = self.ini.getList('general', 'track files virtualdrives')
        self.notifyThresholdMilliseconds = self.ini.getInt("general", "notify threshold milliseconds", 10)
        print "_folders, notify threshold milliseconds: %s"% self.notifyThresholdMilliseconds
        # in order to accept .py but it should be (for fnmatch) *.py etc.:
        self.acceptFileExtensions = self.ini.getList('general', 'track file extensions')
        self.ignoreFilePatterns = self.ini.getList('general', 'ignore file patterns')
        
        # these are for automatic tracking the current folder:
        self.trackAutoFolders = self.ini.getBool('general', 'automatic track folders')
        self.trackAutoFiles = self.ini.getBool('general', 'automatic track files')
        windowsVersion = natqh.getWindowsVersion()
        if (self.trackAutoFiles or self.trackAutoFolders) and  windowsVersion in ('XP', '2000', 'NT4', 'NT351', '98'):
            print '_folders: the options for "automatic track files" and "automatic track folders" of a directory probably do not work for this Windows version: %s'% windowsVersion
            
        self.doSubversion = self.ini.get('general', 'subversion executable')
        if self.doSubversion:
            if not os.path.isfile(self.doSubversion):
                print 'not a valid path to subversion executable: %s, ignore'% self.doSubversion
                self.doSubversion = None
        if not self.doSubversion:
            self.iniIgnoreGrammarLists.extend(['subversionfoldercommands', 'subversionfilecommands'])
            
        self.doGit = self.ini.get('general', 'git executable')
        if self.doGit:
            if not os.path.isfile(self.doGit):
                print 'not a valid path to git executable: %s, ignore'% self.doGit
                self.doGit = None
        if not self.doGit:
            self.iniIgnoreGrammarLists.extend(['gitfoldercommands', 'gitfilecommands'])
                
        self.foldersSections = ['folders']
        # track folders:
        for trf in self.trackFolders:
            if not trf:
                continue
            trf2 = self.substituteFolder(trf)
            #print 'input: %s, output: %s'% (trf, trf2)
            if not os.path.isdir(trf2):
                print 'warning, no valid folder associated with: %s (%s) (skip for track virtualdrives)'% (trf, trf2)
                continue
            #else:
            #    print 'valid folder for tracking: %s (%s)'% (trf, trf2)
            subf = [f for f in os.listdir(trf2) if os.path.isdir(os.path.join(trf2, f))]
            self.trackFoldersSection = 'folders %s'% trf
            self.ini.delete(self.trackFoldersSection)  # not in inifile
            self.foldersSections.append(self.trackFoldersSection)
            self.acceptVirtualDrivesFolder(trf, trf2) # without f, take virtualdrive itself...
            for f in subf:
                ## if no strange signs in folder name:
                self.acceptVirtualDrivesFolder(trf, trf2, f)
            #self.cleanupIniFoldersSection(self.trackFoldersSection, trf)
        #self.removeObsoleteIniSections(prefix="folders ", validPostfixes=self.trackFolders)
        self.removeObsoleteIniSections(prefix="folders ", validPostfixes=[])  # do not keep in ini file
 
        # do the files:
        self.filesDict = {}
        self.trackFiles = self.ini.getList('general', 'track files virtualdrives')
        # in order to accept .py but it should be (for fnmatch) *.py etc.:
        self.acceptFileExtensions = self.ini.getList('general', 'track file extensions')
        self.ignoreFilePatterns = self.ini.getList('general', 'ignore file patterns')
        self.filesSections = ['files']
        # from section files (manual):
        filesList = self.ini.get('files')
        for f in filesList[:]:
            filename = self.substituteFilename(self.ini.get('files', f))
            if not os.path.isfile(filename):
                print 'warning _folders, file "%s" does not exist: "%s"'% (f, filename)
                self.ini.delete('files', f)
                self.ini.set('obsolete files', f, filename)
                continue
            self.filesDict[f] = filename

        for trf in self.trackFiles:
            if not trf:
                continue
            trf2 = self.substituteFolder(trf)
            if not os.path.isdir(trf2):
                print 'warning, no valid folder associated with: %s (%s) (skip for track files)'% (trf, trf2)
                continue
            filesList = [f for f in os.listdir(trf2) if os.path.isfile(os.path.join(trf2, f))]
            self.trackFilesSection = 'files %s'% trf
            self.ini.delete(self.trackFoldersSection)  # not in inifile
            self.filesSections.append(self.trackFilesSection)
            for f in filesList:
                self.acceptFileInFilesDict(trf, trf2, f)
            #self.cleanupIniFilesSection(self.trackFilesSection, trf)
        self.removeObsoleteIniSections(prefix="files ", validPostfixes=[])
        #self.removeObsoleteIniSections(prefix="files ", validPostfixes=self.trackFiles) # not in inifile any more

        # self.childBehavesLikeTop = self.ini.getDict('general', 'child behaves like top')
        # self.topBehavesLikeChild = self.ini.getDict('general', 'top behaves like child')
        # save changes if there were any:
        self.ini.writeIfChanged()        

    
    def resolveVirtualDrives(self, wantedVirtualDrives):
        """check the virtual drives, possibly recursive
        
        the valid virtual drives are put in self.virtualDriveDict
        the invalid virtual drives are sent to the obsolete virtual drives section
        
        no return, self.virtualDriveDict is filled.
        if no progress, make the remaining virtual drives obsolete...
        """
        if not wantedVirtualDrives: return ## nothing done
        lenPrevious = 0
        #checking the paths of virtualDriveList:
        while wantedVirtualDrives and lenPrevious != len(wantedVirtualDrives):
            lenPrevious = len(wantedVirtualDrives)
            # print "resolveVirtualDrives, %s to go: %s"% (lenPrevious, wantedVirtualDrives)
            for dr in wantedVirtualDrives[:]:
                virtualDrive = self.ini.get('virtualdrives', dr)
                folder = self.getFolderFromVirtualDrive(virtualDrive)
                if folder:
                    # print 'accept virtual drive: %s for: %s'% (dr, folder)
                    self.virtualDriveDict[dr] = folder
                    wantedVirtualDrives.remove(dr)
                    self.ini.delete('obsolete virtualdrives', dr) # just in case
        
        if wantedVirtualDrives:
            print 'could not resolve "virtualdrive" entries: %s, move to section "obsolete virtualdrives"'% ", ".join(wantedVirtualDrives)
            for dr in wantedVirtualDrives:
                virtualDrive = self.ini.get('virtualdrives', dr)
                self.ini.delete('virtualdrives', dr)
                self.ini.set('obsolete virtualdrives', dr, virtualDrive)


    def getFolderFromVirtualDrive(self, vd):
        """check validity of virtual drive contents
        also make alternative paths possible  like (C|D):/Documents
        """
        # natlinkcorefunctions.printAllEnvVariables()
        vd = natlinkcorefunctions.expandEnvVariables(vd)
        for possiblePath in loop_through_alternative_paths(vd):
            folder = self.substituteFolder(possiblePath)
            if os.path.isdir(folder):
                return os.path.normpath(folder)
                

    def acceptVirtualDrivesFolder(self, vd, realfolder, foldername=None):
        """check validity of virtualdrive subfolder and put or remove from inifile
    
        not used any more, the contents of a VirtualDrivesFolder are not kept in inifile
        add to foldersDict if applicable
        
        """
        if foldername is None:
            #print 'virtual drive: %s, %s'% (vd, realfolder)
            f = vd
        else:
            f = foldername
        if not reLettersSpace.match(f):  # take only readable/speakable, only those are accepted by inivars
            # print('acceptVirtualDrivesFolder, skipping: %s (%s)'% (f, type(f)))
            return  # nothing to do
        section = self.trackFoldersSection
        spoken = self.ini.getList(section, f, ['xpqzyx'])
        spoken = filter(None, spoken)
        if spoken == ['xpqzyx'] or not spoken:
            if foldername:
                spoken = [f]
            else:
                spoken = [vd,  os.path.split(realfolder)[-1]]
                if spoken[0] == spoken[1]:
                    spoken = spoken[:1]
                #print 'spoken for virtual drive: %s'% spoken
            # self.ini.set(section, f, spoken)
        #else:
        if not spoken:
            return
        for sp in spoken:
            if type(sp) == six.text_type:
                sp = utilsqh.convertToBinary(sp)
            if foldername:
                try:
                    self.foldersDict[sp] = vd + ':/' +  foldername
                except UnicodeDecodeError:
                    vd = utilsqh.convertToBinary(vd)
                    foldername = utilsqh.convertToBinary(foldername)
                #     print("---------------vd: %s(%s) foldername: %s(%s)"(vd, type(vd), foldername, type(foldername)))
            else:
                self.foldersDict[sp] = vd 

    def getActiveFolder(self, hndle=None, className=None):
        """get active folder (only explorer and dialog #32770)
        """
        if hndle is None:
            curmod = natlink.getCurrentModule()
            hndle = curmod[2]
            print "hndle: %s, mod: %s"% (hndle, repr(curmod))
        if not hndle:
            print "getActiveFolder, not a foreground hndle found: %s"% hndle
            return
        if className is None:
            className = win32gui.GetClassName(hndle)
        # print 'getActiveFolder, className: %s'% className
        if not className: return
        f = None
        if className == "CabinetWClass":
            f = mess.getFolderFromCabinetWClass(hndle)
            # if f and f.startswith("search-ms"):
            #     keystroke("{esc}")
            #     natqh.Wait()
            #     f = mess.getFolderFromDialog(hndle, className)
            if not f:
                print "getActiveFolder, CabinetWClass failed: %s"% hndle
        elif className == '#32770':
            f = mess.getFolderFromDialog(hndle, className)
            if not f:
                return
            # if not f:
            #     print "getActiveFolder, #32770 failed: %s"% hndle
        else:
            # print 'class for activeFolder: %s'% className
            return
        if not f:
            if className == 'CabinetWClass':
                print '_folders, getActiveFolder, no folder found in className %s'% className
            return
        if os.path.isdir(f):
            return f
        realFolder = natlinkcorefunctions.getFolderFromLibraryName(f)
        if realFolder:
            return realFolder
        print '_folders, getActiveFolder, could not find folder for %s'% f

    def fillListsForActiveFolder(self, activeFolder):
        """fill list of files and subfolders
        also set activeFolder and className
        
        this is for the automatic filling of the active window (either explorer, CabinetWClass,
        or child #32770.
        
        Seems to fail in windows XP and before.
        
        """
        subs = [utilsqh.convertToUnicode(s) for s in os.listdir(activeFolder)]
        # print 'subs: %s'% subs
        subfolders = [s for s in subs if os.path.isdir(os.path.join(activeFolder, s))]
        subfiles = [s for s in subs if os.path.isfile(os.path.join(activeFolder, s))]
        self.subfoldersDict = self.getSpokenFormsDict(subfolders)
        self.subfilesDict = self.getSpokenFormsDict(subfiles, extensions=1)
        # print 'activeFolder, %s, subfolders: %s'% (activeFolder, self.subfoldersDict.keys())
        # print 'activeFolder, %s, subfiles: %s'% (activeFolder, self.subfilesDict.keys())
        # print 'activeFolder, %s, subfiles: %s'% (activeFolder, self.subfilesDict)
        if self.trackAutoFiles and self.subfilesDict:
            self.setList('subfiles', self.subfilesDict.keys())
        if self.trackAutoFolders and self.subfoldersDict:
            n0 = time.time()
            self.setList('subfolders', self.subfoldersDict.keys())
            n1 = time.time()
            elapsed = int((n1 - n0)*1000)
            if elapsed > self.notifyThresholdMilliseconds:
                print 'set %s subfolders in %s milliseconds'% (len(self.subfoldersDict.keys()), elapsed)
        self.activeFolder = activeFolder

    def emptyListsForActiveFolder(self):
        """no sublists, empty
        """
        n0 = time.time()
        lenSubFolders = len(self.subfoldersDict)
        lenSubFiles = len(self.subfilesDict)
        if self.trackAutoFiles:
            self.emptyList('subfiles')
            self.subfilesDict.clear()
        if self.trackAutoFolders:
            self.emptyList('subfolders')
            self.subfoldersDict.clear()
        n1 = time.time()
        elapsed = int((n1 - n0)*1000)
        if elapsed:
            # if elapsed > self.notifyThresholdMilliseconds:
            print 'emptyListsForActiveFolder: emptied %s subfolders and %s (sub)files in %s milliseconds'% (lenSubFolders, lenSubFiles, elapsed)
        self.activeFolder = None


    def cleanupIniFoldersSection(self, section, vd):
        """cleanup the current ini folder ... section (for non existing folders)
        """
        section = self.trackFoldersSection
        for f in self.ini.get(section):
            if f == vd:
                continue
            folder = self.substituteFolder(vd + ':/' + f)
            if not os.path.isdir(folder):
                print 'remove entry from ini folders section %s: %s (%s)'% (section, f, folder)
                self.ini.delete(section, f)
            elif not self.acceptFileName(f):
                print 'remove entry from ini folders section %s: %s (%s)(invalid folder name)'% (section, f, folder)
                self.ini.delete(section, f)
        self.ini.writeIfChanged()

    def cleanupIniFilesSection(self, section, vd):
        """cleanup the current ini files ... section (for non existing files)
        """
        for f in self.ini.get(section):
            filename = self.substituteFolder(vd + ':/' + f)
            trunk, ext = os.path.splitext(f)
            if not self.acceptExtension(ext):
                print 'remove entry from ini files section %s: %s (%s)(invalid extension)'% (section, f, filename)
                self.ini.delete(section, f)
            elif not self.acceptFileName(trunk):
                print 'remove entry from ini files section %s: %s (%s)(invalid filename)'% (section, f, filename)
                self.ini.delete(section, f)
            elif not os.path.isfile(filename):
                print 'remove entry from ini files section %s: %s (%s)'% (section, f, filename)
                self.ini.delete(section, f)
        self.ini.writeIfChanged()

    def removeObsoleteIniSections(self, prefix, validPostfixes):
        """remove sections that do NOT conform to prefix+ one of the postfixes
        (these were in "track files virtualdrives" or in "track folders virtualdrives"
        but have been removed in the inifile definition)
        """
        prefix = prefix.strip() + " "
        for section in self.ini.get():
            if not section.startswith(prefix):
                continue
            for postfix in validPostfixes:
                if section == prefix + postfix:
                    break
            else:
                print '_folders grammar, deleting ini file section: %s'% section
                self.ini.delete(section)
        self.ini.writeIfChanged()

    def acceptFileInFilesDict(self, vd, realfolder, filename):
        """check validity of filename in subfolder and put/remove in/from inifile
    
        add to filesDict if applicable
        
        """
        f = filename
        trunk, ext = os.path.splitext(f)
        if not self.acceptExtension(ext):
            return
        if not self.acceptFileName(trunk):
            return
                
        section = self.trackFilesSection
        spoken = self.ini.getList(section, f, ['xpqzyx'])
        spoken = filter(None, spoken)
        if spoken == ['xpqzyx'] or not spoken:
            spoken = [trunk]
            # skip if error in inivars:
            #try:
            #    self.ini.set(section, f, spoken)
            #except inivars.IniError:
            #    return

        if not spoken: return
        
        for sp in spoken:
            self.filesDict[sp] = vd + ':/' +  f
       
    def manageRecentFoldersList(self, hndle=None, className=None):
        return
        activeFolder = self.getActiveFolder(hndle, className)
        if not activeFolder: return
        
        activeFolder = os.path.normcase(activeFolder)
        
        if activeFolder in self.recentFoldersList:
            if activeFolder == self.recentFoldersList[0]:
                #print 'no change: %s'% activeFolder
                return
            else:
                self.recentFoldersList.remove(activeFolder)
        if len(self.recentFoldersList) >= self.trackFoldersHistory:
            removeItem = self.recentFoldersList.pop()
            print 'remove from recent folders list: %s'% removeItem
            
        self.recentFoldersList.insert(0, activeFolder)
        #self.displayRecentFoldersList()
        
    def displayRecentFoldersList(self):
        """display the list of recent folders
        """
        for i, item in enumerate(self.recentFoldersList):
            print '%s: %s'% (i+1, item)
        print '-'*20
        
    def gotoRecentFolder(self, chooseNum):
        """service function which can be called from natspeak_dialog
        pass the number of the choicelist (0 based)
        """
        wantedFolder = self.recentFoldersList[chooseNum]
        self.gotoFolder(wantedFolder)
       
    def gotResults_siteshort(self,words,fullResults):
        """switch to last mentioned site in the list
        mainly for private use, a lot of folders reside in the root folder,
        siteRoot.  They all have an input folder and a output folder.


        """
        if self.lastSite:
            words.insert(1, self.lastSite)
            print 'lastSite: %s'% words
            self.gotResults_site(words, fullResults)
        else:
            self.DisplayMessage('no "lastSite" available yet')


    def gotResults_setenvironmentfolders(self,words,fullResults):
        """switch to last mentioned site in the list
        mainly for private use, a lot of folders reside in the root folder,
        siteRoot.  They all have an input folder and a output folder.


        """
        reverseOldValues = {'ignore': []}
        for k in self.ini.get('folders'):
            val = self.ini.get('folders', k)
            if val:
                reverseOldValues.setdefault(val, []).append(k)
            else:
                reverseOldValues['ignore'].append(k)
        reverseVirtualDrives = {}
        for k in self.ini.get('virtualdrives'):
            val = self.ini.get('virtualdrives', k)
            reverseVirtualDrives.setdefault(val, []).append(k)
            
##        print reverseOldValues
        allFolders = self.envDict()  #  natlinkcorefunctions.getAllFolderEnvironmentVariables()  
        kandidates = {}
        ignore = reverseOldValues['ignore']
        for (k,v) in allFolders.items():
            kSpeakable = k.replace("_", " ")
            if k in ignore or kSpeakable in ignore:
                continue
            oldV = self.ini.get('folders', k, "") or self.ini.get('folders', kSpeakable)
            if oldV:
                vPercented = "%" + k + "%"
                if oldV == v:
                    continue
                elif oldV == vPercented:
                    kPrevious = reverseOldValues[vPercented]
##                    print 'vPercented: %s, kPrevious: %s'% (vPercented, kPrevious)
                    if  vPercented in reverseOldValues:
                        if k in kPrevious or kSpeakable in kPrevious:
                            continue
                        else:
                            print 'already in there: %s (%s), but spoken form changed to %s'% \
                              (k, v, kPrevious)
                            continue
                else:
                    print 'different for %s: old: %s, new: %s'% (k, oldV, v)
            kandidates[k] = v
        count = len(kandidates)
        
        if not kandidates:
            self.DisplayMessage("no new environment variables to put into the folders section")
            return
        mes = ["%s new environment variables for your folders section of the grammar _folders"% count]
        
        Keys = kandidates.keys()
        Keys.sort()
        for k in Keys:
            mes.append("%s\t\t%s"% (k, kandidates[k]))

        mes.append('\n\nDo you want these new environment variables in your folders section?')
                       
                

        if YesNo('\n'.join(mes)):
            for (k,v) in kandidates.items():
                if k.find('_') > 0:
                    kSpeakable = k.replace("_", " ")
                    if self.ini.get('folders', k):
                        self.ini.delete('folders', k)
                else:
                    kSpeakable = k
                self.ini.set('folders', kSpeakable, "%" + k + "%")
            self.ini.write()
            self.DisplayMessage('added %s entries, say "Show|Edit folders" to browse'% count)
        else:
            self.DisplayMessage('nothing added, command canceled')
            

    def gotResults_website(self,words,fullResults):
        """start webbrowser, websites in inifile unders [websites]
        
        if www. is not given insert, if https:// is not given insert it.

        so if you have an old http:// or eg qh.antenna.nl you MUST insert http:// or https://

        if <dgndictation> try google!!

        """
        if len(words) == 1 and self.nextRule == 'dgndictation':
            self.waitForDictation = 'website'
            return

        site = self.getFromInifile(words, 'websites')
        if site.startswith("http:") or site.startswith("https:"):
            pass
        else:
            site = "https://"+site
        if ((site.startswith('http:') or site.startswith('https:')) and 
                    site.find('\\') > 0):
            site = site.replace('\\', '/')
        
        if self.nextRule == 'websitecommands':
            self.wantedWebsite = site
        else:
            self.openWebsiteDefault(site)
            self.wantedWebsite = None
            
    def gotResults_thiswebsite(self,words,fullResults):
        """get current website and open with websitecommands rule
        
        """
        natqh.saveClipboard()
        action('SSK {alt+d}{extend}{shift+exthome}{ctrl+c}')
        action("VW")
        self.wantedWebsite = natqh.getClipboard()
        self.wantedWebsite = self.wantedWebsite.rstrip("/")
        self.catchRemember = "website"
        print 'this website: %s'% self.wantedWebsite
        natqh.restoreClipboard()
        if self.hasCommon(words, "remember"):
            if self.nextRule == "dgndictation":
                self.catchRemember = "website"
            else:
                self.checkForChanges = True
                spokenWebsite = self.getWebsiteBasenameRemember(self.wantedWebsite)
                if not spokenWebsite:
                    print "_folders, could not extract a nice spoken website from %s\nTry "% self.wantedWebsite
                    print 'Try "this website remember as <dgndictation>"'
                    return
                self.ini.set("websites", spokenWebsite, self.wantedWebsite)
                print 'with "website %s" you can now open %s'% (spokenWebsite, self.wantedWebsite)
                self.ini.write()

    def getWebsiteBasenameRemember(self, url):
        """extract the website main from the url
        """
        last = url.split("://")[-1]
        first = last.split('/')[0]
        partslist = first.split(".")
        nice = partslist[-2]
        # print "cleanWebsiteToSpoken, return : %s"% nice
        return nice
    
    def getFileBasenameRemember(self, filePath):
        """extract the website main from a file path
        """
        if isinstance(filePath, path):
            namePart = filePath.split()[-1]
        else:
            namePart = os.path.split(filePath)[-1]
        namePart = os.path.splitext(namePart)[0]
        spokenList = self.spokenforms.generateMixedListOfSpokenForms(namePart)
       
        if not spokenList:
            return namePart
        if len(spokenList) > 1:
            print 'getFileBasenameRemember, more spoken alternatives found: %s, return first item'% spokenList
        return spokenList[0]
        
    def getDuplicateFolders(self, wantedFolder):
        """get (spoken, folder) list for this wanted folder
        """
        wantedFolder = self.cleanpath(wantedFolder)
        duplicateNames = []
        # print 'wantedfolderclean: %s'% wantedFolder
        for spokenname, folderpath in self.foldersDict.iteritems():
            folderpath = self.cleanpath(self.substituteFolder(folderpath))
            if folderpath == wantedFolder:
                # print 'name: %s, folderpath: %s'% (utilsqh.convertToBinary(spokenname), utilsqh.convertToBinary(folderpath))
                duplicateNames.append(spokenname)
        return duplicateNames
    
    def cleanpath(self, somepath):
        """normalise path, and lowercase
        """
        return os.path.normpath(os.path.abspath(somepath)).lower().replace("\\", "/")
    
    def getFolderBasenameRemember(self, folderPath):
        """extract the spoken name from the folder path
        """
        print 'getFolderBasenameRemember, folderPath: %s'% folderPath
        if isinstance(folderPath, path):
            namePart = folderPath.split()[-1]
        else:
            namePart = os.path.split(folderPath)[-1]
        spokenList = self.spokenforms.generateMixedListOfSpokenForms(namePart)
        print 'namePart: %s, spokenList: %s'% (namePart, spokenList)
        if not spokenList:
            return namePart
        if len(spokenList) > 1:
            print 'getFolderBasenameRemember, more spoken alternatives found: %s, return first item'% spokenList
        return spokenList[0]
    
            
    def gotResults_websitecommands(self,words,fullResults):
        """start webbrowser, specified
        
        expect self.wantedWebsite to be filled.
        
        open with list in inifile, expected right hand sides to be browsers
        """
        if not self.wantedWebsite:
            print 'websitecommands, no valid self.wantedWebsite: %s'% self.wantedWebsite
        openWith, owIndex = self.hasCommon(words, ['open with'], withIndex=1)
        if openWith:
            openWith = self.getFromInifile(words[owIndex+1], 'websiteopenprograms', noWarning=1)
        self.openWebsiteDefault(self.wantedWebsite, openWith=openWith)

#     def gotResults_folder(self, words, fullResults):
#         """collects the given command words and try to find the given folder
# 
#         made distinction between folders and subfolders (17/2/2017)
#         """
# ##        print '-------folder words: %s'% words
#         # if self.activeFolder and words[1] in self.subfoldersDict:
#         #     subfolder = self.subfoldersDict[words[1]]
#         #     folder = os.path.join(self.activeFolder, subfolder)
#         #     print 'subfolder: %s'% folder
#         # else:
#         # subfolder = None
#         if len(words) == 1:
#             self.gotFolder = True
#             return
#         folder1 = self.foldersDict[words[1]]
#         folder = self.substituteFolder(folder1)
#             
#         # if no next rule, simply go:
#         if not self.nextRule:
#             # do action straight away:
#             self.gotoFolder(folder)
#             self.wantedFolder = None
#         else:
#             self.wantedFolder = folder

    def gotResults_subfolder(self, words, fullResults):
        """collects the given command words and try to find the given subfolder

        see above!! But do no actions if there is a rule after (remember, foldercommands)
        
        fill self.wantedFolder
        """
##        print '-------folder words: %s'% words
        folderWord = utilsqh.convertToUnicode(words[1])
        if self.activeFolder and folderWord in self.subfoldersDict:
            subfolder = self.subfoldersDict[folderWord]
            folder = os.path.join(self.activeFolder, subfolder)
            print 'subfolder: %s'% folder
        else:
            print 'cannot find subfolder: %s'% folderWord
            print 'subfoldersDict: %s'% self.subfoldersDict
            return
            # subfolder = None
            # folder1 = self.foldersDict[words[1]]
            # folder = self.substituteFolder(folder1)
            
        # if no next rule, simply go:
        self.wantedFolder = folder
        if not self.nextRule:
            # do action straight away:
            # self.gotoFolder(folder)folder Natlink Subversion export
            self.gotoInThisComputer(folder)
            self.wantedFolder = None
        elif self.nextRule in ["remember", "foldercommands"]:
            self.catchRemember = "folder"

    def gotResults_recentfolder(self,words,fullResults):
        """give list of recent folders and choose option
        """
        if not self.recentFoldersList:
            if self.trackFoldersHistory:
                if self.language == 'nld':
                    Message('Er zijn geen recente mappen (folders) in de lijst', title="Unimacro grammatica folders")
                else:
                    Message('No recent folders in list', title="Unimacro grammar folders")
            else:
                Message('The option "track folders history" is not switched on, see https://qh.antenna.nl/unimacro/')
            return

        numberOfItems = len(self.recentFoldersList)
        if self.language == 'nld':
            self.dialogWindowTitle = 'Recent geopende mappen (folders)'
        else:
            self.dialogWindowTitle = 'Recent visited folders'
        self.dialogNumberRange = range(1,numberOfItems+1)

        L = []
        for i, item in enumerate(self.recentFoldersList):
            L.append( '%s: %s'% (i+1, item))
            
        L.append("")
        if self.language == 'nld':
            L.append('Open de gewenste map (folder) met "kies #" of sluit het venster ("OK" of "Annuleren")')
        else:
            L.append('Open the folder you want with "choose #" or quit this window ("OK" or "Cancel")')
        Message(L, title=self.dialogWindowTitle)
        # "" is translated into "

    def gotResults_site(self,words,fullResults):
        """switch to one of the sites in the list
        mainly for private use, a lot of folders reside in the root folder,
        siteRoot.  They all have an input folder and a output folder.

        """
        print 'site: %s'% words
        siteSpoken = words[1]
        self.lastSite = None # name of site
        if siteSpoken in self.sitesDict:
            siteName = self.sitesDict[siteSpoken]
            self.lastSite = siteName
        else:
            raise ValueError("no siteName for %s"% siteSpoken)
        
        self.site = self.getSiteInstance(siteName) 
            
        if siteName in self.sitesInstances:
            self.site = self.sitesInstances[siteName]
        else:
            site = self.getSiteInstance(siteName)
            if site:
                self.sitesInstances[siteName] = site
                self.lastSite = siteName
                self.site = site
            else:
                self.site = None
                print 'could not get site: %s'% siteName
        #
        #if site is None:
        #    print 'invalid site: %s, marking in ini file'% site
        #    self.ini.set('sites', siteName, '')
        #    self.ini.write()
        #    return
        if not self.nextRule:
            if self.site:
                rootDir = self.site.rootDir
                self.gotoFolder(rootDir)
            return
        elif self.nextRule == "sitecommands":
            print 'site, waiting for sitecommands'
        else:
            self.wantedFolder = self.site.rootDir
    
    def gotResults_sitecommands(self, words, fullResults):
        """do the various options for sites (QH special).
        Assume lastSite is set
        """
        if not self.site:
            print "sitecommands, no last or current site set"
            return
        print 'sitecommands for "%s": %s (site: %s)'% (self.lastSite, words, self.site)
        site = self.site
        website, folder = None, None
        for command in words:
            command = self.getFromInifile(words[0], 'sitecommands')
    
            if command == 'input':
                print 'input: %s'% words
                folder = unicode(site.sAbs)
            elif command == 'output':
                folder = unicode(site.hAbs)
            elif command == 'local':
                website = os.path.join(unicode(site.hAbs), 'index.html')
            elif command == 'online':
                sitePrefix = site.sitePrefix
                if type(sitePrefix) == types.DictType:
                    for k, v in sitePrefix.iteritems():
                        sitePrefix = v
                        break
                    
                website = os.path.join(unicode(sitePrefix), 'index.html')
            elif command == 'testsite':
                if 'sg' in self.sitesInstances:
                    testsite = self.sitesInstances['sg']
                else:
                    testsite = self.getSiteInstance('sg')
                    if testsite:
                        self.sitesInstances['sg'] = testsite

                if testsite:
                    # site at sitegen site:
                    website = os.path.join(unicode(testsite.sitePrefix['nl']), self.lastSite, 'index.html')

        if self.nextRule:
            if folder:
                self.wantedFolder = folder
                return
            elif website:
                self.wantedWebsite = website
                return
            else:
                print 'no valid folder or website for nextRule'
                return
        elif folder:
            self.gotoFolder(folder)
            self.wantedFolder = None
        elif website:
            self.openWebsiteDefault(website)
            self.wantedWebsite = None

    def getSiteInstance(self, siteName):
        """return pageopen function of site instance, or None
        """
        try:
            site = __import__(siteName)
        except ImportError, msg:
            import traceback
            print 'cannot import module %s'% siteName
            print traceback.print_exc()
            currentDir = '.' in sys.path
            print 'currentDir in sys.path: %s'% currentDir
            print 'sys.path: %s'% sys.path 
            return
        if 'pagesopen' in dir(site):
            try:
                po = site.pagesopen()
                return po
            except:
                print '"pagesopen" failed for site %s'% siteName
                return
        else:
            print 'no function "pagesopen" in module: %s'% siteName
            return
        
    def findFolderWithIndex(self, root, allowed, ignore=None):
        """get the first folder with a file index.html"""

        for i in allowed:
            tryF = os.path.join(root, i)
            if os.path.isdir(tryF) and (
                os.path.isfile(os.path.join(tryF, 'index.html')) or \
                os.path.isfile(os.path.join(tryF, 'index.txt'))):
                return tryF
        if ignore and type(ignore) == types.ListType:
            # look in listdir and take first that is not to be ignored:
            try:
                List = os.listdir(root)
            except:
                return
            for d in List:
                if d in ignore:
                    continue
                tryF = os.path.join(root, d)
                if os.path.isdir(tryF) and os.path.isfile(os.path.join(tryF, 'index.html')):
                    return tryF

    def gotResults_folder(self, words, fullResults):
        """collects the given command words and try to find the given folder

        """
        print '-------folder words: %s'% words
        if len(words) == 1:
            ## catch folder with dgndictation, postpone here:
            self.gotFolder = True
            return

        folder1 = self.foldersDict[words[1]]
        folder = self.substituteFolder(folder1)
        # this one has no remember option:
        if self.nextRule == "foldercommands":  
            self.wantedFolder = folder
        else:
            self.gotoFolder(folder)
            self.wantedFolder = None

    def gotResults_foldercommands(self, words, fullResults):
        """open the folder and do additional actions
        
        the optionalfoldercommands (like new or paste) must appear in the
        right hand side of the inifile section (ie the value) (so spoken may be
        different)
        """
        if not self.wantedFolder:
            print 'rule foldercommands, no wantedFolder, return'
            return
        kw = {}
        for w in words:
            opt = self.getFromInifile(w, 'foldercommands')
            if opt:
                if opt in self.optionalfoldercommands:
                    kw[opt] = opt
                else:
                    kw[w] = opt
        Remote, remoteIndex = self.hasCommon(words, ['on'], withIndex=1)
        print 'remote: %s, remoteIndex: %s, words: %s'% (Remote, remoteIndex, words)
        if Remote:
            remoteLetter =  self.getFromInifile(words[remoteIndex+1], 'letters', noWarning=1)
            remoteVirtualDrive = self.getFromInifile(words[remoteIndex+1], 'virtualdrivesspoken', noWarning=1)
            if remoteLetter:
                print 'remoteLetter: %s'% remoteLetter
                kw['remote'] = remoteLetter.upper() + ":"
            elif remoteVirtualDrive:
                remote = self.virtualDriveDict[remoteVirtualDrive]
                print 'remoteVirtualDrive: %s, resolves to: %s'% (remoteVirtualDrive, remote)
                kw['remote'] = remote
            else:
                print '_folders: no valid drive or virtualdrive for remote options, words: %s'% repr(words)
                return 
        print('foldercommands: %s'% words)
        Subversion, svnIndex = self.hasCommon(words, ['subversion'], withIndex=1)
        if Subversion:
            svnCommand = self.getFromInifile(words[svnIndex+1], 'subversionfoldercommands')
            kw['subversion'] = svnCommand
        Git, gitIndex = self.hasCommon(words, ['git'], withIndex=1)
        if Git:
            gitCommand = self.getFromInifile(words[gitIndex+1], 'gitfoldercommands')
            kw['git'] = gitCommand
        
        self.gotoFolder(self.wantedFolder, **kw)

    def gotResults_namepathcopy(self, words, fullResults):
        """copy the name or the path of a folder, file or website
        """
        if not self.catchRemember:
            print "_folders, namepathcopy, do not know what to copy, folder, file or website"
            return
        if self.hasCommon(words, "name"):
            what = "name"
        elif self.hasCommon(words, "path"):
            what = "path"
        else:
            print "_folders, namepathcopy, choose copy name or path, not: %s"% repr(words)
            return
        if self.catchRemember == "folder":
            if not self.wantedFolder:
                print "_folders, namepathcopy, no valid folder"
                return
            self.wantedFolder = self.wantedFolder.rstrip("/\\")
            if what == "name":
                result = os.path.split(self.wantedFolder)[-1]
            else:
                result = self.wantedFolder
        elif self.catchRemember == "file":
            if not self.wantedFile:
                print "_folders, namepathcopy, no valid file"
                return
            if what == "name":
                result = os.path.split(self.wantedFile)[-1]
            else:
                result = self.wantedFile

        elif self.catchRemember == "website":
            if not self.wantedWebsite:
                print "_folders, namepathcopy, no valid website"
                return
            if what == 'name':
                result = self.wantedWebsite.split("/")[-1]
            else:
                result = self.wantedWebsite.split()[-1]
        print 'namepathcopy, result: %s (type: %s)'% (result, type(result))
        natqh.setClipboard(result, 13)   # 13 unicode!!

    def gotResults_remember(self, words, fullResults):
        """treat the remember function, filling items in ini files
        """
        if not self.catchRemember:
            print '_folders, in remember rule, but nothing to remember'
            return
        # 
        # 
        # waitForDictation = (self.nextRule == "dgndictation")
        # print "waitForDictation: %s"% waitForDictation
        # print 'words remember: %s'% words
        # lastWord = words[-1]
        # if waitForDictation:
        #     print 'last word: %s'% words[-1]
        #     extraWords = ["as", "append", "insert"]
        #     for extra in extraWords:
        #         if self.hasCommon(lastWord, extra):
        #             self.rememberExtra = extra
        #             break
        #     else:
        #         self.rememberExtra = None
        #     if not self.rememberExtra:
        #         print "_folders, no valid word before dgndictation: %s\nShould be (synonym of translation) of one of: %s)"% (words[-1],
        #                                                                     extraWords)
        #     print 'rememberExtra: %s'% self.rememberExtra
        # 
        if self.catchRemember == "folder":
            self.rememberBase = self.getFolderBasenameRemember(self.wantedFolder)
            duplicateFolders = self.getDuplicateFolders(self.wantedFolder)
            self.wantedFolder = self.wantedFolder.replace("\\", "/")
            value = self.wantedFolder
            texts = ['Remember folder "%s" for future calling?'% self.wantedFolder]
            if duplicateFolders:
                texts.append("Folder already known as: %s"% "\n\t".join(duplicateFolders))

            texts.append("Please give a spoken form for this folder and choose OK; or Cancel...")
            default = self.rememberBase
            section = 'folders'
        elif self.catchRemember == "website":
            self.rememberBase = self.getWebsiteBasenameRemember(self.wantedWebsite)
            texts = ['Remember website for future calling?']
            texts.append('- %s -'% self.wantedWebsite)
            texts.append("Please give a spoken form for this website and choose OK; or Cancel...")
            section = 'websites'
            value = self.wantedWebsite
            default = self.rememberBase
        elif self.catchRemember == "file":
            self.rememberBase = self.getFileBasenameRemember(self.wantedFile)
            self.wantedFile = self.wantedFile.replace("\\", "/")
            value = self.wantedFile
            texts = ['Remember file "%s" for future calling?'% self.wantedFile]
            texts.append("Please give a spoken form for this file and choose OK; or Cancel...")
            default = self.rememberBase
            section = 'files'
        else:
            print '_folders, invalid value for catchRemember: %s'% self.catchRemember
            return
        prompt = "Remember in Unimacro _folders grammar"
        inifile = self.ini._file
        inifile = inifile.replace("\\", "/")
        text = '\n\n'.join(texts)
        title = "bla bla bla" # not used
        if not self.checkForChanges:
            self.checkForChanges = 10  # switch this on 10 utterances
        pausetime = 3
        makeFromTemplateAndExecute("C:/Natlink/Unimacro", "unimacrofoldersremembertemplate.py", "rememberexe.py",
                                      prompt, text, default, inifile, section, value, pausetime=pausetime)


    def get_active_explorer(self, hndle=None):
        """give only handle when debugging with unittestFolder
        """
        if hndle is None:
            hndle = win32gui.GetForegroundWindow()
        shell = Dispatch("Shell.Application")

        for window in shell.Windows():
            if int(window.HWND) == int(hndle):
                return window
        print "_folders: no active explorer."
        return None        
    
    def get_current_directory(self, hndle=None):
        window = self.get_active_explorer(hndle)
        if window is None:
            return
        path = urllib.unquote(window.LocationURL)
        
        for prefix in ["file:///", "http://", "https://"]:
            if path.startswith(prefix):
                lenprefix = len(prefix)
                path = path[lenprefix:]
        return path

    def get_selected_paths(self):
        window = self.get_active_explorer()
        if window is None:
            print 'get_selected_paths, cannot find application'
            return
        items = window.Document.SelectedItems()
        paths = []
        for item in collection_iter(items):
            paths.append(item.Path)
        return paths

    def get_selected_filenames(self):
        paths = self.get_selected_paths()
        if paths is None:
            return
        return [os.path.basename(p) for p in paths]

    def gotResults_thisfile(self, words, fullResults):
        """point to current file, can be selected, or pointed at with the mouse
        
        So "here" or "this" will work.
        
        Expect an action, remember or filecommands, so only catchRemember and wantedFile is returned.
        """
        if self.hasCommon(words[0], "here"):
            ## wait for the mouse to have stoppede moving
            button, nClick = 'left', 1
            if not self.doWaitForMouseToStop():
                print '_folders, thisfile, mouse did not stop, cannot click'
                return
            natqh.buttonClick(button, nClick)
            natqh.visibleWait()

        # print 'filenames: %s'% self.get_selected_filenames()
        self.wantedFile = None
        # paths = self.get_selected_paths()
        # if paths:
        #     for p in paths:
        #         if os.path.isfile(p):
        #             self.wantedFile = p
        #             break
        #     else:
        #         print "warning, thisfile: no valid file found"
        #             
        # else:
        natqh.saveClipboard()
        natqh.Wait()
        keystroke("{ctrl+c}")
        natqh.Wait()
        paths1 = natlinkclipboard.Clipboard.get_system_folderinfo()
        natqh.restoreClipboard() 

        if paths1:
            paths1 = [p for p in paths1 if os.path.isfile(p)]

        paths2 = get_selected_files(folders=False)
        print 'get_system_folderinfo: %s'% paths1
        print 'get_selected_files: %s'% paths2
        if paths1 and paths2:
            if paths1 == paths2:
                paths = paths1
            else:
                print '_thisfile, different info for both methods:\nVia Clipboard %s\nVia this module functions: %s'% \
                           (repr(paths1), repr(paths2))
                paths = paths2
        elif paths1:
            print '_thisfile, only paths1 (via clipboard) has data: %s'% repr(paths1)
            paths = paths1
        elif paths2:
            paths = paths2
            print '_thisfile, only paths2 (this module functions) has data: %s'% repr(paths2)
        else:
            print 'no paths info found with either methods'
            paths = None

        if not paths:
            print "no selected file found"
            return
        self.wantedFile = paths[0]
        if len(paths) > 1:
            print "warning, more files selected, take the first one: %s"% self.wantedFile
        print 'wantedFile: %s'% self.wantedFile
        self.catchRemember = "file"

    def gotResults_disc(self,words,fullResults):
##        print '-------drive words: %s'% words
        letter = self.getFromInifile(words, 'letters')
        if letter:
            f = letter + ":\\"
        else:
            print '_folders, ruls disc, no letter provided: %s'% words
            return
        
        if self.nextRule in ['foldercommands']:
            self.wantedFolder = f
        else:
            self.gotoFolder(f)
            self.wantedFolder = None

    def gotResults_file(self,words,fullResults):
        """collects the given command words and try to find the given file

        """
        File = None
        wantedFile = utilsqh.convertToUnicode(words[1])        
        if self.activeFolder and wantedFile in self.subfilesDict:
            File = self.subfilesDict[wantedFile]
            extension =self.getFromInifile(words, 'extensions', noWarning=1)
            if extension:
                File, old_extension =os.path.splitext (File)
                File = File +'.' + extension
                print 'got file: %s'% File
            File = os.path.join(self.activeFolder, File)
            if not os.path.isfile(File):
                print 'folders, file, from subfilesList, not a valid path: %s (return None)'% File
                File = None
            else:
                print 'file from subfileslist: %s'% File
            self.catchRemember = "file"
        if not File:
            try:
                File = self.filesDict[wantedFile]
            except KeyError:
                print 'file cannot be found in filesDict: %s (and not in subfilesDict either)'% wantedFile
                return
            File = self.substituteFolder(File)
            print "_folders, get file: actual filename (fixed fileslist): %s"% File
            extension =self.getFromInifile(words, 'extensions', noWarning=1)
            if extension:
                File, old_extension =os.path.splitext (File)
                File = File +'.' + extension
            if not os.path.isfile(File):
                print 'invalid file: %s'% File
                return
        if self.nextRule in ["filecommands", "remember"]:
            self.wantedFile = File
        else:
            self.gotoFile(File)
            self.wantedFile = None

    def gotResults_filecommands(self, words, fullResults):
        
        if not self.wantedFile:
            print 'rule filecommands, no wantedFile, return'
            return
        # print 'filecommands: %s'% words
        kw = {}
        for w in words:
            opt = self.getFromInifile(w, 'filecommands')
            if opt:
                if opt in self.optionalfilecommands:
                    kw[opt] = opt
                # elif opt.startswith('subversion '):
                #     opt = opt[11:]
                #     kw['subversion'] = opt
                    
                else:
                    kw[w] = opt
        
        # remote on virtualdrivesspoken or letter, like foldercommands:
        Remote, remoteIndex = self.hasCommon(words, ['on'], withIndex=1)
        if Remote:
            # print 'file remote: %s, remoteIndex: %s, words: %s'% (Remote, remoteIndex, words)
            remoteLetter =  self.getFromInifile(words[remoteIndex+1], 'letters', noWarning=1)
            remoteVirtualDrive = self.getFromInifile(words[remoteIndex+1], 'virtualdrivesspoken', noWarning=1)
            if remoteLetter:
                print 'get file on remoteLetter: %s'% remoteLetter
                kw['remote'] = remoteLetter.upper() + ":"
            elif remoteVirtualDrive:
                remote = self.virtualDriveDict[remoteVirtualDrive]
                print 'get file on remoteVirtualDrive: %s, resolves to: %s'% (remoteVirtualDrive, remote)
                kw['remote'] = remote
            else:
                print '_folders: no valid drive or virtualdrive for remote options, of getting file. Words: %s'% repr(words)
                return
        
        OpenWith, owIndex = self.hasCommon(words, ['open with'], withIndex=1)
        if OpenWith:
            OpenWith = self.getFromInifile(words[owIndex+1], 'fileopenprograms')
            print 'openwith: %s'% OpenWith
            kw["openwith"] = OpenWith
        
        Subversion, svnIndex = self.hasCommon(words, ['subversion'], withIndex=1)
        if Subversion:
            svnCommand = self.getFromInifile(words[svnIndex+1], 'subversionfilecommands')
            print 'subversion file command: %s'% svnCommand
            kw['subversion'] = svnCommand
        self.gotoFile(self.wantedFile, **kw)
        
    # methods gotResults_info and gotResults_onoroff are
    # provided in IniGrammar
    
    def gotResults_thisfolder(self,words,fullResults):
        """do additional commands for current folder
    
        can be reached with "this" or "here" (buttonclick)
        assume foldercommands or remember action follows, so only rememberBase and wantedFolder are given
        
        """
        cb = natlinkclipboard.Clipboard(save_clear=True)
        
        if self.hasCommon(words[0], "here"):
            ## wait for the mouse to have stoppede moving
            button, nClick = 'left', 1
            if not self.doWaitForMouseToStop():
                print "_folders, command thisfolder: doWaitForMouseToStop fails"
                return
            natqh.buttonClick(button, nClick)
            natqh.visibleWait()

        # now got attention, go ahead:
        self.wantedFolder = None        
        natqh.saveClipboard()
        natqh.Wait()
        keystroke("{ctrl+c}")
        natqh.Wait()
        paths1 = natlinkclipboard.Clipboard.Get_folderinfo()
        if paths1:
            paths1 = [p for p in paths1 if os.path.isdir(p)]
        paths2 = get_selected_files(folders=True)
        natqh.Wait()
        if paths1 and paths2:
            if paths1 == paths2:
                paths = paths1
            else:
                print '_thisfolder, different info for both methods:\nVia Clipboard %s\nVia this module functions: %s'% \
                           (repr(paths1), repr(paths2))
                paths = paths2
        elif paths1:
            print '_thisfolder, only paths1 (via clipboard) has data: %s'% repr(paths1)
            paths = paths1
        elif paths2: #
            paths = paths2
            print '_thisfolder, only paths2 (this module functions) has data: %s'% repr(paths2)
        else:
            print 'no paths info found with either methods'
            paths = None
            
        print 'paths:::: %s'% paths #
        if paths:
            self.wantedFolder = paths[0]
            if len(paths) > 1:
                print "warning, more items selected, take the first one: %s"% self.wantedFolder
        elif self.activeFolder:
            print 'take activeFolder: %s'% self.activeFolder
            self.wantedFolder = self.activeFolder
        else:
            print '"this folder" no selected folder found'
            return
        if os.path.isdir(self.wantedFolder):
            # print '_folders, this folder, wantedFolder: %s'% self.wantedFolder
            self.catchRemember = "folder" # in case remember follows
        else:
            print '_folders, wantedFolder not a valid folder: %s'% self.wantedFolder
           
    # def gotResults_dgndictation(self, words, fullResults):
    # this rule proved to hit too often with website command. Better avoid this rule!
    #     """catch dictate for remember folder, file or website
    #     """
    #     if self.waitForDictation == 'website':
    #         text, dummy = nsformat.formatWords(words, state=-1)  # no capping, no spacing
    #         print 'google for %s'% text
    #         textplus = "+".join(text.split())
    #         searchurl = "https://www.google.com/search?q=%s"% textplus
    #         self.openWebsiteDefault(searchurl)
    #         return
    #         
    def gotResults_folderup(self,words,fullResults):
        """ go up in hierarchy"""
        upn = self.getNumberFromSpoken(words[-1])
        #print 'folderup: %s'% upn
        m = natlink.getCurrentModule()
        prog, title, topchild, windowHandle = natqh.getProgInfo(modInfo=m)
        hndle = m[2]
        Iam2x = prog == '2xexplorer'
        IamExplorer = prog == 'explorer'
        IamChild32770 = topchild, windowHandle == 'child' and win32gui.GetClassName(hndle) == '#32770'
        if IamChild32770:
            self.className = '#32770'
        browser = prog in ['iexplore', 'firefox','opera', 'netscp']
        # print 'iambrowser: %s Iamexplorer: %s'% (browser, IamExplorer)
        istop = self.getTopOrChild( m, childClass="#32770" )  # True if top window
        if IamChild32770:
            if not self.activeFolder:
                self.activeFolder = mess.getFolderFromDialog(hndle, self.className)
            if self.activeFolder:
                newfolder = self.goUpInPath(self.activeFolder, upn)
                #print 'newfolder (up %s): %s'% (upn, newfolder)
                self.gotoInThisDialog(newfolder, hndle, self.className)
            else:
                print 'method not working (any more) for #32770: %s'% title
            
        elif not istop:   # child window actions
            
            action("RMP 1, 0.02, 0.05, 0")
            action("<<filenameenter>>; {shift+tab}")
            action("{backspace %s}"% upn)
        elif browser:
            natqh.saveClipboard()
            keystroke('{alt+d}{extend}{shift+exthome}{ctrl+c}')
            t = natqh.getClipboard()
            prefix, path = t.split('://')
            T = path.split('/')
            if len(T) > upn:
                T = T[:-upn]
            else:
                T = T[0]
            
            keystroke(prefix + '://' + '/'.join(T))
            keystroke('{enter}')
            natqh.restoreClipboard()
        elif IamExplorer:
            if not self.activeFolder:
                self.activeFolder = mess.getFolderFromCabinetWClass(hndle)
            if self.activeFolder:
                newfolder = self.goUpInPath(self.activeFolder, upn)
                print 'newfolder (up %s): %s'% (upn, newfolder)
                self.gotoInThisComputer(newfolder)
            else:
                print 'method not working any more, going folder up'
                action("MP 1, 50, 10, 0")
                for i in range(upn):
                    action("{backspace} VW")
            
        else:            
            print 'yet to implement, folder up for  %s'% prog
            
        #print 'had folder up: %s'% words
        
    
    def substituteFolder(self, folder):
        """substitute virtual drive into for  into folder name

        If a virtual drive is not in folder name, simply
        the name is returned, otherwise the contents of
        this virtual drive are inserted.
        Also the EnvVariables are resolved.
          
        """
        folder = folder.replace('/', '\\')
        folder = self.substituteEnvVariable(folder)
        if not self.virtualDriveDict:
            #print 'no virtualDriveDict, return %s'% folder
            return folder
        if folder in self.virtualDriveDict:
            drive, rest = folder, ""
        elif folder.find(':\\') > 0:
            drive, rest = folder.split(":\\", 1)
        elif folder.find(":") == -1 and folder.find('\\') == 2:
            drive, rest = folder.split("\\", 1)
        elif folder.find(':') > 0:
            drive, rest = folder.split(":", 1)
        else:
            drive, rest = folder, ''

        if drive in self.virtualDriveDict:
            vd = self.virtualDriveDict[drive]
            vd = self.substituteFolder(vd)
            if rest:
                return os.path.join(vd, rest)
            else:
                return vd
        else:
            return folder

    def substituteEnvVariable(self,folder):
        """honor environment variables like %HOME%, %PROGRAMFILES%

        %HOME% is also recognised by ~ (at front of name)
        
        With expandEnvVars, also NATLINK and related variables can be handled.
        NATLINKDIRECTORY, COREDIRECTORY etc.
        """
        substitute = natlinkcorefunctions.expandEnvVariables(folder)
        return substitute

    def substituteFilename(self, filename):
        """substitute virtual drive into for  into filename,and possibly the spoken form

        If a virtual drive is not in folder name, simply
        the name is returned, otherwise the contents of
        this virtual drive are inserted.
          
        """
        filename = filename.replace('/', '\\')
        filename = self.substituteEnvVariable(filename)
        if filename.find(':\\') > 0:
            drive, rest = filename.split(":\\", 1)
            if drive in self.virtualDriveDict:
                drive1 = self.substituteFolder(drive)
##                print 'drive for: |%s|: |%s|'% (drive, drive1)
                return os.path.join(drive1, rest)
        elif filename.find(':') == -1 and filename.find('\\') == 2:
            drive, rest = filename.split("\\", 1)
            drive1 = self.substituteFolder(drive)
            return os.path.join(drive1, rest)
        elif filename.find('\\') > 0:
            start, rest = filename.split("\\", 1)
            F = self.getFromInifile(start, 'folders')
            if F:
                start = self.substituteFolder(F)
                return os.path.join(start, rest)
        return filename  

    def checkSubversionFolder(self, f):
        """return True if f is a valid subversion folder
        """
        svnsubdir = os.path.join(f, '.svn')
        if os.path.exists(svnsubdir) and os.path.isdir(svnsubdir):
            return True
        

    def getSpokenFormsDict(self, List, extensions=None):
        """make speakable forms, leave out extensions if extensions = 1
        
        files: set extensions to 1, and 
            take only extensions from the list self.acceptFileExtensions
            (to be set in ini file
        
        make all keys lowercase
        
        """
        D = {}
        for item in List:
            if extensions:
                spoken, ext = os.path.splitext(item)
                if not self.acceptExtension(ext):
                    continue
                if not self.acceptFileName(spoken):
                    continue
            else:
                if not self.acceptFileName(item):
                    continue
                spoken = item
            spokenList = self.spokenforms.generateMixedListOfSpokenForms(spoken)
            if not spokenList:
                print '_folders, getSpokenFormsDict: false spokenList, List: %s'% List
                return D
            #if spoken.startswith('.'):
            #    spoken = 'dot ' + spoken[1:]
            #    spoken = 'underscore ' + spoken[1:]
            for spoken in spokenList:
                D[spoken] = item
        #print '----D:\n%s\n----'% D
        return D      

    def getSpokenDetail(self, detail):
        """if numeric, get number else return same
        """
        try:
            n = int(detail)
        except ValueError:
            return detail
        if n in self.spokenforms.n2s:
            return self.spokenforms.n2s[n][0]
        return detail
    
    def acceptExtension(self, ext):
        """accept file extension according to settings
        
        acceptFileExtensions
        """
        if ext.lower() in self.acceptFileExtensions:
            return 1

    def acceptFileName(self, item, extensions=None):
        """return 1 if filename ok, only filename expected here
        """
        for pat in self.ignoreFilePatterns:
            if fnmatch.fnmatch(item, pat):
                return
        return 1
    
    def gotoFile(self, f, **kw):
        """goto the file f"""
        if self.citrixApps:
            prog = natqh.getProgInfo()[0]
            
            print 'citrixApps: %s app: %s'% (self.citrixApps, prog)
            if prog in self.citrixApps:
                print 'doing action gotoFolder for citrixApp: %s'% prog    
                action("<<openstartmenu>>")
                keystroke(f)
              
                # keystroke("{enter}")
                return


        if not os.path.isfile(f):
            self.DisplayMessage('file does not exist: %s'% f)
            return
        m = natlink.getCurrentModule()
        prog, title, topchild, windowHandle = natqh.getProgInfo(modInfo=m)
        mode = openWith = None
        
        # istop logic, with functions from action.py module, settings from:
        # child behaves like top = natspeak: dragon-balk
        # top behaves like child = komodo: find, komodo; thunderbird: bericht opslaan
        # in actions.ini:

        istop = self.getTopOrChild( m, childClass="#32770") # True if top

        for opt in self.optionalfilecommands:
            exec("%s = None"% opt.capitalize())
        additionalOptions = []
        for k, v in kw.items():
            if k in self.optionalfilecommands:
                print 'setting option %s to %s'% (k, v)
                exec("%s = '%s'"% (k.capitalize(), v))
            else:
                additionalOptions.append(v)
        # if additionalOptions:                
        #     print 'additional options: %s'% additionalOptions
        
        if Remote:
            print 'Remote: %s'% Remote
        if Remote:
            print 'Remote: %s'% Remote
            f = self.getValidFile(f, Remote)
            if not f:
                return
            
        if Subversion:
            print 'subversion command "%s" for file "%s"'% (Subversion, f)
            self.doSubversionCommand(Subversion, f)
            return
        if Git:
            print 'git command "%s" for file "%s"'% (Git, f)
            self.doGitCommand(Git, f)
            return
        
        if Edit:
            mode = 'edit'        
        else:
            mode = 'open'

        if Copy:
            natqh.setClipboard(f)
            return
        if Paste:
            action("SCLIP %s"%f)
            # keystroke(f)C>Documenten
            return
        if additionalOptions:
            print 'additional options: %s'% additionalOptions


        if not istop:   # child window actions
            # put the mouse in the left top corner of the window:
            print "Open file from child window: %s"% f
            action("RMP 1, 0.02, 0.05, 0")
            action('<<filenameenter>>')
            natqh.saveClipboard()
            keystroke('{Ctrl+x}')
            keystroke(f)
            action('<<filenameexit>>')
            keystroke('{Ctrl+v}')
            natqh.restoreClipboard()
            keystroke('{Shift+Tab}')
        else:
            # top or top behaviourthis
            kw = dict(mode=mode, openWith=Openwith)
            self.openFileDefault(f, mode=mode, openWith=Openwith, addOpts=additionalOptions)
        
    def openFileDefault(self, filename, mode=None, openWith=None, addOpts=None):
        """open the file in the default window and perform additional options"""
##        action('CW')
        if not os.path.isfile(filename):
            print 'file does not exist, cannot open: %s'% filename
            return
        if not ancestor.openFileDefault(self, filename, mode=mode, openWith=openWith):
            print 'could not open %s (mode: %s, openWith: %s)'% (filename, mode, openWith)
            return
        if addOpts:
            for opt in addOpts:
                action(opt)




    def openFolderDefault(self, foldername, *args):
        """open the folder in the default window
         LW() 
        if succeed, perform optional additional options.
        
        """
##        action('CW')
        #print 'going to open folder: %s'% foldername
            
        if not ancestor.openFolderDefault(self, foldername):
            print 'failed to open folder: %s'% foldername
            return
        for opt in args:
            action(opt)
            
    #  This is the function which does the real work, depending on the
    #    window you are in
    def gotoFolder(self, f, **kw):
        """go to the specified folder

        f = the (local) folder to go to
        options to be set in dict kw:
        --New = true if a new window is asked for
        --Explorer = true is an explorer window (possibly 2xExplorer) is wanted (obsolete)
        --Remote = the remote drive letter if the folder is wanted on another drive

        this is the central routine, with complicated strategy for getting it,
        in pseudocode:
        
        If QuickMode, we are in CabinetWClass and probably want a subfolder
        
        if New:
            if Explorer:
                start start new Explorer
                (xxExplorer or Windows Explorer)
            elif isTop and in xxExplorer:
                go to other pane
            else:
                get new folder
        else:
            if Explorer:
                search for Explorer or start new
                (mainly for cases: in child or if xxExplorer is switched on)
            elif isChild:
                get the folder
            else: # isTop!
                if in xxExplorer:
                    get the folder
                else:
                    look for all for the Windows with titles
                    if exact:
                        go to that folder window
                    elif overList: (titles are longer than folder asked for)
                        get folder in this window
                        (if you are already there, switch to the folder you want)
                    elif underList: (titles are shorter than folder you asked for)
                        take longest of the windows, if you are in goto exact
                    else:
                        if part of path is common, switch to that and goto folder

        ## only if subversion executable and/or git executable are defined in section [general]
        subversion, git
                        
        """
        if self.citrixApps:
            prog = natqh.getProgInfo()[0]
            
            print 'citrixApps: %s app: %s'% (self.citrixApps, prog)
            if prog in self.citrixApps:
                print 'doing action gotoFolder for citrixApp: %s'% prog    
                action("<<openstartmenu>>")
                keystroke(f)
                keystroke("{enter}")
                return
        f = os.path.normpath(f)
        if not os.path.isdir(f):
            self.DisplayMessage('folder does not exist: %s'% f)
            return
        if type(f) == six.binary_type:
            f = utilsqh.convertToUnicode(f)
        
        QuickMode = None
        for opt in self.optionalfoldercommands:
            exec("%s = None"% opt.capitalize())
        additionalOptions = []
        for k, v in kw.items():
            if k in self.optionalfoldercommands:
                # special options, not handled in foldercommands in inifile:
                exec("%s = '%s'"% (k.capitalize(), v))
            else:
                additionalOptions.append(v)
        addOpts = tuple(additionalOptions)
        
        if Subversion:
            self.doSubversionCommand(Subversion, f)

        if Git:
            self.doGitCommand(Git, f)
        
        xx = self.xxExplorer
        if Remote:
            print 'Remote: %s'% Remote
            f = self.getValidDirectory(f, Remote)
            if not f:
                return
        if Paste:
            action("SCLIP(%s)"%f)
            # keystroke(f)
            return
        if Copy:
            print 'put path on clipboard: "%s"'% f
            natqh.setClipboard(f)
            return
        
        m = natlink.getCurrentModule()
        istop = self.getTopOrChild( m, childClass="#32770" )
        prog, title, topchild, windowHandle = natqh.getProgInfo(modInfo=m)

        Iam2x = prog == '2xexplorer'
        IamExplorer = prog == 'explorer'
        browser = prog in ['iexplore', 'firefox','opera', 'netscp']
##        print 'iambrowser:', browser
##        print 'xx: %s, Iam2x: %s, IamExplorer: %s'% (xx, Iam2x, IamExplorer)
        if New:
            if Explorer:
                if xx:
                    self.doStart2xExplorer()
                    self.gotoIn2xExplorer(f)
                    return
                elif self.useOtherExplorer:
                    UnimacroBringUp(self.useOtherExplorer)
                    self.gotoInOtherExplorer(f)
                else:
                    self.openFolderDefault(f, *addOpts)
                    
##
####                    print 'starting windows explorer'
##                    self.doStartWindowsExplorer()
##                    self.gotoInThisComputer(f)
                    return
            elif istop and Iam2x:
                keystroke('{tab}')
                # and go on in the next section!
            else:
                self.openFolderDefault(f, *addOpts)
                return
        # now ready for a go:
        m = natlink.getCurrentModule()
        istop = self.getTopOrChild( m, childClass="#32770" )
        hndle = thisHandle = m[2]
        if not hndle:
            print '_folders, gotoFolder: no window handle found, return'
        # prog, title, topchild, windowHandle = natqh.getProgInfo(modInfo=m)
        Iam2x = prog == '2xexplorer'
        IamExplorer = prog == 'explorer'
        IamChild32770 = (not istop) and win32gui.GetClassName(hndle) == '#32770'
        if IamChild32770:
            self.className = '#32770'
        if IamChild32770:
            self.gotoInThisDialog(f, hndle, self.className)
            return
        elif QuickMode and self.className == 'CabinetWClass':
            self.gotoInThisComputer(f)
            return

        #print 'no dialog 32770 or QuickMode, finding good window for %s'% f
        if Explorer:
            if xx:
                self.doStart2xExplorer()
                self.gotoIn2xExplorer(f)
                return
            else:
                pass # simply look for a window outside child
        elif not istop:   # child window actions
            # put the mouse in the left top corner of the window:
            action("RMP 1, 0.02, 0.05, 0")
            action('<<filenameenter>>')
            natqh.saveClipboard()
            keystroke('{Ctrl+x}')
            keystroke(f)
            action('<<filenameexit>>')
            keystroke('{Ctrl+v}')
            natqh.restoreClipboard()
            keystroke('{Shift+Tab}')
            return

        # rest, in top, look for right window:
        if Iam2x:
            self.gotoIn2xExplorer(f)
            return

        # if user wants another explorer:
        if self.useOtherExplorer:
            UnimacroBringUp(self.useOtherExplorer)    
            self.gotoInOtherExplorer(f)
            return
            
        # search folder titles (with Class name: CabinetWClass)
        LIST = getExplorerTitles()
        if not LIST:
            self.openFolderDefault(f, *addOpts)

            return
        
        exactList = []
        overList = [] # windowtitle longer than wanted folder
        underList = [] # windowtitle shorter than wanted folder
        restList = []
##            print 'find appropriate window'
        # titles are unicode now, folder is still str.
        # print('f: (%s): %s'% (type(f), f))
        for t, h in LIST:
            # print('t: (%s): %s'% (type(t), t))
            # print('h: (%s): %s'% (type(h), h))
            if t == f:
                exactList.append((t, h))
            elif t.find(f) == 0:
                overList.append((t, h))
            elif f.find(t) == 0:
                underList.append((t, h))
            else:
                restList.append((t,h))
        #print 'searching for: ', f
        #print 'exactList: ', exactList
        #print 'overList: ', overList
        #print 'underList: ', underList
        #print 'restList: ', restList
        if exactList:
##                print 'exactList %s' % (exactList)
            if len(exactList) > 1:
                print 'warning, 2 matching windows: %s'% exactList
            t, h = exactList[0]
            natqh.SetForegroundWindow(h)
        elif overList:
##            print 'over List %s' % (overList)
            # eg f = d:\\a\\b
            # and elements of overList are d:\\a\\b\\c and d:\\a\\b\\c\\d
            # goto shortest element
            # later make choice list of where to go
            if len(overList) == 1:
                t, h = overList[0]
                natqh.SetForegroundWindow(h)
            lenMin = 999
            for t, h in overList:
##                    print 'nearList: %s'% nearList
                if len(t) < lenMin:
                    take = h
                    lenMin = len(t)
                
##                print 'i: %s, take: %s'% (i, nearList[i])
            toHandle = take

            if thisHandle == toHandle:
                self.gotoInThisComputer(f)
            else:
                natqh.SetForegroundWindow(take)
        elif underList:
            # eg f = d:\\a\\b\\c
            # elementes of underList are d:\\a d:\\a\\b etc.
            # go to longest element and switch in that window to folder
            print 'under list, go to first folder'
            lenMax = 0
            
            for t, h in underList:
##                    print 'nearList: %s'% nearList
                if len(t) > lenMax:
                    take = h
                    lenMax = len(t)
            if natqh.SetForegroundWindow(take):
                self.gotoInThisComputer(f)

        elif restList:
##            print 'rest list, go to first folder'
            # get longest "intersection" of restList and f
            # being the most convenient window for displaying the folder
            take = getLongestCommon(restList, f) # tuple (title, handle)
##            print 'take: ', `take`
            if take:
                t, h = take
                if natqh.SetForegroundWindow(h):
                    self.gotoInThisComputer(f)
                else:
                    print 'could not set foregroundwindow: %s'% h
                    self.openFolderDefault(f, *addOpts)
                    
            else:
                #print 'no matching window at all, start new'
                self.openFolderDefault(f, *addOpts)
        else:
            # no this computer windows (yet)
            print "grammar folders shouldn't be here!"  


    def getValidDirectory(self, f, remote):
        """substitute remote in front of f and try to find a valid directory
        
        (tried in pathmanipulate_folders_grammar.py, private Quintijn)
        f = r'C:\Documenten\Quintijn'
        remote = r'C:\DocumentenOud'
        returns: r'C:\DocumentenOud\Quintijn
        
        f = r'E:\DocumentenFakeFolder\Quintijn'
        remote = r'C:\Documenten'
        returns: r'C:\Documenten\Quintijn'
        
        Works also for drive letters only: 
        f = r'C:\Documenten\Quintijn'
        remote = r'E:'
        returns: r'E:\Documenten\Quintijn'
        (if E: is a valid backup drive)

        """
        fdrive, fdir = os.path.splitdrive(f)
        remdrive, rempart = os.path.splitdrive(remote)
        fparts = [part for part in fdir.split(os.sep) if part]
        while fparts:
            fpart = os.sep.join(fparts)
            tryF = os.path.join(remote + os.sep, fpart)
            if os.path.isdir(tryF):
                return tryF
            fparts.pop(0)
        print '_folders, no valid remote folder found for %s and remote: %s'% (f, remote)

    def getValidFile(self, f, remote):
        fdrive, fdir = os.path.splitdrive(f)
        remdrive, rempart = os.path.splitdrive(remote)
        fparts = [part for part in fdir.split(os.sep) if part]
        while fparts:
            fpart = os.sep.join(fparts)
            tryF = os.path.join(remote + os.sep, fpart)
            if os.path.isfile(tryF):
                return tryF
            fparts.pop(0)
        print '_folders, no valid remote file found for %s and remote: %s'% (f, remote)


    def getListOfSites(self, root):
        """return list of sitenames, to be found as python files in root
        
        """
        pyfiles = [f for f in os.listdir(root) if f.endswith('.py')]
        #print 'pyfiles for sites: %s'% pyfiles
        D = {}
        entries = self.ini.get('sites')
        for p in pyfiles:
            trunk = p[:-3]
            if not reOnlyLowerCase.match(trunk):
                continue   # only lowercase items can be a sites item, so __init__ and HTMLgen etc are skipped
            if trunk in entries:
                spokenList = self.ini.getList('sites', trunk)
                if not spokenList:
                    #print 'empty item in siteslist: %s'% trunk
                    continue
                else:
                    for spoken in spokenList:
                        spoken = self.spokenforms.correctLettersForDragonVersion(spoken)
                        D[spoken] = trunk
            else:
                # make new entry in sites section
                if len(trunk) <= 3:
                    spoken = '. '.join(list(trunk.upper()))+'.'
                else:
                    spoken = trunk
                spoken = self.spokenforms.correctLettersForDragonVersion(spoken)
                D[spoken] = trunk
                #print 'set in sites: %s -> %s'% (trunk, spoken)
                self.ini.set('sites', trunk, spoken)
        return D
    
    def gotResults(self, words,fullResults):
        """at end of utterance, check recentFoldersList
        """
        if self.trackFoldersHistory:
            #print 'got results, start timer callback'
            natlink.setTimerCallback(self.manageRecentFoldersList, 1000)
        

    def doSubversionCommand(self, command, path):
        """launch subversion with command and path
        """
        args = '/command:%s /path:""%s""'% (command, path)
        
        # Construct arguments and spawn TortoiseSVN.
        name = "subversion %s %s"% (command, path)
        print 'subversion %s'% name
        natqh.AppBringUp(name, self.doSubversion, args)
        
    def doGitCommand(self, command, path):
        """launch git with command and path
        """
        args = '/command:%s /path:""%s""'% (command, path)
        
        # Construct arguments and spawn TortoiseSVN.
        name = "git %s %s"% (command, path)
        print('future git %s, %s'% (name, args))
        ## does not work (yet)...
        # natqh.AppBringUp(name, self.doGit, args)
        
        
#     def checkChildBehavesLikeTop(self, prog, title):
#         """check if prog and title match with self.childBehavesLikeTop
#         
#         obsolete, in favour of ChilWindowBehavesLikeTop of actions.py (december 2017)
#         """
#         title = title.lower()
# ##        print 'self.childBehavesLikeTop: %s'% self.childBehavesLikeTop
#         if prog in self.childBehavesLikeTop:
#             wantedTitles = self.childBehavesLikeTop[prog]
# ##            print 'child behave like top?? title %s, wanted: %s'% (title, wantedTitles)
#             if not wantedTitles:
#                 return 1   # found!
#             if type(wantedTitles) != types.ListType:
#                 wantedTitles = [wantedTitles]
# 
#             for t in wantedTitles:
#                 t = t.lower()
#                 if title.find(t) >= 0:
#                     print 'child window behaves like top: %s: %s'% (prog, title)
#                     return 1

#     def checkTopBehavesLikeChild(self, prog, title):
#         """check if prog and title match with self.topBehavesLikeChild
#         
#         obsolete, in favour of topWindowBehavesLikeChild (december 2017)
#         """
#         title = title.lower()
# ##        print 'self.childBehavesLikeTop: %s'% self.childBehavesLikeTop
#         if prog in self.topBehavesLikeChild:
#             wantedTitles = self.topBehavesLikeChild[prog]
# ##            print 'child behave like top?? title %s, wanted: %s'% (title, wantedTitles)
#             if not wantedTitles:
#                 return 1   # found!
#             if type(wantedTitles) != types.ListType:
#                 wantedTitles = [wantedTitles]
# 
#             for t in wantedTitles:
#                 t = t.lower()
#                 if title.find(t) >= 0:
#                     print 'top window behaves like child: %s: %s'% (prog, title)
#                     return 1

    def doStart2xExplorer(self):
        """starting the 2xExplorer

        """        
        command = 'AppBringUp "%s"'% self.xxExplorer
##                    print 'starting 2xExplorer: %s'% command
        natlink.execScript(command)
        natqh.Wait(1.0)
        keystroke("{alt+space}{extdown 4}{enter}")

    def gotoInThisComputer(self, f):
        """perform the keystrokes to go to a folder in this computer

        """
        keystroke('{alt+d}')
        action('W')
        keystroke(f)
        action('VW')
        if natqh.getWindowsVersion() == '7':
            keystroke('{enter}{shift+tab 3}')
        else:
            keystroke('{enter}{tab}')

    def gotoInThisDialog(self, f, hndle, className):
        """perform the keystrokes to go to a folder in a (#32770) Dialog

        """
        activeFolder = self.activeFolder or mess.getFolderFromDialog(hndle, self.className)
        keystroke('{alt+d}')
        if os.path.isdir(f):
            folder, filename = f, None
        elif os.path.isfile(f):
            folder, filename = os.path.split(f)
        else:
            print 'invalid target for gotoInThisDialog: %s'% f
            return
        
        if folder != activeFolder:
            # action("SCLIP %s{enter}") # here SCLIP does not work...
            keystroke(f)
            keystroke('{enter}')
        for i in range(4):
            action('W')
            keystroke('{shift+tab}')
        if filename:
            action("SCLIP %s"% filename)
            # keystroke(filename)
            
    def gotoInOtherExplorer(self, f):
        """pass keystrokes for "other explorers"
        
        from grammar _folders, in use now "xplorer2"
        
        """
        if self.useOtherExplorer == "xplorer2":
            keystroke("{shift+tab}%s{enter}{down}{up}"% f)
        else:
            print '_folders, please specify in function "gotoInOtherExplorer" for "use other explorer": "%s"'% self.useOtherExplorer

    def goUpInPath(self, Path, nsteps):
        """return a new path, n steps up in hierarchy
        """
        if not nsteps:
            nsteps = 1
        for i in range(nsteps):
            Path = os.path.normpath(os.path.join(Path, '..'))        
        return Path

    def gotoIn2xExplorer(self, f):
        """perform the keystrokes to go to a folder in the 2xExplorer

        """
        keystroke('{alt+f}t')
        keystroke(f)
        keystroke('{enter}')

        
    def doStartWindowsExplorer(self):
        natqh.rememberWindow()
        startExplorer = self.ini.get('general', 'start windows explorer')
        action(startExplorer)
        try:
            natqh.waitForNewWindow(50, 0.05)  # 2,5 seconds max
        except natqh.NatlinkCommandTimeOut:
            print 'Error with action "start windows explorer" (%s) from command in grammar + "_folders".' % \
                  startExplorer
            print 'Correct in ini file by using the command: ' + {'enx': "Edit Folders",
                                              'nld': "Bewerk folders"}[self.language]
            return
        return 1        
                                

    def fillDefaultInifile(self, ini=None):
        """initialize as a starting example the ini file (obsolete)

        """       
        pass


def getLongestCommon(tupleList, f):
    """first part of tupleList must match most of f"""
    m = 0
    pToTake = ''
    hToTake = 0
    for (p,h) in tupleList:
        nCommon = getCommonLength(p, f)
##        print 'nCommon %s and %s: %s'% (p,f,nCommon)
            
        if nCommon > m and nCommon > 3:
            pToTake = p
            hToTake = h
            m = nCommon
    if hToTake:
        return pToTake, hToTake

def getCommonLength(a, b):
    i = 0
    la = len(a)
    lb = len(b)
    
    while i < la and i < lb and a[i] == b[i]:
        i += 1
    return i

def getExplorerTitles():
    """get all titles of top windows with class name in tuple below

    This class name belongs, as far as I know, to the window explorer window

    """
    TitlesHandles = []
    ## Classes come from global variable at top of this module
    ##print 'Classes:', Classes
##    Classes = None
    win32gui.EnumWindows(getExplWindowsWithText, (TitlesHandles, Classes))
    return TitlesHandles

def getExplWindowsWithText(hwnd, th):
    TH, Classes = th
    if win32gui.GetClassName(hwnd) in Classes:
        # wTitle = win32gui.GetWindowText(hwnd).strip()  # ansi
        wTitle = getwindowtext(hwnd).strip()
        if wTitle and hwnd:
            TH.append((wTitle, hwnd))

def getwindowtext(hwnd):
    """unicode version of getwindowstext,
    need ctypes, see top of file
    """
    length = GetWindowTextLength(hwnd)
    buff = ctypes.create_unicode_buffer(length + 1)
    GetWindowText(hwnd, buff, length + 1)
    return buff.value

## functions for generating alternative paths in virtual drives
## uses reAltenativePaths, defined in the top of this module
## 
def generate_alternatives(s):
    m = reAltenativePaths.match(s)
    if m:
        alternatives = s[1:-1].split("|")
        for item in alternatives:
            yield item
    else:
        yield s
        
def cross_loop_alternatives(*sequences):
    if sequences:
        for x in generate_alternatives(sequences[0]):
            for y in cross_loop_alternatives(*sequences[1:]):
                yield (x,) + y
    else:
        yield ()

def loop_through_alternative_paths(pathdefinition):
    """can hold alternatives (a|b)
    
    so "(C|D):/natlink" returns first "C:/natlink" and then "D:/natlink".
    with more alternatives more items are returned "(C:|D:|E:)\Document(s|en)"
    """
    m = reAltenativePaths.search(pathdefinition)
    if m:
        result = reAltenativePaths.split(pathdefinition)
        result = [x for x in result if x and not x.startswith("|")]
        for pathdef in cross_loop_alternatives(*result):
            yield ''.join(pathdef)
    else:
        # no alternatives, simply yield the pathdefinition:
        yield pathdefinition
        
## from caster utilities at bringme:
def get_clipboard_formats():
    '''
    Return list of all data formats currently in the clipboard
    '''
    formats = []
    f = win32clipboard.EnumClipboardFormats(0)
    while f:
        formats.append(f)
        f = win32clipboard.EnumClipboardFormats(f)
    # print '_folders, clipboard formats: %s'% formats
    return formats

def get_selected_files(folders=False):
    '''
    Copy selected (text or file is subsequently of interest) to a fresh clipboard
    '''
    # cb = Clipboard(from_system=True)
    # cb.clear_clipboard()
    keystroke("{ctrl+c}")
    # Key("c-c").execute()
    time.sleep(0.1)
    files = get_clipboard_files(folders)
    # cb.copy_to_system()
    # print 'files: %s'% files
    return files

def get_clipboard_files(folders=False):
    '''
    Enumerate clipboard content and return files either directly copied or
    highlighted path copied
    '''
    files = None
    win32clipboard.OpenClipboard()
    f = get_clipboard_formats()
    if win32clipboard.CF_HDROP in f:
        files = win32clipboard.GetClipboardData(win32clipboard.CF_HDROP)
    else:
        # print 'get_clipboard_files, not expected clipboard format CF_HDROP, but %s'% f
        if win32clipboard.CF_UNICODETEXT in f:
            files = [win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)]
        elif win32clipboard.CF_TEXT in f:
            files = [win32clipboard.GetClipboardData(win32clipboard.CF_TEXT)]
        elif win32clipboard.CF_OEMTEXT in f:
            files = [win32clipboard.GetClipboardData(win32clipboard.CF_OEMTEXT)]
    if not files:
        # print "get_clipboard_files, no files found from clipboard"
        return
    if folders:
        files = [f for f in files if os.path.isdir(f)] if files else None
    else:
        files = [f for f in files if os.path.isfile(f)] if files else None
    win32clipboard.CloseClipboard()
    return files        

def makeFromTemplateAndExecute(folder, templatefile, exefile, prompt, text, default, inifile, section,  value, pausetime=0):
    """fill in in template actual values and execute the file
    
    meant for setting up a inputbox dialog
    """
    encoding, bom, Text = readwritefile.readAnything(os.path.join(folder, templatefile))
    # print Text
    for orig, toreplace in  [('$prompt$', prompt), ('$default$', default), ('$text$', text),
         ('$inifile$', inifile) , ('$value$', value), ('$section$', section),
         ('"$pausetime$"', str(pausetime))]:
        Text = Text.replace(orig, toreplace)
    if pausetime:
        outputfile = "foldersrememberdialog.py"
        pythonexe = "C:/python27/python.exe"
    else:
        outputfile = "foldersrememberdialog.pyw"
        pythonexe = "C:/python27/pythonw.exe"
        
    outputpath = os.path.join(folder, "foldersrememberdialog.py")
    readwritefile.writeAnything(outputpath, encoding, bom, Text)
    print 'wrote to: %s'% outputfile
    UnimacroBringUp(pythonexe, outputpath)    

        
def changeCallback(type, args):
    """special behaviour for martijn"""
    if ((type == 'mic') and (args=='on')):
        user = natqh.getUser()

## different functions#########################################3
outlookApp = None
outlookAppProgram = None
def connectOutlook():
    """connect to outlook"""
    global outlookApp, outlookAppProgram
    
    if outlookAppProgram != 'outlook' or not outlookApp:
        pass
        #outlookApp = win32com.client.Dispatch('Outlook.Application')
    if outlookApp:
        print 'outlook application collected'
        return outlookApp
    else:
        print 'outlook not connected'
        outlookApp = None
        outlookAppProgram = None
        return outlookApp
    

def collection_iter(collection):
    for index in xrange(collection.Count):
        yield collection.Item(index)
if __name__ == "__main__":
    print get_selected_files()
else:
    # standard stuff Joel (adapted for possible empty gramSpec, QH, unimacro)
    thisGrammar = ThisGrammar()
    if thisGrammar.gramSpec:
        thisGrammar.initialize()
    else:
        thisGrammar = None
    
    def unload():
        global thisGrammar, dialogGrammar
        if thisGrammar:
            natlink.setTimerCallback(None, 0)
            thisGrammar.unload()
        thisGrammar = None

