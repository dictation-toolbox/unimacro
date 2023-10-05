from natlinkcore import natlinkutils
import natlink
import os
import os.path
import time

class ThisGrammar(natlinkutils.GrammarBase):

    gramSpec = """
<trayicon> exported = test tray icon;
        """

    def initialize(self):
        self.load(self.gramSpec)
        self.activateAll()
        #self.gotResults_trayicon(None, None)

    def gotBegin(self, moduleInfo):
        pass

#  starting message
    def gotResults_trayicon(self, words, fullResults):


        #iconDir = r'D:\natlink\unimacro\icons'
        #for name in ['repeat', 'repeat2', 'waiting', 'waiting2']:
        #    iconPath = os.path.join(iconDir, name+'.ico')
        #    print 'iconPath', iconPath
        #    natlink.setTrayIcon(iconPath)
        #    time.sleep(0.5)
        #
        ## remove the icon:
        #natlink.setTrayIcon()
        self.stopShowing = 0  # can be used for interrupt by clicking on the tray icon...
        self.directions = ['right', 'down', 'up', 'left']
        self.loops = 12
        self.currentLoop = 0
        self.currentDirection = 0
        natlink.setTimerCallback(self.doNextIcon, 500)  # each 500 milliseconds
        
    def doNextIcon(self):
        if self.stopShowing:
            print('caught callback, stop the looping')
            natlink.setTrayIcon()
            natlink.setTimerCallback(None)
            return
        if self.currentLoop >= self.loops:
            self.currentLoop = 0
            self.currentDirection += 1
            if self.currentDirection >= len(self.directions):
                print('ready all done, remove the icon and stop the timercallback')
                natlink.setTrayIcon()
                natlink.setTimerCallback(None)
        if self.currentLoop%2:
            iconName = '%s2'% self.directions[self.currentDirection]
        else:
            iconName = '%s'% self.directions[self.currentDirection]
        print('set trayIcon: %s'% iconName)
        natlink.setTrayIcon(iconName, 'test also click on icon %s'% iconName, self.onTrayIcon)
        
    def onTrayIcon(self, message):
        """calls back into this function if the tray icon is clicked upon
        """
        print('caught the onTrayIcon callback, clicked on the tray icon with button: %s'% message)
        # remove the icon:
        self.stopShowing = 1
        
# standard stuff Joel (adapted for possible empty gramSpec, QH, unimacro)
thisGrammar = ThisGrammar()
if thisGrammar.gramSpec:
    thisGrammar.initialize()
else:
    thisGrammar = None

def unload():
    #pylint:disable=W0603
    global thisGrammar
    if thisGrammar: thisGrammar.unload()
    thisGrammar = None

