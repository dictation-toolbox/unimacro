"""


(unimacro - natlink macro wrapper/extensions)
see http://qh.antenna.nl/unimacro/aboutunimacro.html for copyright note
    
      
"""
from dtactions.unimacro import unimacroutils
from natlinkcore import natlinkutils
from dtactions.unimacro import unimacroactions as actions
action = actions.doAction

import unittest
import UnimacroTestHelpers

class MessageTest(UnimacroTestHelpers.UnimacroTestHelpers):
    """Testing the Message and YesNo functions in 'actions.py'

    and the corresponding shorthand commands
    """    
    def setUp(self):
        pass


    def test_Should_handle_embedded_quotes_and_newlines(self):
        mes = 'Do you want to do the "handle_embedded_quotes_and_newlines" test?'
        result = actions.YesNo(mes, 'Starting the handle_embedded_quotes_and_newlines Test')
        if not result:
            print('handle_embedded_quotes_and_newlines (MessageTest) skipped')
            return
        mes1 = 'This has embedded newlines: \n and \\r characters: \r in it:\n' \
              'and embedded quotes: " and \'\n\n\n' \
              'Please answer OK'
        mes2 = 'This has embedded newlines: \n and \\r characters: \r in it:\n' \
              'and embedded quotes: " and \'\n\n\n' \
              'Please answer Yes if there are embedded newlines and quotes in this Dialog and in previous one'
        result = actions.Message(mes1, "\"'\n\rhandle_embedded_quotes_and_newlines (MessageTest)")
        result = actions.YesNo(mes2, "\"\"'\"\r\nhandle_embedded_quotes_and_newlines (MessageTest)")
        self.assertEqual(True, result, "you answered NO to test: %s"% self.squeeze_whitespace(mes2))

        
        

    def test_Should_give_a_message(self):
        mes = "Do you want to do the Message Box tests?"
        result = actions.YesNo(mes, "Starting the MessageTest (Message Box)")
        if not result:
            print('Message Box tests (MessageTest) skipped')
            return

##        for alert,icon in enumerate([16, 32, 48, 64]):
##            mes = '''This is a test message with\n\n\ticon=%s and\n
##                  \talert=%s\n\nplease answer "OK"'''% (icon, alert)
##            actions.Message(mes, "MessageTest", icon=icon, alert=alert)

        actions.Message('This is a the default test message\n\nPlease answer "OK"', "MessageTest")


        for alert, icon in enumerate(['information', 'warning', 'critical']):
            if alert:
                mes = '''This is a test message
                         \nicon=%s and
                         \nalert (number of bells ringing)=%s
                         \nPlease answer "OK"'''%(icon, alert)
            else:
                mes = '''This is a test message
                         \n\ticon=%s and
                         \n\tno alert (sound heard)
                         \nPlease answer "OK"'''%icon
            actions.Message(mes, "MessageTest", icon=icon, alert=alert)
        mes = '''Where all of the previous messages correct,
                 \nespecially the icons and the number of alerts?
              '''
        result = actions.YesNo(mes, "Evaluation of MessageTest", icon=icon, alert=alert)
        self.assertEqual(True, result, "you answered NO to test: %s"% self.squeeze_whitespace(mes))
    


    def test_Should_give_a_YesNo_box(self):

        mes = "Do you want to do the YesNo Box tests?"
        result = actions.YesNo(mes, "Starting the MessageTest (YesNo Box)")
        if not result:
            print('YesNo Box tests (MessageTest) skipped')
            return

        res = actions.YesNo('Please answer "Yes"', "MessageTest")
        self.assertTrue(res, "Result should be True when you really answered *Yes*")
        res = actions.YesNo("Please answer\n'No'", "MessageTest")
        self.assertFalse(res, "Result should be False when you really answered *No*")
        for alert, icon in enumerate(['query', 'warning', 'critical']):
            if alert:
                mes = '''This is a test question\n\nicon=%s and
                      \nalert(number of bells ringing)=%s\n\nIs this OK?'''%(icon, alert)
            else:
                mes = '''This is a test question\n\n\ticon=%s and
                      \n\tno alert (sound heard)\n\nIs this OK?'''%icon
            print('alerts: ', alert)
            result = actions.YesNo(mes, "MessageTest", icon=icon, alert=alert)
            self.assertEqual(True, result, "you answered NO to test: %s"% self.squeeze_whitespace(mes))


if __name__ == "__main__":
    unittest.main(verbose=1)
