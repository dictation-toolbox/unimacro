# This file is part of a SourceForge project called "unimacro" see
# https://unimacro.SourceForge.net and https://qh.antenna.nl/unimacro
# (c) copyright 2003 see https://qh.antenna.nl/unimacro/aboutunimacro.html
#    or the file COPYRIGHT.txt in the natlink\natlink directory 
#
#  grammar: _folders.py
# Written by: Quintijn Hoogenboom (QH softwaretraining & advies)
# starting 2003, revised QH march 2011
# moved to the GitHub/Dictation-toolbox April 2020, improved vastly Febr 2024 (with partly new options)
#pylint:disable=C0302, W0613, W0702, R0911, R0912, R0913, R0914, R0915, W0212
#pylint:disable=E1101, C0209
r"""with this grammar, you can reach folders, files and websites from any window.
From some windows (my computer and most dialog windows) the folders and files
can be called directly by name if they are in the foreground.

If you are in a child window (often a file dialog window) the specified
folder is put into the filename text box, if you are in the Windows
Explorer or in the Internet Explorer file or drive is put in the
address text box, and otherwise a new window is opened with the
specified folder.

This grammar now makes use of ini files, to show and edit the contents
of the lists used.

Several "meta actions" are used, eg <<nameenter>> and <<filenameexit>>
when entering were exiting the file name text box in a file
dialog. These actions can be tailored for specific programs, like
some office programmes to behave different, or for WinZip. See examples
in actions.ini (call with "Edit Actions"/"Bewerk acties")

In the inifile also the commands for start this computer or start
windows explorer must be given. Correct these commands ("Edit
Folders"/"Bewerk folders") if they do not work correct.


This explorer is then taken if you are in or if Explorer is explicitly asked for.

The strategy for "New" and "Explorer" (when you say "new", "nieuw",
"explorer" in the folder command, are complicated, look below

"""            
import re
import pickle    #recentfoldersDict
import os
import sys
import time
import fnmatch
import urllib.request
import urllib.parse
import urllib.error
import ctypes    # get window text
from pathlib import Path
# from pprint import pprint
import win32gui
from win32com.client import Dispatch
import win32clipboard

import natlink
from natlinkcore import readwritefile
from natlinkcore import natlinktimer
from natlinkcore import natlinkstatus
from dtactions.unimacro import extenvvars
from dtactions import messagefunctions as mess
from dtactions import natlinkclipboard
from dtactions.unimacro.unimacroactions import doAction as action
from dtactions.unimacro.unimacroactions import doKeystroke as keystroke
# from dtactions.unimacro.unimacroactions import do_YESNO as YesNo
from dtactions.unimacro.unimacroactions import UnimacroBringUp
from dtactions.unimacro import unimacroutils
# from dtactions.unimacro.unimacroactions import Message
# from dtactions.unimacro import unimacroactions as actions
import unimacro.natlinkutilsbj as natbj
# from unimacro.unimacro_wxpythondialogs import InputBox
# import natlinkcore.natlinkutils as natut

thisDir = str(Path(__file__).parent)
status = natlinkstatus.NatlinkStatus()
# for getting unicode explorer window titles:
GetWindowText = ctypes.windll.user32.GetWindowTextW
GetWindowTextLength = ctypes.windll.user32.GetWindowTextLengthW

# for substituting environment variable like %HOME% in a file path:
# and %DESKTOP% in a file path.
# %HOME% defaults to your my documents folder, but can be in the system environment variables.
reEnv = re.compile('%([A-Z_]+)%')
reOnlyLowerCase = re.compile(r'^[a-z]+$')
reLettersSpace = re.compile(r'^[ \w]+$')
###########################################################
# for alternatives in virtual drive definitions:
reAltenativePaths = re.compile(r"(\([^|()]+?(\|[^|()]+?)+\))")

# classes for this computer and windows explorer:
Classes = ('ExploreWClass', 'CabinetWClass')

# together with track folders history:
# some child windows have to behave as top window (specified in ini file):
# note: title is converted to lowercase, only full title is recognised

