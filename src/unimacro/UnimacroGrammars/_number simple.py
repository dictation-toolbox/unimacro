#
# (unimacro - natlink macro wrapper/extensions)
# _number.py 
#  written by: Quintijn Hoogenboom (QH softwaretraining & advies)
#  August 2003//April 2022 (python3)
#
"""smart and reliable number dictation

the number part of the grammar was initially provided by Joel Gould in
his grammar "winspch.py". It is changed quite a bit, but essentially
all sorts of numbers can be dictated with his grammar.

For real use copy the things from his grammar into another grammar. See
for example "_lines.py" and "firefox_browsing.py".

This grammar shows the simplest "number" rule. For more examples, see "_number extended.py".

WARNING: do not have them BOTH switched on ("_number simple.py" and "_number extended.py")

QH september 2013: rewriting of the functions, ruling out optional command words. The optional word "and" has been removed
            (now say "three hundred twenty" instead of "three hundred and twenty")

further comments in _number extended.py. Also see the page "number grammar" on the Unimacro we
"""
#pylint:disable=C0115, C0116, W0613
from dtactions.unimacro import unimacroutils
from dtactions.sendkeys import sendkeys as keystroke
import unimacro.natlinkutilsbj as natbj

ancestor = natbj.IniGrammar
class ThisGrammar(ancestor):

    language = unimacroutils.getLanguage()

    #Step 1, choose one of next three grammar rules:
    # the <integer> rule comes from these grammar rules
    number_rules = natbj.numberGrammarTill999[language] # hundreds, including a long string of digits
    #number_rules = natbj.numberGrammarTill999999[language] # including thousands
    #number_rules = natbj.numberGrammar[language] #  including millions
    # the rules <integer> and <float> are already defined.
    name = "number simple"

    gramSpec = """
<testnumber> exported = Number <number>;
<number> = <integer> | Minus <integer> | <float> | Minus <float>;
"""+number_rules+"""
    """
    def __init__(self):
        self.minus = False
        self.number = False
        super().__init__()
  
    def initialize(self):
        if not self.language:
            print("no valid language in grammar "+__name__+" grammar not initialized")
            return
        self.load(self.gramSpec)
        # if switching on fillInstanceVariables also fill numbers lists like {n1-9} or {number1to99}
        self.switchOnOrOff() 

    def gotResultsInit(self, words, fullResults):
        # Step 2:
        # you can initialise variables here, eg self.minus = None, self.number = ''. Not necessary, but
        # in some grammars more appropriate than in the next function.
        pass
        
    def gotResults_testnumber(self, words, fullResults):
        # step 3: specify the number you are waiting for
        # check if the word Minus is present, and then wait for the number named "number"
        # note in this example self.number is non existent until collectNumber has been visited.
        # self.minus will only be set if the rule number is visited.
        self.waitForNumber('number')
        self.minus = False 

    def gotResults_number(self, words, fullResults):
        # step 3a: when in this rule, the word Minus (or synonym or translation) has been spoken..
        self.minus = True
 
    def gotResults(self,words,fullResults):
        # step 4, in gotResults collect the number (as a string):
        self.collectNumber() # setting self.number, see self.waitForNumber above
        print('number from the _number simple grammar: %s'% self.number)
        if self.minus:
            self.number = '-' + self.number
        # disable when testing through unittestIniGrammar.py (in unimacro_test directory):
        self.outputNumber(self.number)
            
                      
    def outputNumber(self, number):
        #pylint:disable=R0201
        keystroke(number)
        #Step 5:
        # Here some extra postprocessing for different programs:
        prog = unimacroutils.getProgName()
        if prog in ['iexplore', 'firefox', 'chrome', 'safari']:
            keystroke('{tab}')
        elif prog in ['natspeak']:  # DragonPad
            keystroke('{enter}')
        elif prog in ['excel']:
            keystroke('{tab}')

# standard stuff Joel (adapted for possible empty gramSpec, QH, unimacro)
thisGrammar = ThisGrammar()
if thisGrammar.gramSpec:
    thisGrammar.initialize()
else:
    thisGrammar = None

def unload():
    #pylint:disable=W0603
    global thisGrammar
    if thisGrammar:
        thisGrammar.unload()
    thisGrammar = None 
