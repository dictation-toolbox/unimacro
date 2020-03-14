__version__ = "$Rev: 606 $ on $Date: 2019-04-23 14:30:57 +0200 (di, 23 apr 2019) $ by $Author: quintijn $"
# This file is part of a SourceForge project called "unimacro" see
# http://unimacro.SourceForge.net and http://qh.antenna.nl/unimacro
# (c) copyright 2003 see http://qh.antenna.nl/unimacro/aboutunimacro.html
#    or the file COPYRIGHT.txt in the natlink\natlink directory 
#
# Firefox, numbers mode
#
# assumes Hint-a-Hint extension from Pekka Sillanpaa (mode = "hah" )
# Or
# Mouseless Browsing extension from Rudolf Noe (mode = "mlb")
#
# set in line 61 below================================================
#
#
# written by: Quintijn Hoogenboom (QH software, training & advies)
#
# the lists {n1-9}, {n1-20} are constructed in internal grammar functions
#
# the lists {pagecommands} and {tabcommands} in the inifile (edit firefox hah)
#
"""
This command grammar up to now is:

get numbers | show numbers | toggle numbers
numbers off|cancel|clear numbers
choose #
choose # new tab|new window

(# is a number that can go as high as 300)

for going forward and back in pages (and refreshing pages):

next page | previous page |  refresh page
page back <1-20> | page forward <1-20>

For tabbed browsing:

previous tab | next tab | refresh tab | close tab
tab number # |  tab number # close | tab number # refresh
"""


import natlink
natqh = __import__('natlinkutilsqh')
natut = __import__('natlinkutils')
natbj = __import__('natlinkutilsbj')
from actions import doAction as action
from actions import doKeystroke as keystroke

# some fixed keystrokes:
getNumbers = dict(hah='{ctrl+,}', mlb='{NumKey.}')  #keystrokes to get the numbers
Escape = dict(hah='{esc}', mlb='{esc}')
waitBeforeNewNumbers = 0.8
visiblePause = 0.4

language = natqh.getLanguage()

#SET THIS TO "hah" or "mlb":
mode = "mlb"

ancestor = natbj.IniGrammar
class ThisGrammar(ancestor):

    try:
        numberGram = natbj.numberGrammarTill999[language]
    except KeyError:
        print('take number grammar from "enx"')
        numberGram = natbj.numberGrammarTill999['enx']
        
    if language == "nld":
        name = 'Faajer foks brouwsen'
    else:
        name = 'Firefox Browsing'

    gramSpec = """
<getnumbers> exported = (give|hide|toggle) numbers |
                            numbers on;
<choose>     exported = (follow|focus|new) <integer> |
                        (follow) <integer> ('new tab' | 'context menu'|snelmenu);
<cancelnumbers> exported = numbers off | clear numbers;

<navigatepages> exported = (next|previous|{pagecommands}) page |
                            page (back|forward) | page (back|forward) {n1-20} |
                            page {pagecommands} |
                            (next|previous) page | (next|previous) page {pagecommands};

<navigatetabs> exported = (next|previous) tab | (next|previous) tab {tabcommands} |
                            {tabcommands} (tab) |
                            tab {n1-30} |
                            tab (number|minus|number minus) {n1-30} |
                            tab {n1-30} {tabcommands} |
                            tab (number|minus|number minus) {n1-30} {tabcommands} |
                            tab {tabcommands};
<moretabsclose> exported = {n2-20} tabs close;
<update> exported = (update|refresh) numbers;

#and the numbers grammar (0,...,999):                             
"""+numberGram
        
    def initialize(self):
        self.prevHandle = -1
        self.load(self.gramSpec)

    def gotBegin(self,moduleInfo):
        if not language: return
        winHandle = moduleInfo[2]
        if self.prevHandle == winHandle:
            return
        self.prevHandle = winHandle
        if natqh.matchModule('firefox', modInfo=moduleInfo):
            #print 'activate firefox %s mode'% mode
            if self.checkForChanges:
                print('firefox browsing (%s), checking the inifile'% self.name)
                self.checkInifile()

            self.switchOnOrOff()
        elif self.isActive():
            #print 'deactivate Firefox %s mode'% mode
            self.deactivateAll()

    #  Bij het initialiseren wordt de horizontale spatiejering uitgerekend.
    #    Er wordt van uitgegaan dat het venster niet te smal staat.
    def gotResultsInit(self,words,fullResults):
        """at start of actions"""
        # just in case a button was kept down (with show card commands)
        self.hadChoose = None
        self.chooseSpecification = ''
        self.number = ''

        
    def gotResults_getnumbers(self,words,fullResults):
        """works also if numbers already given, but cancels the loading of a page

        """