ancestor = natbj.IniGrammar
class ThisGrammar(ancestor):
    """grammar for quickly going to folders, files and websites
    """
    #pylint:disable=R0902, R0904, C0116, W0201
    language = unimacroutils.getLanguage()
    name = "folders"
    iniIgnoreGrammarLists = ['subfolders', 'subfiles']
        # 'recentfolders' is filled via self.in inicngingData
         # subfolders and subfiles are filled on the fly and not saved for future use
    
    # commands with special status, must correspond to a right hand side
    # of a ini file entry (section foldercommands or filecommands)
    # remote, openwith have hardcoded details.
    optionalfoldercommands = ['new', 'explorer', 'paste', 'copy', 'remote']
    optionalfilecommands = ['copy', 'paste', 'edit', 'paste', 'remote', 'openwith']

    
    gramSpec = """
<folder> exported = folder ({folders}[<foldercommands>]);
<subfolder> exported = subfolder {subfolders}[<foldercommands>|<remember>];
<disc> exported = drive {letters} [<foldercommands>]; 
<thisfolder> exported = ((this|here) folder) (<foldercommands>|<remember>);
<foldercommands> = new | here | paste | on ({letters}|{virtualdrivesspoken}) |
                    <namepathcopy>| {foldercommands};
                   
<folderup> exported = folder up|folder up {n1-10};   
<recentfolder> exported = recent [folder] ({recentfolders}|SHOW|HIDE|RESET|START|STOP) [<foldercommands>];

<file> exported = file ({files}|{subfiles})[<filecommands>|<remember>];  
<thisfile> exported = ((here|this) file) (<filecommands>|<remember>); 
<filecommands> = {filecommands}| on ({letters}|{virtualdrivesspoken}) |
                ('open with') {fileopenprograms}|<namepathcopy>;

<website> exported = website {websites} [<websitecommands>]; 
<thiswebsite> exported = (this website) (<websitecommands>|<remember>);
<websitecommands> = ('open with') {websiteopenprograms}|
                    <namepathcopy>;
<remember> = remember;  
<namepathcopy> = (copy (name|path)) | ((name|path) copy);

"""

    def initialize(self):
        # self.envDict = natlinkcorefunctions.getAllFolderEnvironmentVariables()   # for (generalised) environment variables
        self.subfiles = self.subfiles = self.activeFolder = self.activeTimerFolder = None  # for catching on the fly in explorer windows (CabinetClassW)
        self.className = None
        self.dialogWindowTitle = "" # for recent folders dialog, grammar in natspeak.py
        self.dialogNumberRange = [] # ditto
        self.catchRemember = ""
        self.inTimerRecentFolders = False
        self.prevDisplayRecentFolders = None   # displaying recent folders list
        self.subfoldersDict = {}
        self.subfilesDict = {}
        self.foldersSet = set()
        if not self.language:
            print("no valid language in grammar "+__name__+" grammar not initialized")
            return
        self.load(self.gramSpec)
        self.switchOnOrOff() # initialises lists from inifile, and switches on
        
    def gotBegin(self,moduleInfo):
        if self.checkForChanges:
            self.checkInifile() # refills grammar lists and instance variables
                                # if something changed.
            if isinstance(self.checkForChanges, int) and self.checkForChanges > 0:
                self.checkForChanges -= 1
              
        if self.mayBeSwitchedOn == 'exclusive':
            print("exclusive (_folders), do switchOnOrOff")
            self.switchOnOrOff()

        self.progInfo = unimacroutils.getProgInfo()

        hndle = self.progInfo.hndle
        classname = self.progInfo.classname
        # activeFolder = self.getActiveFolder(hndle, classname)
        if self.trackFilesAtUtterance or self.trackSubfoldersAtUtterance:
            activeFolder = self.getActiveFolder(hndle, classname)
            self.handleTrackFilesAndFolders(activeFolder)
      
        if hndle and self.trackRecentFoldersAtUtterance:
            self.catchTimerRecentFolders(hndle, classname)
            
    def gotResultsInit(self,words,fullResults):
        if self.mayBeSwitchedOn == 'exclusive':
            print('recog folders, switch off mic')
            natbj.SetMic('off')
        self.wantedFolder = self.wantedFile = self.wantedWebsite = None
        self.catchRemember = None
        self.gotFolder = self.gotFile = self.gotWebsite = False ## for catching 
        
        # folder options:
        # CopyName and PasteName refers to the folder, file or website name
        # Cut, Copy Paste of file or folder is not implemented
        self.New = self.Here = self.Remote = self.Cut = self.Copy = self.Paste = self.CopyNamePath = self.PastePath = False
        # file options:
        # OpenWith goes via Open.
        self.Open = self.Edit = None
        self.FolderOptions = []
        self.FileOptions = []
        self.WebsiteOptions = []
        # redo getProgInfo, in case the focus did change:
        self.progInfo = unimacroutils.getProgInfo()


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
            # nFiles, nFolders = len(self.subfilesDict), len(self.subfoldersDict)
            # print(f'set {nFiles} (sub)files and {nFolders} subfolders')
            self.activeFolder = activeFolder
            return

    def fillList(self, listName):
        """fill a list in the grammar from the data of the inifile

        overload, because the list sites is special:reversed
        the section [site] must exist,on the right side is to spoken form.
        """

        if listName == 'folders':
            if self.foldersDict:
                items = list(self.foldersDict.keys())
                self.foldersSet = { self.substituteFolder(f) for f in self.foldersDict.values()}
                # print("foldersSet: %s"% self.foldersSet)
                self.setList('folders', items)
                return items
            print('no folders to set list to')
            self.emptyList('folders')
        elif listName == 'subfolders':
            if self.subfoldersDict:
                items = list(self.subfoldersDict.keys())
                self.setList('subfolders', items)
                return items
            print('no subfolders to set list to')
            self.emptyList('subfolders')

        elif listName == 'files':
            if self.filesDict:
                items = list(self.filesDict.keys())
                self.setList('files', items)
                return items
        elif listName == 'recentfolders':
            self.loadRecentFoldersDict()
            if self.recentfoldersDict:
                items = list(self.recentfoldersDict.keys())
                self.setList('recentfolders', items)
                return items
            self.emptyList('recentfolders')
        else:
            return ancestor.fillList(self, listName)
        return None

    def dumpRecentFoldersDict(self):
        """for making the dict of recent folders persistent
        """
        if self.pickleChangingData:
            dumpToPickle(self.recentfoldersDict, self.pickleChangingData)
        else:
            print('dumpRecentFoldersDict, no self.pickleChangingData')

    def loadRecentFoldersDict(self):
        """for getting the dict of recent folders from previous session
        """
        if self.pickleChangingData and Path(self.pickleChangingData).is_file():
            result = loadFromPickle(str(self.pickleChangingData))
            if result and isinstance(result, dict):
                self.recentfoldersDict = result
                return
        print('no recent folders dict')
        self.recentfoldersDict = {}

    def fillInstanceVariables(self):
        """fills the necessary instance variables
          take the lists of folders, virtualdrives (optional) and remotedrives (optional).
        
        """
        # valid options, value possibly corresponding to an previous option text
        optionsdict = {}
        optionsdict['initial on'] = ''
        optionsdict['child behaves like top'] = ''
        
        actualoptions = set(self.ini.get('general'))
        
        
        self.useOtherExplorer = self.ini.get('general', 'use other explorer')
        optionsdict['use other explorer'] = ''
        if self.useOtherExplorer:
            if os.path.isfile(self.useOtherExplorer):
                print('_folders, use as default explorer: "%s"'% self.useOtherExplorer)
            else:
                print('_folders, variable "use other explorer" set to: "%s" (use data from "actions.ini")'% self.useOtherExplorer)


        # these are for automatic tracking the current folder at an utterance:
        optionsdict['track files at utterance'] = 'automatic track files'
        optionsdict['track subfolders at utterance'] = 'automatic track folders'
        self.trackSubfoldersAtUtterance = self.ini.getInt('general', 'track subfolders at utterance', 0)
        self.trackFilesAtUtterance = self.ini.getInt('general', 'track files at utterance', 0)

        optionsdict['track recent folders at utterance'] = ''
        optionsdict['max recent folders'] = ''
        # track recent folder at gotbegin or with timer:
        ## callback time in seconds:
        optionsdict['timer track folders interval'] = ''
        interval = self.ini.getInt('general', 'timer track folders interval', 0)  # default 0 (off).
        if interval and interval > 100:
            print(f'_folders, warning, "timer track folders interval" should be set in seconds, not {interval}')
            interval = 0
        self.trackFoldersTimerInterval = int(interval*1000)  # give in seconds
        self.recentfoldersDict = {}
        
        self.trackRecentFoldersAtUtterance = self.ini.getBool('general', 'track recent folders at utterance')
        self.maxRecentFolders = 0 

        self.pickleChangingData = str(Path(status.getUnimacroDataDirectory())/"recentfoldersdata.pickle")
        if self.trackFoldersTimerInterval or self.trackRecentFoldersAtUtterance:

            optionsdict['max recent folders'] = ''                
            self.maxRecentFolders = self.ini.getInt('general', 'max recent folders', 50)        
            self.doTrackRecentFolders = True   # can be started or stopped with command
                                                # recent [folders] START or recent [folders] STOP
            intervalSeconds = int(self.trackFoldersTimerInterval/1000)
            if self.trackFoldersTimerInterval or self.trackRecentFoldersAtUtterance:
                if not self.trackFoldersTimerInterval:
                    print(f'maintain a list of (max) {self.maxRecentFolders} recent folders (Explorer or File Dialog) at every utterance')
                elif not self.trackRecentFoldersAtUtterance:
                    print(f'maintain a list of (max) {self.maxRecentFolders} recent folders (Explorer or File Dialog) every {intervalSeconds} seconds')
                else:
                    print(f'maintain a list of (max) {self.maxRecentFolders} recent folders (Explorer or File Dialog) at every utterance and every {intervalSeconds} seconds')
            if self.trackFoldersTimerInterval:                      
                natlinktimer.setTimerCallback(self.catchTimerRecentFolders, self.trackFoldersTimerInterval)  # every 5 seconds default...
        else:
            self.doTrackRecentFolders = False
        
        # virtual drives:
        # extract special variables from ini file:
        self.virtualDriveDict = {}
        wantedVirtualDriveList = self.ini.get('virtualdrives')
        if wantedVirtualDriveList:
            self.resolveVirtualDrives(wantedVirtualDriveList)
        self.virtualDriveList = list(self.virtualDriveDict.keys())
        # print '_folders, virtual drives from dict: %s'% repr(self.virtualDriveDict)
        # print '_folders, virtual drives from list: %s'% ', '.join(self.virtualDriveList)

        #  checking the passes of all folders:
        foldersList = self.ini.get('folders')
        self.foldersDict = {}
        for f in foldersList:
            raw_folder = self.ini.get('folders', f)
            folder = self.substituteFolder(raw_folder)
            if not os.path.isdir(folder):
                print(f'warning _folders,  folder "{f}" does not exist: "{folder}"')
                # self.ini.delete('folders', f)
                # self.ini.set('obsolete folders', f, folder)
                continue
            self.foldersDict[f] = folder
        
        # track virtual drives if in ini file:
        optionsdict['track folders virtualdrives'] = ''
        optionsdict['track files virtualdrives'] = ''
        self.trackFolders = self.ini.getList('general', 'track folders virtualdrives')
        self.trackFiles = self.ini.getList('general', 'track files virtualdrives')

        # in order to accept files in the list but it should be (for fnmatch) *.py etc.:
        optionsdict['track file extensions'] = ''
        optionsdict['ignore file patterns'] = ''

        self.acceptFileExtensions = self.ini.getList('general', 'track file extensions')
        self.ignoreFilePatterns = self.ini.getList('general', 'ignore file patterns')
        
            
        self.foldersSections = ['folders']
        # track folders:
        for trf in self.trackFolders:
            if not trf:
                continue
            trf2 = self.substituteFolder(trf)
            #print 'input: %s, output: %s'% (trf, trf2)
            if not os.path.isdir(trf2):
                print('warning, no valid folder associated with: %s (%s) (skip for track virtualdrives)'% (trf, trf2))
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
        self.filesSections = ['files']
        # from section files (manual):
        filesList = self.ini.get('files')
        if filesList:
            for f in filesList[:]:
                filename = self.substituteFilename(self.ini.get('files', f))
                if not os.path.isfile(filename):
                    print(f'warning _folders, file "{f}" does not exist: "{filename}"')
                    # self.ini.delete('files', f)
                    # self.ini.set('obsolete files', f, filename)
                    continue
                self.filesDict[f] = filename

        for trf in self.trackFiles:
            if not trf:
                continue
            trf2 = self.substituteFolder(trf)
            if not os.path.isdir(trf2):
                print('warning, no valid folder associated with: %s (%s) (skip for track files)'% (trf, trf2))
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
        
        self.checkValidOptions(optionsdict, actualoptions)

    def checkValidOptions(self, optionsdict, actualoptions):
        """check if all options given are valid and give feedback
        """
        validoptions = set(optionsdict)
        oldoptions = actualoptions - validoptions
        if oldoptions:
            print(f'obsolete options: {oldoptions}')
            # give new option, if available:
            for old in oldoptions:
                for k,v in optionsdict.items():
                    if v == old:
                        print(f'replace option "{old}" into "{k}" please')
                        break
        unusedoptions = validoptions - actualoptions
        for unused in unusedoptions:
            print(f'-- option "{unused}" is not set, grammar "_folders",\n\tplease set (possibly without value) in section [general]')

    def fillGrammarLists(self, listOfLists=None):
        """fills the lists of the grammar with data from inifile
        
        extra, the 'recentfolders' list in self.loadRecentFoldersDict
        (note: fillList is a specialised function of this grammar)

        """
        ancestor.fillGrammarLists(self)
        
        ## this one is ignored in the` parent class version of this function
        ## when recentfolders is not needed in the grammar, it raises a ValueError
        try:
            self.fillList('recentfolders')
        except ValueError:
            pass
    
    def resolveVirtualDrives(self, wantedVirtualDrives):
        """check the virtual drives, possibly recursive
        
        the valid virtual drives are put in self.virtualDriveDict
        the invalid virtual drives are sent to the obsolete virtual drives section
        
        no return, self.virtualDriveDict is filled.
        if no progress, make the remaining virtual drives obsolete...
        """
        if not wantedVirtualDrives:
            return ## nothing done
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
            textline = ", ".join(wantedVirtualDrives)
            print(f'Warning: could not resolve "virtualdrive" entries: {textline}, ignore')
            # for dr in wantedVirtualDrives:
            #     virtualDrive = self.ini.get('virtualdrives', dr)
            #     self.ini.delete('virtualdrives', dr)
            #     self.ini.set('obsolete virtualdrives', dr, virtualDrive)


    def getFolderFromVirtualDrive(self, vd):
        """check validity of virtual drive contents
        also make alternative paths possible  like (C|D):/Documents
        """
        # natlinkcorefunctions.printAllEnvVariables()
        vd = extenvvars.expandEnvVariables(vd)
        for possiblePath in loop_through_alternative_paths(vd):
            folder = self.substituteFolder(possiblePath)
            if os.path.isdir(folder):
                return os.path.normpath(folder)
        return None 

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
        spoken = [_f for _f in spoken if _f]
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
            if foldername:
                self.foldersDict[sp] = vd + ':/' +  foldername
            else:
                self.foldersDict[sp] = vd 

    def getActiveFolder(self, hndle=None, className=None):
        """get active folder (only explorer and dialog #32770)
        """
        if hndle is None:
            curmod = natlink.getCurrentModule()
            hndle = curmod[2]
        if not hndle:
            # print("getActiveFolder, not a foreground hndle found: %s"% hndle)
            return None
        if className is None:
            className = win32gui.GetClassName(hndle)
        # print 'getActiveFolder, className: %s'% className
        if not className:
            return None
        f = None

        if className == "CabinetWClass":
            f = mess.getFolderFromCabinetWClass(hndle)
        elif className == '#32770':
            f = mess.getFolderFromDialog(hndle, className)
        if not f:
            return None
        if os.path.isdir(f):
            nf = os.path.normpath(f)
            # print("getActiveFolder: %s"% nf)
            return nf
        print(f'getActiveFolder, strange invalid path for folder: "{f}"' )
        return None
    
    def fillListsForActiveFolder(self, activeFolder):
        """fill list of files and subfolders
        also set activeFolder and className
        
        this is for the automatic filling of the active window (either explorer, CabinetWClass,
        or child #32770.
       
        """
        subs = os.listdir(activeFolder)
        # print 'subs: %s'% subs
        subfolders = [s for s in subs if os.path.isdir(os.path.join(activeFolder, s))]
        subfiles = [s for s in subs if os.path.isfile(os.path.join(activeFolder, s))]
        if self.trackFilesAtUtterance:
            if len(subfiles) > self.trackFilesAtUtterance:
                print(f'_folders, only set first {self.trackFilesAtUtterance} files, total: {len(subfiles)}')
                subfiles = subfiles[:self.trackFilesAtUtterance]
            self.subfilesDict = self.getSpokenFormsDict(subfiles, extensions=1)
        else:
            self.subfilesDict = {}
        
        if self.trackSubfoldersAtUtterance:    
            if len(subfolders) > self.trackSubfoldersAtUtterance:
                print(f'_folders, only set first {self.trackSubfoldersAtUtterance} subfolders of total: {len(subfolders)}')
                subfolders = subfolders[:self.trackSubfoldersAtUtterance]
            self.subfoldersDict = self.getSpokenFormsDict(subfolders)
        else:
            self.subfoldersDict = {}
            
        # print 'activeFolder, %s, subfolders: %s'% (activeFolder, self.subfoldersDict.keys())
        # print 'activeFolder, %s, subfiles: %s'% (activeFolder, self.subfilesDict.keys())
        # print 'activeFolder, %s, subfiles: %s'% (activeFolder, self.subfilesDict)
        if self.subfilesDict:
            self.setList('subfiles', list(self.subfilesDict.keys()))
        if self.subfoldersDict:
            self.setList('subfolders', list(self.subfoldersDict.keys()))
        self.activeFolder = activeFolder
        if self.subfilesDict and self.subfoldersDict:
            print(f'activeFolder, set {len(subfiles)} files and {len(subfolders)} subfolders')
        elif self.subfilesDict:
            print(f'activeFolder, set {len(subfiles)} files')
        elif self.subfoldersDict:
            print(f'activeFolder, set {len(subfolders)} subfolders')
            

    def emptyListsForActiveFolder(self):
        """no sublists, empty
        """
        if self.trackFilesAtUtterance:
            self.emptyList('subfiles')
            self.subfilesDict.clear()
        if self.trackSubfoldersAtUtterance:
            self.emptyList('subfolders')
            self.subfoldersDict.clear()
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
                print('remove entry from ini folders section %s: %s (%s)'% (section, f, folder))
                self.ini.delete(section, f)
            elif not self.acceptFileName(f):
                print('remove entry from ini folders section %s: %s (%s)(invalid folder name)'% (section, f, folder))
                self.ini.delete(section, f)
        self.ini.writeIfChanged()

    def cleanupIniFilesSection(self, section, vd):
        """cleanup the current ini files ... section (for non existing files)
        """
        for f in self.ini.get(section):
            filename = self.substituteFolder(vd + ':/' + f)
            trunk, ext = os.path.splitext(f)
            if not self.acceptExtension(ext):
                print('remove entry from ini files section %s: %s (%s)(invalid extension)'% (section, f, filename))
                self.ini.delete(section, f)
            elif not self.acceptFileName(trunk):
                print('remove entry from ini files section %s: %s (%s)(invalid filename)'% (section, f, filename))
                self.ini.delete(section, f)
            elif not os.path.isfile(filename):
                print('remove entry from ini files section %s: %s (%s)'% (section, f, filename))
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
                print('_folders grammar, deleting ini file section: %s'% section)
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
        spoken = [_f for _f in spoken if _f]
        if spoken == ['xpqzyx'] or not spoken:
            spoken = [trunk]
            # skip if error in inivars:
            #try:
            #    self.ini.set(section, f, spoken)
            #except inivars.IniError:
            #    return

        if not spoken:
            return
        
        for sp in spoken:
            self.filesDict[sp] = vd + ':/' +  f
       
       
    def catchTimerRecentFolders(self, hndle=None, className=None):
        """this function is called back every ... seconds with timercallback
        
        Or with the subfolder or folder ... on virtual drive command.
        
        Whenever there is a folder in the foreground, it is cached as recentfolder.
        
        When the buffer grows too large, the first inserted items are removed from the list
        (QH, March 2020, Febr 2024)
        """
        # print('_folders, catchTimerRecentFolders')
        if self.inTimerRecentFolders:
            return
        self.inTimerRecentFolders = True
        try:
            activeFolder = self.getActiveFolder(hndle, className)
            if not activeFolder:
                return
            if activeFolder == self.activeTimerFolder:
                return
            self.activeTimerFolder = activeFolder
            # activeFolder = os.path.normcase(activeFolder)
            if self.recentfoldersDict and activeFolder == list(self.recentfoldersDict.values())[-1]:
                return
            spokenName = self.getFolderBasenameRemember(activeFolder)
            # print(f'add activeFolder "{activeFolder}" to recent, spoken name: "{spokenName}"')
            self.manageRecentFolders(spokenName, activeFolder)
        finally:
            self.inTimerRecentFolders = False

    def manageRecentFolders(self, Spoken, Folder):
        """manage the internals of the recent folders dict
        
        This can be called from the timer callback "catchTimerRecentFolders"
        Or from the subfolder or folder ... on virtual drive commands
        """
        # first see if the buffer needs to be shrinked:    
        buffer = max(10, self.maxRecentFolders//10)
        print(f'manageRecentFolders buffer: {buffer}, self.maxRecentFolders: {self.maxRecentFolders}, len(recentfoldersDict): {len(self.recentfoldersDict)}')
        if self.recentfoldersDict:
            if len(self.recentfoldersDict) > self.maxRecentFolders + buffer:
                print("shrink recentfoldersDict with %s items to %s"% (buffer, self.maxRecentFolders))
                while len(self.recentfoldersDict) >= self.maxRecentFolders:
                    keysList = list(self.recentfoldersDict.keys())
                    _removeItem = self.recentfoldersDict.pop(keysList[0])
                    # print('_folders, remove from recent folders: %s (%s)'% (keysList[0], removeItem))
                # print("refilling recentfolders list with %s items'"% len(self.recentfoldersDict))
                self.setList('recentfolders', list(self.recentfoldersDict.keys()))
                self.dumpRecentFoldersDict()

        if not Spoken:
            return
        if Spoken in self.recentfoldersDict:
            spokenFolder = self.recentfoldersDict[Spoken]
            if spokenFolder == Folder:
                print(f'readd {Spoken} to recentfoldersDict')
                del self.recentfoldersDict[Spoken]
                self.recentfoldersDict[Spoken] = Folder
                self.dumpRecentFoldersDict()
            elif Folder not in self.foldersSet:
                # print('-- "recent [folder] %s": %s\nNote: "folder %s", points to: %s'% (Spoken, Folder, Spoken, spokenFolder))
                del self.recentfoldersDict[Spoken]
                self.recentfoldersDict[Spoken] = Folder
                self.dumpRecentFoldersDict()
        else:
            # print('adding Folder in recent folders: %s (%s)'% (Spoken, Folder))
            self.recentfoldersDict[Spoken] = Folder
            self.appendList('recentfolders', Spoken)
            self.dumpRecentFoldersDict()
            # self.pickleChangingData.set("recentfolders", Spoken, Folder)
        # self.pickleChangingData.writeIfChanged()
    
    def startRecentFolders(self):
        self.doTrackRecentFolders = True
        self.fillList('recentfolders')
        timerInterval = self.trackFoldersTimerInterval
        if timerInterval: 
            print(f'start timer interval {timerInterval} milliseconds')
        else:
            timerInterval = 1000
            print(f'start timer with interval {timerInterval} milliseconds, for this session only')
        natlinktimer.setTimerCallback(self.catchTimerRecentFolders, self.trackFoldersTimerInterval)  # should have milliseconds
        
    def stopRecentFolders(self):
        self.doTrackRecentFolders = False
        natlinktimer.setTimerCallback(self.catchTimerRecentFolders, 0)
        self.dumpRecentFoldersDict()
        self.recentfoldersDict = {}
        self.emptyList('recentfolders')
        if self.trackFoldersTimerInterval:
            print("the track recent folders timer is stopped, for this session")
        else:
            print("the track recent folders timer is stopped.")
            
        
    def resetRecentFolders(self):
        self.recentfoldersDict = {}
        self.dumpRecentFoldersDict()
        # self.pickleChangingData.delete('recentfolders')
        # self.pickleChangingData.writeIfChanged()
        self.emptyList('recentfolders')
  
    def displayRecentFolders(self):
        """display the list of recent folders
        """
        mess_list = ["--- recent folders:"]
        if not self.recentfoldersDict:
            message = 'recent folders list is empty at the moment'
            self.prevDisplayRecentFolders = message
            print(message)
            return
        for name, value in reversed(self.recentfoldersDict.items()):
            mess_list.append('- %s: %s'% (name, value))
        mess_list.append('-'*20)
        message = '\n'.join(mess_list)  
        if message == self.prevDisplayRecentFolders:
            print("recent folders, no change")
        else:
            self.prevDisplayRecentFolders = message
            print(message)
        
        
    # def gotoRecentFolder(self, chooseNum):
    #     """service function which can be called fr_RECNTom natspeak_dialog
    #     pass the number of the choicelist (0 based)
    #     """
    #     wantedFolder = self.recentfoldersList[chooseNum]
    #     self.gotoFolder(wantedFolder)
       

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
        self.wantedWebsite = site
        
           
    def gotResults_thiswebsite(self,words,fullResults):
        """get current website and open with websitecommands rule
        
        """
        unimacroutils.saveClipboard()
        action('SSK {alt+d}{extend}{shift+exthome}{ctrl+c}')
        action("VW")
        self.wantedWebsite = unimacroutils.getClipboard()
        self.wantedWebsite = self.wantedWebsite.rstrip("/")
        self.catchRemember = "website"
        print('this website: %s'% self.wantedWebsite)
        unimacroutils.restoreClipboard()
        if self.hasCommon(words, "remember"):
            ## dgndictation is not used at the moment!!
            if self.nextRule == "dgndictation":
                self.catchRemember = "website"
            else:
                self.checkForChanges = True
                spokenWebsite = self.getWebsiteBasenameRemember(self.wantedWebsite)
                if not spokenWebsite:
                    print("_folders, could not extract a nice spoken website from %s\nTry "% self.wantedWebsite)
                    print('Try "this website remember as <dgndictation>"')
                    return
                self.ini.set("websites", spokenWebsite, self.wantedWebsite)
                print('with "website %s" you can now open %s'% (spokenWebsite, self.wantedWebsite))
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
        namePart = Path(filePath).stem
        spokenList = self.spokenforms.generateMixedListOfSpokenForms(namePart)
       
        if not spokenList:
            return namePart
        if len(spokenList) > 1:
            print('getFileBasenameRemember, more spoken alternatives found: %s, return first item'% spokenList)
        return spokenList[0]
        
    # def checkSubfolderRecent(self, name, folder):
    #     """add name to the recentfolders dict if appropriate
    #     """
    #     print("checkSubfolderRecent, try: %s: %s"% (name, folder))
    #     if name in self.foldersDict:
    #         if folder == self.foldersDict[name]:
    #             print("not for recent, already in foldersDict: %s"% name)
    #             return
    #         else:
    #             print("possibly clash, but include in recentfolders: %s, %s"% (name, folder))
    #     else:
    #         print("include in recentfolders: %s, %s"% (name, folder))
    #         
    #     # spokenList = self.spokenforms.generateMixedListOfSpokenForms(spoken)
    #     if name in self.recentfoldersDict:
    #         if self.recentfoldersDict[name] == folder:
    #             return  # all ok
    #         else:
    #             self.recentfoldersDict[name] = folder
    #             return   # no setList needed
    ## TODOQH::       
        # self.setList('recentfolders', list(self.recentfoldersDict.keys()))
        
    def getDuplicateFolders(self, wantedFolder):
        """get (spoken, folder) list for this wanted folder
        """
        wantedFolder = self.cleanpath(wantedFolder)
        duplicateNames = []
        # print 'wantedfolderclean: %s'% wantedFolder
        for spokenname, folderpath in self.foldersDict.items():
            folderpath = self.cleanpath(self.substituteFolder(folderpath))
            if folderpath == wantedFolder:
                duplicateNames.append(spokenname)
        return duplicateNames
    
    def cleanpath(self, somepath):
        """normalise path, and lowercase
        """
        p = str(Path(somepath))
        return p
    
    def getFolderBasenameRemember(self, folderPath):
        """extract the spoken name from the folder path
        """
        folderPath = Path(folderPath)
        namePart = folderPath.name
        spokenList = self.spokenforms.generateMixedListOfSpokenForms(namePart)
        if not spokenList:
            return namePart
        if len(spokenList) > 1:
            print('getFolderBasenameRemember, more spoken alternatives found: %s'% spokenList)
        return spokenList[0]
    
            
    def gotResults_websitecommands(self,words,fullResults):
        """start webbrowser, specified
        
        expect self.wantedWebsite to be filled.
        
        open with list in inifile, expected right hand sides to be browsers
        """
        if not self.wantedWebsite:
            print('websitecommands, no valid self.wantedWebsite: %s'% self.wantedWebsite)

        nextOpenWith = False

        for w in words:
            if self.hasCommon(w, 'open with'):
                nextOpenWith = True
            elif nextOpenWith:
                self.Open = self.getFromInifile(w, 'websiteopenprograms')
                nextOpenWith = False
            else:
                print("unexpected website option: %s"% w)

    def gotResults_subfolder(self, words, fullResults):
        """collects the given command words and try to find the given subfolder

        see above!! But do no actions if there is a rule after (remember, foldercommands)
        
        fill self.wantedFolder and self.Here (do in same folder, also if top)
        """
##        print '-------folder words: %s'% words
        folderWord = words[1]
        if self.activeFolder and folderWord in self.subfoldersDict:
            subfolder = self.subfoldersDict[folderWord]
            folder = os.path.join(self.activeFolder, subfolder)
        else:
            print('cannot find subfolder: %s'% folderWord)
            print('subfoldersDict: %s'% self.subfoldersDict)
            return
            # subfolder = None
            # folder1 = self.foldersDict[words[1]]
            # folder = self.substituteFolder(folder1)
            
        # if no next rule, simply go:
        self.wantedFolder = folder
        self.Here = True
        self.manageRecentFolders(folderWord, folder)
        
    def gotResults_recentfolder(self,words,fullResults):
        """give list of recent folders and choose option
        """
        if self.hasCommon("SHOW", words[-1]):
            self.displayRecentFolders()
            return
        if self.hasCommon("RESET", words[-1]):
            self.resetRecentFolders()
            print("Reset recent folders list")
            return
        if self.hasCommon("START", words[-1]):
            self.startRecentFolders()
            return
        if self.hasCommon("STOP", words[-1]):
            self.stopRecentFolders()
            return

        if not self.recentfoldersDict:
            print("no recentfolders yet")
            return
        name = words[-1]
        folder = self.recentfoldersDict[name]
        print("recentfolder, name: %s, folder: %s"% (name, folder))
        self.wantedFolder = folder
        
    def findFolderWithIndex(self, root, allowed, ignore=None):
        """get the first folder with a file index.html"""

        for i in allowed:
            tryF = os.path.join(root, i)
            if os.path.isdir(tryF) and (
                os.path.isfile(os.path.join(tryF, 'index.html')) or \
                os.path.isfile(os.path.join(tryF, 'index.txt'))):
                return tryF
        if ignore and isinstance(ignore, (list, tuple)):
            # look in listdir and take first that is not to be ignored:
            try:
                List = os.listdir(root)
            except:
                return None
            for d in List:
                if d in ignore:
                    continue
                tryF = os.path.join(root, d)
                if os.path.isdir(tryF) and os.path.isfile(os.path.join(tryF, 'index.html')):
                    return tryF
        return None

    def gotResults_folder(self, words, fullResults):
        """collects the given command words and try to find the given folder

        """
        if len(words) == 1:
            ## catch folder with dgndictation, postpone here:
            self.gotFolder = True
            return

        folder1 = self.foldersDict[words[1]]
        folder = self.substituteFolder(folder1)
        # actions in gotResults_remember or in gotResults
        self.wantedFolder = folder

    def gotResults_foldercommands(self, words, fullResults):
        """open the folder and do additional actions
        
        the optionalfoldercommands (like new or paste) must appear in the
        right hand side of the inifile section (ie the value) (so spoken may be
        different)
        """
        if not self.wantedFolder:
            print('rule foldercommands, no wantedFolder, return')
            return
        nextRemote = False
        for w in words:
            if self.hasCommon(w, 'here'):
                print("got Here: ", w)
                self.Here = True
            elif self.hasCommon(w, 'new'):
                print("got New: ", w)
                self.New = True
            elif self.hasCommon(w, 'paste'):
                print("got Paste, set PastePath: ", w)
                self.PastePath = True
            elif self.hasCommon(w, 'on'):
                print("got Remote: ", w)
                nextRemote = True
            elif nextRemote:
                remoteLetter =  self.getFromInifile(w, 'letters', noWarning=1)
                remoteVirtualDrive = self.getFromInifile(w, 'virtualdrivesspoken', noWarning=1)
                if remoteLetter:
                    print('remoteLetter: %s'% remoteLetter)
                    self.Remote = remoteLetter.upper() + ":"
                elif remoteVirtualDrive:
                    self.Remote = self.virtualDriveDict[remoteVirtualDrive]
                    print('remoteVirtualDrive: %s, resolves to: %s'% (remoteVirtualDrive, self.Remote))
                nextRemote = False
            else:
                opt = self.getFromInifile(w, 'foldercommands')
                print("got FolderOptions: ", opt)
                self.FolderOptions.append(opt)

    def gotResults_namepathcopy(self, words, fullResults):
        """copy the name or the path of a folder, file or website
        """
        if not self.catchRemember:
            print("_folders, namepathcopy, do not know what to copy, folder, file or website")
            return
        if self.hasCommon(words, "name"):
            what = "name"
        elif self.hasCommon(words, "path"):
            what = "path"
        else:
            print("_folders, namepathcopy, choose copy name or path, not: %s"% repr(words))
            return
        if self.catchRemember == "folder":
            if not self.wantedFolder:
                print("_folders, namepathcopy, no valid folder")
                return
            self.wantedFolder = self.wantedFolder.rstrip("/\\")
            if what == "name":
                result = os.path.split(self.wantedFolder)[-1]
            else:
                result = self.wantedFolder
        elif self.catchRemember == "file":
            if not self.wantedFile:
                print("_folders, namepathcopy, no valid file")
                return
            if what == "name":
                result = os.path.split(self.wantedFile)[-1]
            else:
                result = self.wantedFile

        elif self.catchRemember == "website":
            if not self.wantedWebsite:
                print("_folders, namepathcopy, no valid website")
                return
            if what == 'name':
                result = self.wantedWebsite.split("/")[-1]
            else:
                result = self.wantedWebsite.split()[-1]
        print('namepathcopy, result: %s (type: %s)'% (result, type(result)))
        unimacroutils.setClipboard(result, 13)   # 13 unicode!!

    def gotResults_remember(self, words, fullResults):
        """treat the remember function, filling items in ini files
        """
        if not self.catchRemember:
            print('_folders, in remember rule, but nothing to remember')
            return
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
            print('_folders, invalid value for catchRemember: %s'% self.catchRemember)
            return
        prompt = "Remember in Unimacro _folders grammar"
        inifile = self.ini._file
        inifile = inifile.replace("\\", "/")
        text = '\n\n'.join(texts)
        if not self.checkForChanges:
            self.checkForChanges = 10  # switch this on 10 utterances
        pausetime = 3
        # reset variables, no action in gotResults:
        self.wantedFile = self.wantedFolder = self.wantedWebsite = ""
        print(f'thisDir: {thisDir}')
        UnimacroDirectory = extenvvars.expandEnvVariableAtStart('%Unimacro%')
        print(f'UnimacroDirectory: {UnimacroDirectory}')
        UnimacroGrammarsDirectory = extenvvars.expandEnvVariableAtStart('%UnimacroGrammars%')
        print(f'UnimacroGrammarsDirectory: {UnimacroGrammarsDirectory}')
        makeFromTemplateAndExecute(UnimacroDirectory, "unimacrofoldersremembertemplate.py", UnimacroGrammarsDirectory, "rememberdialog.py",
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
        print("_folders: no active explorer.")
        return None        
    
    def get_current_directory(self, hndle=None):
        window = self.get_active_explorer(hndle)
        if window is None:
            return None
        path = urllib.parse.unquote(window.LocationURL)
        
        for prefix in ["file:///", "http://", "https://"]:
            if path.startswith(prefix):
                lenprefix = len(prefix)
                path = path[lenprefix:]
        return path

    def get_selected_paths(self):
        window = self.get_active_explorer()
        if window is None:
            print('get_selected_paths, cannot find application')
            return None
        items = window.Document.SelectedItems()
        paths = []
        for item in collection_iter(items):
            paths.append(item.Path)
        return paths

    def get_selected_filenames(self):
        paths = self.get_selected_paths()
        if paths is None:
            return None
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
                print('_folders, thisfile, mouse did not stop, cannot click')
                return
            unimacroutils.buttonClick(button, nClick)
            unimacroutils.visibleWait()

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
        unimacroutils.saveClipboard()
        unimacroutils.Wait()
        keystroke("{ctrl+c}")
        unimacroutils.Wait()
        paths1 = natlinkclipboard.Clipboard.get_system_folderinfo()
        unimacroutils.restoreClipboard() 

        if paths1:
            paths1 = [p for p in paths1 if os.path.isfile(p)]

        paths2 = get_selected_files(folders=False)
        print('get_system_folderinfo: %s'% paths1)
        print('get_selected_files: %s'% paths2)
        if paths1 and paths2:
            if paths1 == paths2:
                paths = paths1
            else:
                print('_thisfile, different info for both methods:\nVia Clipboard %s\nVia this module functions: %s'% \
                           (repr(paths1), repr(paths2)))
                paths = paths2
        elif paths1:
            print('_thisfile, only paths1 (via clipboard) has data: %s'% repr(paths1))
            paths = paths1
        elif paths2:
            paths = paths2
            print('_thisfile, only paths2 (this module functions) has data: %s'% repr(paths2))
        else:
            print('no paths info found with either methods')
            paths = None

        if not paths:
            print("no selected file found")
            return
        self.wantedFile = paths[0]
        if len(paths) > 1:
            print("warning, more files selected, take the first one: %s"% self.wantedFile)
        print('wantedFile: %s'% self.wantedFile)
        self.catchRemember = "file"

    def gotResults_disc(self,words,fullResults):
##        print '-------drive words: %s'% words
        letter = self.getFromInifile(words, 'letters')
        if letter:
            f = letter + ":\\"
        else:
            print('_folders, ruls disc, no letter provided: %s'% words)
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
        wantedFile = words[1]
        if self.activeFolder and wantedFile in self.subfilesDict:
            File = self.subfilesDict[wantedFile]
            extension =self.getFromInifile(words, 'extensions', noWarning=1)
            if extension:
                File, _old_extension = os.path.splitext (File)
                File = File +'.' + extension
                print('got file: %s'% File)
            File = os.path.join(self.activeFolder, File)
            if not os.path.isfile(File):
                print('folders, file, from subfilesList, not a valid path: %s (return None)'% File)
                File = None
            else:
                print('file from subfileslist: %s'% File)
            self.catchRemember = "file"
        if not File:
            try:
                File = self.filesDict[wantedFile]
            except KeyError:
                print('file cannot be found in filesDict: %s (and not in subfilesDict either)'% wantedFile)
                return
            File = self.substituteFolder(File)
            print("_folders, get file: actual filename (fixed fileslist): %s"% File)
            extension =self.getFromInifile(words, 'extensions', noWarning=1)
            if extension:
                File, _old_extension =os.path.splitext (File)
                File = File +'.' + extension
            if not os.path.isfile(File):
                print('invalid file: %s'% File)
                return
        if self.nextRule in ["filecommands", "remember"]:
            self.wantedFile = File
        else:
            self.gotoFile(File)
            self.wantedFile = None

    def gotResults_filecommands(self, words, fullResults):
        
        if not self.wantedFile:
            print('rule filecommands, no wantedFile, return')
            return
        # print 'filecommands: %s'% words
        OpenWith = Remote = False
        for w in words:
            if self.hasCommon(w, 'open with'):
                OpenWith = True
            elif OpenWith:
                self.Open = self.getFromInifile(w, 'fileopenprograms')
                OpenWith = False
            elif self.hasCommon(w, 'on'):
                Remote = True
            elif Remote:
                remoteLetter =  self.getFromInifile(w, 'letters', noWarning=1)
                remoteVirtualDrive = self.getFromInifile(w, 'virtualdrivesspoken', noWarning=1)
                if remoteLetter:
                    print('remoteLetter: %s'% remoteLetter)
                    self.Remote = remoteLetter.upper() + ":"
                elif remoteVirtualDrive:
                    self.Remote = self.virtualDriveDict[remoteVirtualDrive]
                    print('remoteVirtualDrive: %s, resolves to: %s'% (remoteVirtualDrive, self.Remote))
                Remote = False
            else:
                act = self.getFromInifile(w, 'foldercommands')
                print("got FileCommand: ", act)
                self.FileOptions.append(act)
       
    def gotResults_thisfolder(self,words,fullResults):
        """do additional commands for current folder
    
        can be reached with "this" or "here" (buttonclick)
        assume foldercommands or remember action follows, so only rememberBase and wantedFolder are given
        
        """
        # cb = natlinkclipboard.Clipboard(save_clear=True) ##TODO
        
        if self.hasCommon(words[0], "here"):
            ## wait for the mouse to have stoppede moving
            button, nClick = 'left', 1
            if not self.doWaitForMouseToStop():
                print("_folders, command thisfolder: doWaitForMouseToStop fails")
                return
            unimacroutils.buttonClick(button, nClick)
            unimacroutils.visibleWait()

        # now got attention, go ahead:
        self.wantedFolder = None        
        unimacroutils.saveClipboard()
        unimacroutils.Wait()
        keystroke("{ctrl+c}")
        unimacroutils.Wait()
        paths1 = natlinkclipboard.Clipboard.Get_folderinfo()
        unimacroutils.restoreClipboard()
        if paths1:
            paths1 = [p for p in paths1 if os.path.isdir(p)]
        paths2 = get_selected_files(folders=True)
        unimacroutils.Wait()
        if paths1 and paths2:
            if paths1 == paths2:
                paths = paths1
            else:
                print('_thisfolder, different info for both methods:\nVia Clipboard %s\nVia this module functions: %s'% \
                           (repr(paths1), repr(paths2)))
                paths = paths2
        elif paths1:
            print('_thisfolder, only paths1 (via clipboard) has data: %s'% repr(paths1))
            paths = paths1
        elif paths2: #
            paths = paths2
            print('_thisfolder, only paths2 (this module functions) has data: %s'% repr(paths2))
        else:
            print('no paths info found with either methods')
            paths = None
            
        print('paths:::: %s'% paths) #
        if paths:
            self.wantedFolder = paths[0]
            if len(paths) > 1:
                print("warning, more items selected, take the first one: %s"% self.wantedFolder)
        elif self.activeFolder:
            print('take activeFolder: %s'% self.activeFolder)
            self.wantedFolder = self.activeFolder
        else:
            print('"this folder" no selected folder found')
            return
        if os.path.isdir(self.wantedFolder):
            # print '_folders, this folder, wantedFolder: %s'% self.wantedFolder
            self.catchRemember = "folder" # in case remember follows
        else:
            print('_folders, wantedFolder not a valid folder: %s'% self.wantedFolder)
           
    #         
    def gotResults_folderup(self,words,fullResults):
        """ go up in hierarchy"""
        upn = self.getNumberFromSpoken(words[-1])
        #print 'folderup: %s'% upn
        _progpath, prog, title, _topchild, classname, hndle = self.progInfo
        IamExplorer = prog == 'explorer'
        IamChild32770 = classname == '#32770'
        browser = prog in ['iexplore', 'firefox','opera', 'netscp']
        # print 'iambrowser: %s Iamexplorer: %s'% (browser, IamExplorer)
        istop = self.getTopOrChild(self.progInfo, childClass="#32770")  # True if top window
        if IamChild32770:
            print("IamChild32770: ", self.activeFolder)
            if not self.activeFolder:
                self.activeFolder = mess.getFolderFromDialog(hndle, classname)
                print("IamChild32770 getFolderFromDialog: ", self.activeFolder)
            if self.activeFolder:
                newfolder = self.goUpInPath(self.activeFolder, upn)
                #print 'newfolder (up %s): %s'% (upn, newfolder)
                self.gotoInThisDialog(newfolder, hndle, classname)
            else:
                print('method not working (any more) for #32770: %s'% title)
            
        elif not istop:   # child window actions
            
            action("RMP 1, 0.02, 0.05, 0")
            action("<<filenameenter>>; {shift+tab}")
            action("{backspace %s}"% upn)
        elif browser:
            unimacroutils.saveClipboard()
            keystroke('{alt+d}{extend}{shift+exthome}{ctrl+c}')
            t = unimacroutils.getClipboard()
            prefix, path = t.split('://')
            T = path.split('/')
            if len(T) > upn:
                T = T[:-int(upn)]
            else:
                T = T[0]
            
            keystroke(prefix + '://' + '/'.join(T))
            keystroke('{enter}')
            unimacroutils.restoreClipboard()
        elif IamExplorer:
            if not self.activeFolder:
                self.activeFolder = mess.getFolderFromCabinetWClass(hndle)
            if self.activeFolder:
                newfolder = self.goUpInPath(self.activeFolder, upn)
                print('newfolder (up %s): %s'% (upn, newfolder))
                self.gotoInThisComputer(newfolder)
            else:
                print('method not working any more, going folder up')
                action("MP 1, 50, 10, 0")
                for _i in range(upn):
                    action("{backspace} VW")
            
        else:            
            print('yet to implement, folder up for  %s'% prog)
            
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
        # if not self.virtualDriveDict:
        #     #print 'no virtualDriveDict, return %s'% folder
        #     return folder
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
                return os.path.normpath(os.path.join(vd, rest))
            return os.path.normpath(vd)
        return os.path.normpath(folder)

    def substituteEnvVariable(self,folder):
        """honor environment variables like %HOME%, %PROGRAMFILES%

        %HOME% is also recognised by ~ (at front of name)
        
        With expandEnvVars, also NATLINK and related variables can be handled.
        NATLINKDIRECTORY, COREDIRECTORY etc.
        """
        substitute = extenvvars.expandEnvVariables(folder)
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
            if spokenList:
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
        return None
    
    def acceptFileName(self, item, extensions=None):
        """return 1 if filename ok, only filename expected here
        """
        for pat in self.ignoreFilePatterns:
            if fnmatch.fnmatch(item, pat):
                return None
        return 1

    def gotoWebsite(self, f):
        """goto the file f, options in instance variables
        
        FileOptions: list
        Remote, False or the virtual drive to be inserted
        Open, False or app to Open with (default)
        Edit, False or app to Edit with, if fails, take Notepad

        """
        if self.Open:
            print("gotoWebsite %s with: %s", (f, self.Open))
        else:
            print("gotoWebsite: ", f)
        self.openWebsiteDefault(f, openWith=self.Open)

    def gotoFile(self, f):
        """goto the file f, options in instance variables
        
        FileOptions: list
        Remote, False or the virtual drive to be inserted
        Open, False or app to Open with (default)
        Edit, False or app to Edit with, if fails, take Notepad
        """
        if not os.path.isfile(f):
            self.DisplayMessage('file does not exist: %s'% f)
            return
        # istop logic, with functions from action.py module, settings from:
        # child behaves like top = natspeak: dragon-balk
        # top behaves like child = komodo: find, komodo; thunderbird: bericht opslaan
        # in actions.ini:
        istop = self.getTopOrChild( self.progInfo, childClass="#32770") # True if top
    
        if self.Remote:
            print('Remote: %s'% self.Remote)
            f = self.getValidFile(f, self.Remote)
            
            if not f:
                return
            
        mode = 'edit'        
        if self.Open:
            mode = 'open'

        if self.CopyNamePath:
            unimacroutils.setClipboard(f)
            return
        if self.Paste:
            action("SCLIP %s"%f)
            # keystroke(f)
            return

        if not istop:   # child window actions
            # put the mouse in the left top corner of the window:
            print("Open file from child window: %s"% f)
            action("RMP 1, 0.02, 0.05, 0")
            action('<<filenameenter>>')
            unimacroutils.saveClipboard()
            keystroke('{Ctrl+x}')
            keystroke(f)
            action('<<filenameexit>>')
            keystroke('{Ctrl+v}')
            unimacroutils.restoreClipboard()
            keystroke('{Shift+Tab}')
        else:
            # top or top behaviourthis
            self.openFileDefault(f, mode=mode)
        
    def openFileDefault(self, filename, mode=None, windowStyle=None, name=None, openWith=None):
        """open the file according to the options given
        
        The passed keyword arguments are identical to those in the ancestor class, but hardly used.
        
        Open, Edit and FileOptions, see above
        """
##        action('CW')
        if not os.path.isfile(filename):
            print('file does not exist, cannot open: %s'% filename)
            return
        if not ancestor.openFileDefault(self, filename, mode=mode, openWith=openWith):
            print('could not open %s (mode: %s, openWith: %s)'% (filename, mode, openWith))
            return
        try:
            # try is needed in case function is called from another class (dirty trick with _control, sorry)
            for act in self.FileOptions:
                if act:
                    action(act)
        except AttributeError:
            pass

    def openFolderDefault(self, foldername, mode=None, windowStyle=None, openWith=None):
        """open the folder in the default window
         LW() 
        if succeed, perform optional additional options.
        
        """
##        action('CW')
        #print 'going to open folder: %s'% foldername
            
        if not ancestor.openFolderDefault(self, foldername, mode=mode, openWith=openWith):
            print('failed to open folder: %s'% foldername)
            return
        
        for act in self.FolderOptions:
            if act:
                print("openFolderDefault, action: %s"% act)
                action(act)
            
    #  This is the function which does the real work, depending on the
    #    window you are in
    def gotoFolder(self, f):
        """go to the specified folder
        
        all the options are via instance variables, New, Here, Copy, Paste, Remote (all False by default)
        and FolderOptions (a list, initially empty).
        
        f = the (local) folder to go to

        Options that can be set to True(ish)
        --New: a new window is wanted
        --Here: if you want to remain in the same window
                -for top windows: if explorer OK, otherwise paste the path.
                -for child windows: default if file dialog window (#32770), otherwise paste the path)
        --Remote: pass the (virtual) drive where the folder is wanted
        --Copy: investigate
        --Paste: only paste the path at the place where you are.

        this is the central routine, with complicated strategy for getting it,
        in pseudocode:
        
        if New:
            get new explorer folder
        elif Here:
            if Top and explorer:
                open in same window
            if Top and other program:
                paste text of folder
            if child and #32770 file dialog:
                (Here is default)
                goto the folder in this dialog
            if child and NOT file dialog:
                paste text of folder
        elif Paste:
            just paste text of folder
        elif Copy:
            more details, but get the name of path of the called folder (or this folder) on the clipboard
        else:
            if Top and explorer:
                open in same window if new folder is in same tree
            if Top and other program:
                open in new window, looking for nearest window if possible, see below
            if child and #32770 file dialog:
                goto the folder in this dialog
            if child and NOT file dialog:
                open in new window, looking for nearest window if possible, see below

            when looking for best fitting window alread open:
                look for all for the Windows with titles
                ## TODOQH
                if exact:
                    go to that folder window
                elif overList: (titles are longer than folder asked for)
                    get folder in nearest window 
                    (if you are already there, switch to the folder you want)
                elif underList: (titles are shorter than folder you asked for)
                    take longest of the windows, if you are in goto exact
                else:
                    if part of path is common, switch to that and goto folder

        """
        ## undoncitionally if folderoption New is used:
        if self.New:
            self.openFolderDefault(f)
            return                    
        
        prog = self.progInfo.prog
        f = os.path.normpath(f)
        if not os.path.isdir(f):
            self.DisplayMessage('folder does not exist: %s'% f)
            return
        
        if prog == 'cmd':
            print("_folder, for cmd: %s"% f)
            # t = " " + f
            action('SCLIP(%s)'% f)
            return
        
        if self.Remote:
            print('Remote: %s'% self.Remote)
            f = self.getValidDirectory(f, self.Remote)
            print('Remote: %s'% f)
            if not f:
                return
        if self.PastePath:
            action("SCLIP(%s)"%f)
            print("PastePath: %s"% f)
            return  # 
        if self.CopyNamePath:
            print('put path on clipboard: "%s"'% f)
            unimacroutils.setClipboard(f)
            return

        istop = self.getTopOrChild(self.progInfo, childClass="#32770")
        prog = self.progInfo.prog
        hndle = self.progInfo.hndle
        if not hndle:
            print('_folders, gotoFolder: no window handle found, return')
        # Iam2x = prog == '2xexplorer'
        IamExplorer = prog == 'explorer'
        _browser = prog in ['iexplore', 'firefox','opera', 'netscp', 'brave']
##        print 'iambrowser:', browser
##        print 'xx: %s, Iam2x: %s, IamExplorer: %s'% (xx, Iam2x, IamExplorer)
##
        IamExplorer = prog == 'explorer'
        IamChild32770 = (not istop) and win32gui.GetClassName(hndle) == '#32770'
        if IamChild32770:
            self.className = '#32770'
        if IamChild32770:
            self.activeFolder = self.getActiveFolder()
            if self.activeFolder:
                # print("go from here activeFolder: %s"% self.activeFolder)
                self.gotoInThisDialog(f, hndle, self.className)
                return
            print("no files/folder dialog, treat as top window")
            self.openFolderDefault(f)
            return
                
        if not istop:   # child window actions
            # put the mouse in the left top corner of the window:
            print("_folders, child window, comes ever here???")
            action("RMP 1, 0.02, 0.05, 0")
            action('<<filenameenter>>')
            unimacroutils.saveClipboard()
            keystroke('{Ctrl+x}')
            keystroke(f)
            action('<<filenameexit>>')
            keystroke('{Ctrl+v}')
            unimacroutils.restoreClipboard()
            keystroke('{Shift+Tab}')
            return

        ## now istop:
        if self.Here:
            if IamExplorer:
                self.gotoInThisComputer(f)
            else:
                # paste, the best we can do
                action("SCLIP %s"%f)
            return

        ## now the big search for the most appropiate window
        ## TODOQH should be looked into:
        LIST = getExplorerTitles()
        if not LIST:
            self.openFolderDefault(f)
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
                print('warning, 2 matching windows: %s'% exactList)
            t, h = exactList[0]
            unimacroutils.SetForegroundWindow(h)
        elif overList:
##            print 'over List %s' % (overList)
            # eg f = d:\\a\\b
            # and elements of overList are d:\\a\\b\\c and d:\\a\\b\\c\\d
            # goto shortest element
            # later make choice list of where to go
            if len(overList) == 1:
                t, h = overList[0]
                unimacroutils.SetForegroundWindow(h)
            lenMin = 999
            for t, h in overList:
##                    print 'nearList: %s'% nearList
                if len(t) < lenMin:
                    take = h
                    lenMin = len(t)
                
##                print 'i: %s, take: %s'% (i, nearList[i])
            toHandle = take
            thisHandle = hndle   ## ?? TODO
            if thisHandle == toHandle:
                self.gotoInThisComputer(f)
            else:
                unimacroutils.SetForegroundWindow(take)
        elif underList:
            # eg f = d:\\a\\b\\c
            # elementes of underList are d:\\a d:\\a\\b etc.
            # go to longest element and switch in that window to folder
            print('under list, go to first folder')
            lenMax = 0
            
            for t, h in underList:
##                    print 'nearList: %s'% nearList
                if len(t) > lenMax:
                    take = h
                    lenMax = len(t)
            if unimacroutils.SetForegroundWindow(take):
                self.gotoInThisComputer(f)

        elif restList:
##            print 'rest list, go to first folder'
            # get longest "intersection" of restList and f
            # being the most convenient window for displaying the folder
            take = getLongestCommon(restList, f) # tuple (title, handle)
##            print 'take: ', `take`
            if take:
                t, h = take
                if unimacroutils.SetForegroundWindow(h):
                    self.gotoInThisComputer(f)
                else:
                    print('could not set foregroundwindow: %s'% h)
                    self.openFolderDefault(f)  
                    
            else:
                #print 'no matching window at all, start new'
                self.openFolderDefault(f)
        else:
            # no this computer windows (yet)
            print("grammar folders shouldn't be here!")  


    def getValidDirectory(self, f, remote):
        r"""substitute remote in front of f and try to find a valid directory
        
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
        _fdrive, fdir = os.path.splitdrive(f)
        fparts = [part for part in fdir.split(os.sep) if part]
        while fparts:
            fpart = os.sep.join(fparts)
            tryF = os.path.join(remote + os.sep, fpart)
            if os.path.isdir(tryF):
                return tryF
            fparts.pop(0)
        print('_folders, no valid remote folder found for %s and remote: %s'% (f, remote))
        return ''

    def getValidFile(self, f, remote):
        _fdrive, fdir = os.path.splitdrive(f)
        fparts = [part for part in fdir.split(os.sep) if part]
        while fparts:
            fpart = os.sep.join(fparts)
            tryF = os.path.join(remote + os.sep, fpart)
            if os.path.isfile(tryF):
                return tryF
            fparts.pop(0)
        print('_folders, no valid remote file found for %s and remote: %s'% (f, remote))
        return ''

    
    def gotResults(self, words,fullResults):
        """at last do most of the actions, depending on the variables collected in the rules.
        """
        if self.wantedFolder:
            self.gotoFolder(self.wantedFolder)
        if self.wantedFile:
            self.gotoFile(self.wantedFile)
        if self.wantedWebsite:
            self.gotoWebsite(self.wantedWebsite)

    def gotoInThisComputer(self, f):
        """perform the keystrokes to go to a folder in this computer

        """
        keystroke('{alt+d}')
        action('W')
        keystroke(f)
        action('VW')
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
            print('invalid target for gotoInThisDialog: %s'% f)
            return
        
        if folder != activeFolder:
            # action("SCLIP %s{enter}") # here SCLIP does not work...
            keystroke(f)
            keystroke('{enter}')
        for _i in range(4):
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
            print('_folders, please specify in function "gotoInOtherExplorer" for "use other explorer": "%s"'% self.useOtherExplorer)

    def goUpInPath(self, PATH, nsteps=None):
        """return a new path, n steps up in hierarchy, default 1
        """
        if not nsteps:
            nsteps = 1
        for _i in range(nsteps):
            PATH = os.path.normpath(os.path.join(PATH, '..'))        
        return PATH

    def gotoIn2xExplorer(self, f):
        """perform the keystrokes to go to a folder in the 2xExplorer, obsolete

        """
        keystroke('{alt+f}t')
        keystroke(f)
        keystroke('{enter}')

        
    def doStartWindowsExplorer(self):
        unimacroutils.rememberWindow()
        startExplorer = self.ini.get('general', 'start windows explorer')
        action(startExplorer)
        try:
            unimacroutils.waitForNewWindow(50, 0.05)  # 2,5 seconds max
        except unimacroutils.NatlinkCommandTimeOut:
            print('Error with action "start windows explorer" (%s) from command in grammar + "_folders".' % \
                  startExplorer)
            print('Correct in ini file by using the command: ' + {'enx': "Edit Folders",
                                              'nld': "Bewerk folders"}[self.language])
            return None
        return 1        
                                

    def fillDefaultInifile(self, ini=None):
        """initialize as a starting example the ini file (obsolete)

        """       


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
    return None

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
    TH, classes = th
    if win32gui.GetClassName(hwnd) in classes:
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
    r"""can hold alternatives (a|b)
    
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
    try:
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
            return None
        if folders:
            files = [f for f in files if os.path.isdir(f)] if files else None
        else:
            files = [f for f in files if os.path.isfile(f)] if files else None
    finally:
        win32clipboard.CloseClipboard()
    return files        

def makeFromTemplateAndExecute(unimacrofolder, templatefile, unimacrogrammarsfolder, exefile, prompt, text, default, inifile, section,  value, pausetime=0):
    """fill in in template actual values and execute the file
    
    meant for setting up a inputbox dialog
    """
    rwfile = readwritefile.ReadWriteFile()
    print(f'unimacrofolder: {unimacrofolder}')
    Text = rwfile.readAnything(os.path.join(unimacrofolder, templatefile))
    # print(f'OldText: {Text}')
    for orig, toreplace in  [('$prompt$', prompt), ('$default$', default), ('$text$', text),
         ('$inifile$', inifile) , ('$value$', value), ('$section$', section),
         ('"$pausetime$"', str(pausetime))]:
        Text = Text.replace(orig, toreplace)
    # print(f'newText: {Text}')
    if not (exefile and exefile.endswith('.py')):
        raise ValueError(f'makeFromTemplateAndExecute, outputfile should end with ".py", not {exefile}')
    if pausetime:
        outputfile = exefile
        pythonexe = Path(sys.prefix)/'python.exe'
    else:
        outputfile = exefile + 'w'
        pythonexe = Path(sys.prefix)/'pythonw.exe'
        
    outputpath = os.path.join(unimacrogrammarsfolder, outputfile)
    rwfile.writeAnything(outputpath, Text)
    # print('wrote to: %s'% outputfile)
    # print(f'output dialog: {outputpath}, python: {pythonexe}')
    UnimacroBringUp(str(pythonexe), outputpath)    


## different functions#########################################3
outlookApp = None
outlookAppProgram = None
def connectOutlook():
    """connect to outlook"""
    #pylint:disable=W0603
    global outlookApp, outlookAppProgram
    
    if outlookAppProgram != 'outlook' or not outlookApp:
        pass
        #outlookApp = win32com.client.Dispatch('Outlook.Application')
    if outlookApp:
        print('outlook application collected')
        return outlookApp
    print('outlook not connected')
    outlookApp = None
    outlookAppProgram = None
    return outlookApp


def loadFromPickle(picklePath):
    """retrieve from pickle file, None if error
    """
    # print("loadFromPickle %s"% picklePath)
    try:
        with open(picklePath, 'rb') as pp:
            data = pickle.load(pp)
            # print("data loaded %s"% len(data))

            return data
    except:
        return None
    
def dumpToPickle(data, picklePath):
    """dump the data to picklePath
    """
    # print("dumpToPickle %s, %s"% (picklePath, len(data)))
    try:
        with open(picklePath, 'wb') as pp:
            pickle.dump(data, pp)
    except:
        pass

    

def collection_iter(collection):
    for index in range(collection.Count):
        yield collection.Item(index)


# standard stuff Joel (adapted for different calling methods, including tests QH, unimacro)
def unload():
    #pylint:disable=W0603
    global thisGrammar
    # print("function unload in _folders.py")
    if thisGrammar:
        # print("unloading folders grammar")
        thisGrammar.stopRecentFolders()  # stopping the timer callback
        thisGrammar.unload()
        print("unloaded folders grammar")
        thisGrammar = None

if __name__ == "__main__":
    ## interactive use, for debugging:
    natlink.natConnect()
    try:
        thisGrammar = ThisGrammar(inifile_stem="_folders")
        # thisGrammar.startInifile()
        thisGrammar.initialize()

        # get hndle of a explore window (via _general "give window info") and try interactive
        # thisGrammar.catchTimerRecentFolders(132524, "CabinetWClass")
        thisGrammar.getActiveFolder(198518)


        # # Words = ['folder', 'dtactions']
        # Fr = {}
        # Words = ['subfolder', 'hello']
        # thisGrammar.gotResultsInit(Words, Fr)
        # thisGrammar.gotResults_subfolder(Words, Fr)
    finally:
        thisGrammar.unload()
        natlink.natDisconnect()
elif __name__.find('.') == -1:
    # standard startup when Dragon starts:
    thisGrammar = ThisGrammar()
    thisGrammar.initialize()
