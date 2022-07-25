"""


(unimacro - natlink macro wrapper/extensions)
see http://qh.antenna.nl/unimacro/aboutunimacro.html for copyright note
    
      
"""
from dtactions.unimacro import unimacroutils
from natlinkcore import natlinkutils
from dtactions.unimacro import unimacroactions as actions
import natlink
import unittest
import time
import types
import UnimacroTestHelpers

#special mods, the bring up you ask for produces and other module:
specialMods = {}
specialMods['edit'] = 'uedit32'
specialMods['dragonpad'] = 'natspeak'
specialMods['voicecode'] = 'emacs'


class BringupTest(UnimacroTestHelpers.UnimacroTestHelpers):
    """Testing the Bringup in 'actions.py'

    and the corresponding shorthand commands

    the different tests can be configured.  Notice "edit" is some
    edit program that does the normal editing of .txt and .ini files
    (in case QH it is uedit32 (ultraedit)). Can be configured
    through the actions.ini configuration file.

    Also tests the do_KW (kill window) function.    

    voicecode is special, starts emacs, looks for mediator, checks the user...

    cmd is the windows command prompt    
    
    """
    first = 1
    def setUp(self):
        if self.first:
            actions.debugActions(1)
            self.first = 0
        else:
            actions.debugActions(1, openMode='a')
        self.startUser = natlink.getCurrentUser()[0]

    def tearDown(self):
        endUser = natlink.getCurrentUser()[0]
        if self.startUser != endUser:
            print('reopen user: %s'% self.startUser)
            natlink.openUser(self.startUser)
        actions.debugActions(0)
        

    def test_Should_BringUp_DragonPad(self):

        actions.UnimacroBringUp("dragonpad")
        time.sleep(2)
        self.assert_mod_partoftitle('natspeak', 'DragonPad', " when bringing up DragonPad")
        natlinkutils.playString("this should last 2 seconds")
        time.sleep(2)
        actions.do_KW()

        
    def test_Bringup_list_of_small_applications(self):
        preserveApps = []  # other apps are killed after the test
        apps = ['notepad', 'dragonpad']   ## calc renamed in Windows 10
        self.doTestBringupApplications(apps, preserveApps)

    def test_Bringup_list_of_medium_applications(self):

        preserveApps = ['pythonwin', 'edit']  # other apps are killed after the test
        apps = ['notepad', 'pythonwin', 'dragonpad', 'edit', 'cmd']
        self.doTestBringupApplications(apps, preserveApps)

    def tttest_Bringup_list_of_emacs_applications(self):

        preserveApps = ['pythonwin']  # other apps are killed after the test
        apps = ['notepad', 'emacs', 'pythonwin']
        self.doTestBringupApplications(apps, preserveApps)

    def test_Bringup_list_of_office_applications(self):

        preserveApps = []  # other apps are killed after the test
        apps = ['notepad', 'winword', 'excel']
        self.doTestBringupApplications(apps, preserveApps)
        
    def tttest_Bringup_voicecode(self):

        preserveApps = ['emacs']  #ther adepps are killed after the test
        apps = ['calc', 'emacs', 'voicecode', 'notepad']
        self.doTestBringupApplications(apps, preserveApps)
    
    def tttest_Bringup_voicecode_user_switching(self):
    
        user, dummy = natlink.getCurrentUser()
        if user == 'VoiceCode':
            mes = ['active user is: %s'% user, '',
                   'Cannot test voicecode_user_switching to VoiceCode again', '', 
                   'Please start test with another user being active.']
            actions.Message(mes)
            self.fail("start test with a user profile NOT being VoiceCode")
            

        preserveApps = ['emacs']  #ther adepps are killed after the test
        apps = ['voicecode', 'notepad']
        if not self.doTestBringupApplications(apps, preserveApps, prompt="test_Bringup_voicecode_user_switching"):
            print('test_Bringup_voicecode_user_switching skipped halfway')
            return
        newUser, dummy = natlink.getCurrentUser()
        self.assert_equal('VoiceCode', newUser, "user name should be switched to 'VoiceCode'")
        if user == newUser:
            mes = ['cannot test voicecode user coming from another user',
                   'start test from another user as "VoiceCode"']
            actions.Message(mes)

        natlink.openUser(user)
        newUser, dummy = natlink.getCurrentUser()
        self.assert_equal(user, newUser, "user name should be switched to '%s'\n"
                          "in order to be able to test the user switching part of this test"% user)
        self.doTestBringupApplications(apps, preserveApps, prompt=0)
        newUser, dummy = natlink.getCurrentUser()
        self.assert_equal('VoiceCode', newUser, "user name should be switched to 'VoiceCode', also the second time of testing")


    def doTestBringupApplications(self, apps, preserveApps, prompt=1):
        """do the testing of bringing up and destroying applications

        switching is done several times, also after killing the window.
        switching with UnimacroBringUp several times is fast and comes back
        to the same window, if not killed in between.

        In these tests the different combinations are checked.        

        """
        destroyApps = [a for a in apps if a not in preserveApps]
        if prompt:
            mes = ["Do you want to do the Bringup applications tests?", "",
                   'using %s'%apps,
                   'keeping open: %s'% preserveApps,
                   'destroying after testing: %s'% destroyApps]
            if type(prompt) == bytes:
                mes.insert(0, prompt+'\n\n')
            result = actions.YesNo(mes, "Starting the Bringup applicationsTest ")
            if not result:
                print('Bringup applications test skipped')
                return

        appString = ', '.join(apps)

        # these should correspond with "name" in [bringup app] section of actions.ini
        # call for edit actions to inspect these:
        expectedMods = dict(list(zip(apps, apps)))
        expectedMods.update(specialMods)

        # bring them up:        
        for app in apps:
            result = actions.UnimacroBringUp(app)
            if result:
                self.assert_mod(expectedMods[app], " (round 1) when bringing up %s (%s)"%
                                (app, appString))
            else:
                self.fail(" (round 1) did not get result from switching to app: %s (%s)"%
                          (app, appString))
            
        # and do it again:
        for app in apps:
            result = actions.UnimacroBringUp(app)
            if result:
                self.assert_mod(expectedMods[app], " (round 2) when bringing up %s (%s)"%
                                (app, appString))
            else:
                self.fail(" (round 2) did not get result from switching to app: %s (%s)"%
                          (app, appString))

            result = actions.UnimacroBringUp(app)
            if result:
                self.assert_mod(expectedMods[app], " (round 2, double!) when bringing up %s (%s)"%
                                (app, appString))
            else:
                self.fail(" (round 2, double!) did not get result from switching to app: %s (%s)"%
                          (app, appString))
        # do it in reverse order, kill the window, except for pythonwin and uedit32 (preserveApps):
        apps.reverse()
        for app in apps:
            result = actions.UnimacroBringUp(app)
            if result:
                self.assert_mod(expectedMods[app], " (round 3) when bringing up %s (%s)"%
                                (app, appString))
            else:
                self.fail(" (round 3, revers order) did not get result from switching to app: %s (%s)"%
                          (app, appString))
            if app not in preserveApps:
                actions.do_KW()
                self.failIf_mod(app, "(round 3) kill window did not succeed for app\n\n"
                                "(THIS MAY BE A TEST ARTEFACT OR A FAILURE OF THE KW (KillWindow) ACTION: %s (%s)"%
                                (app,appString))
                
        # again reverse order, bringup again and kill the window, except for pythonwin and uedit32:
        for app in apps:
            result = actions.UnimacroBringUp(app)
            if result:
                self.assert_mod(expectedMods[app], " (round 4, after killing previous app)) when bringing up %s (%s)"%
                                (app, appString))
            else:
                self.fail(" (round 4, after killing previous app)) did not get result from switching to app: %s (%s)"%
                          (app, appString))
            if app not in preserveApps:
                actions.do_KW()
                self.failIf_mod(app, "(round 4, after killing previous app)) kill window did not succeed for app: %s (%s)"%
                                (app,appString))
        return 1
# no main statement, run from command in _unimacrotest.py.