##        print 'getnumbers, doing: %s'% Escape + getNumbers
        if mode == 'hah':
            keystroke(Escape[mode])
        keystroke(getNumbers[mode])
        
    def gotResults_update(self,words,fullResults):
        """forces refresh of numbers on the page with MLB"""
        keystroke('{alt+=}')


    def gotResults_cancelnumbers(self,words,fullResults):
        """also stops loading the page when not finished"""
##        print 'cancel numbers, doing: %s'% Escape
        if mode == 'hah':
            keystroke(Escape[mode])
        else:
            keystroke(getNumbers[mode])

    def gotResults_navigatepages(self,words,fullResults):
        """go to next or previous page(s) and refresh possibly"""
##        print 'navigate pages: %s'% words
        
        dir = None
        command = self.getFromInifile(words, 'pagecommands',noWarning=1)
        
        if self.hasCommon(words, ['next', 'verder', 'volgende', 'vooruit', 'forward']):
            dir = 'right'
        elif self.hasCommon(words, ['previous', 'terug', 'vorige', 'back']):
            dir = 'left'
        else:
            print('no direction found in command: %s'% words)
        
        counts = self.getNumbersFromSpoken(words)
        if counts:
            count = counts[0]
        else:
            count = 1
##        print 'PAGES:     dir: %s, count: |%s|, command: |%s|'% (dir, counlinker balkt, command)
        if mode == 'hah':
            keystroke(Escape[mode])

        getNumbersAgain = 1
        if dir:        
            while count > 0:
                count= count -1
                keystroke('{alt+ext%s}'%(dir))
                natqh.Wait(0.5) #0.3 seem too short for going back pages in Firefox
        #elif count:
        #    print "Ctl + number doesnot work always!"
        #    keystroke('{ctrl+%s}'% count)
        #    natqh.Wait(0.3)
            
        if command:
            action(command)
        if command.lower().find('f5') > 0:
            # refresh action:
            getNumbersAgain = 1

        # only get new numbers if no refresh was asked for
        if getNumbersAgain and mode =="hah":
            natqh.Wait(waitBeforeNewNumbers)
            keystroke(getNumbers[mode])

    def gotResults_navigatetabs(self,words,fullResults):
        """switch to tabs in firefox

        goto numbered tab or to next|previous tab. optional command (refresh)
        """
##        print 'navigate tabs: %s'% words
        dir = None
        minus = None
        command = self.getFromInifile(words, 'tabcommands',noWarning=1)
        
        if self.hasCommon(words, ['next', 'verder', 'volgend','volgende']):
            dir = 'pgdn'
        elif self.hasCommon(words, ['previous', 'terug', 'vorig', 'vorige']):
            dir = 'pgup'
        elif self.hasCommon(words, ['minus', 'min']):
            minus = 1
            
        counts = self.getNumbersFromSpoken(words)
        if counts:
            count = counts[0]
        else:
            count = None
        #print 'TABS: dir: %s, count: |%s|, command: |%s|'% (dir, count, command)
        keystroke(Escape[mode])

        getNumbersAgain = 1
        if dir:        
            keystroke('{ctrl+ext%s %s}'%(dir, count or '1'))
            natqh.Wait(visiblePause)
        elif count:
            if mode == 'mlb':
                  if minus:
                      mbDonumber("01",'ctrl')
                      # need to wait:
                      natqh.Wait(visiblePause*2)
                      dir = 'pgup'
                      keystroke('{ctrl+ext%s %s}'%(dir, count or '1'))
                      natqh.Wait(visiblePause)
                  else:
##                      print 'go to tab: %s'% count
                      numberString = '%s%s'% (0,count)
                      mbDonumber(numberString,'ctrl')
            else:
                  if minus:
                      print('not implemented in hah')
                  else:
                      keystroke('{ctrl+%s}'% count)
        else:
            getNumbersAgain = 0
            
        if command:
            natqh.Wait(visiblePause*2)
            action(command)

        if command.lower().find('f5') > 0:
            # refresh action:
            getNumbersAgain = 0

        if getNumbersAgain and mode =="hah":
            natqh.Wait(waitBeforeNewNumbers)
            keystroke(getNumbers[mode])

    def gotResults_moretabsclose(self,words,fullResults):
        """close more tabs in one commands
        """
        n = self.getNumberFromSpoken(words[0])
        for i in range(n):
            keystroke("{ctrl+w}")

    def gotResults_choose(self,words,fullResults):
        w = words[0]
        #print 'choose words: %s'% words
        if not self.hadChoose:
            self.hadChoose = 1
            self.waitForNumber('number')
            
        if self.hasCommon(words, ['focus']):
            self.chooseSpecification = 'focus'
        if self.hasCommon(words, ['new', 'nieuw', 'new tab', 'nieuw tabblad']):
            self.chooseSpecification = 'new'
        if self.hasCommon(words, ['context menu', 'snelmenu']):
            self.chooseSpecification = 'context menu'

    def gotResults(self,words,fullResults):
    
        # step 5, in got results collect the number:
        # only necessary in this grammar for collecting the choose command
        if not self.hadChoose:
            return
        self.collectNumber()
        print('%s: dictated number: %s'% (self.name, self.number))
        
        if mode =="hah":
##            print 'hah go to number:',self.number
            keystroke("%s"% self.number)
            # natqh.Wait(visiblePause)
            keystroke(getNumbers[mode])
            print('firefox browsing with hah obsolete')
            return
            if self.hadChoose in ['focus']:
                pass
            elif not self.hadNew:
                keystroke("{enter}")
            elif self.hasCommon(self.hadNew,['tab', 'tabblad']):
                keystroke("{numpadd++}")
            elif self.hasCommon(self.hadNew, ['venster', 'window']):
                keystroke("{shift+enter}")
            elif self.hasCommon(self.hadNew, ['menu', 'snelmenu']): 
                keystroke("{shift+shift}")
                return
            elif self.hasCommon(self.hadNew,['new', 'nieuw']):
                keystroke("{numpadd++}")
                return
            else:
                print('unknown word in command: %s'% self.hadNew)
                keystroke("{enter}")

            natqh.Wait(waitBeforeNewNumbers)
            keystroke(getNumbers[mode])
            
        elif mode == "mlb":
            keystroke("{esc}")
            if self.chooseSpecification == 'new':
                #print 'firefox MLB: open in new tab'
                mbDonumber(self.number,'alt')
            elif self.chooseSpecification in ['focus', 'context menu']:
                #print 'firefox MLB: show focus'
                mbDonumber(self.number)
                keystroke("{shift}")
                if self.chooseSpecification == 'context menu':
                    keystroke("{shift+f10}")
            else:
                mbDonumber(self.number,'ctrl')

lookupdict = dict(enter=13)

def getKeyCode(k):
    """get the code of a key"""
    if k[0] == '{':
        return lookupdict[k[1:-1]]
    elif k in utilsqh.lowercase:
        return ord(k.upper())
    elif k in utilsqh.uppercase:
        return ord(k)
    elif k in utilsqh.digits:
        return 96 + int(k)

modifiers = { 
    'ctrl':  ((natut.wm_keydown, natut.vk_control, 1), (natut.wm_keyup, natut.vk_control, 1)),
    'shift':  ((natut.wm_keydown, natut.vk_shift, 1), (natut.wm_keyup, natut.vk_shift, 1)),
    'alt':  ((natut.wm_syskeydown, natut.vk_menu, 1), (natut.wm_syskeyup, natut.vk_menu, 1))}

    
##def mbDonumber(number, modifier=None):
##    if not number:
##        return
##    L = ['{ctrl+numkey%s}'%s for s in str(number)]
##    print 'L: %s'% L
##    for l in L:
##        natut.playString(l, natut.hook_f_systemkeys)
    
def mbDonumber(number, modifier=None):
    events = []
    if modifier:
        events.append (modifiers[modifier][0])
    for n in number:
        code = getKeyCode(n)
        events.append((natut.wm_keydown, code, 1))
        events.append((natut.wm_keyup, code, 1))
    if modifier:
        events.append (modifiers[modifier][1])
    try:
        natlink.playEvents(events)
    except natlink.NatError:
        print("==================")
        print("Error playing events in firefox browsing, doNumber: %s"% repr(events))
        

# standard stuff Joel (adapted for possible empty gramSpec, QH, unimacro)
thisGrammar = ThisGrammar()
if thisGrammar.gramSpec:
    thisGrammar.initialize()
else:
    thisGrammar = None
    
def unload():
    global thisGrammar
    if thisGrammar: thisGrammar.unload()
    thisGrammar = None
