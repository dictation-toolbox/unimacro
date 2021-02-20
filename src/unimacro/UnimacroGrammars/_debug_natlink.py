"""
Grammar to help with natlink hosted python debugging.
"""


import natlinkcore.natlink as natlink
import natlinkpydebug as pd
import unimacro.natlinkutilsqh as natqh as natqh
import natlinkcore.natlinkutils as natut as natut
import unimacro.natlinkutilsbj as natbj as natbj
# import gramparser as gp
from actions import doAction as action
import nsformat

ancestor = natbj.IniGrammar  #QH1

class DebugGrammar(ancestor):
    # language = natqh.getLanguage()
    name = "Natlink Debug"
    gramSpec = """
<debug> exported = debug <deb_cmd>;
<deb_cmd>   = <dap_info> | <dap_start> | <dap_break>;
<dap_info> exported = code Info;
<dap_start> exported = code Start;
<dap_break> exported = code Break;
##<dap_cmd>  = code <dap_arg>;  ## we use utterance "CODE"  instead of "DAP" 
                                      ##for DAP compatible debugggers DAP https://microsoft.github.io/debug-adapter-protocol/
                                      ##since Visual Studio Code is a commmon one and "Code" is an english word, DAP isn't.
##<dap_arg>  = Info | Start | Break;
"""
    # def __init__(self):n  ##QH2
    #     return print(f"debug __init__ ")
    #     ancestor.__init__(self,self.gramSpec,self.name)  ## should be ancestor.__init__(self) only. but not needed.
    
    def initialize(self):
        print(f"debug initialize, by loading self.gramSpec")
        self.load(self.gramSpec)
        self.switchOnOrOff()   ## based on the ini settings, by default, on
        


    def gotResults_dap_info(self, words, fullResults):
        print(f"DAP Info: {pd.dap_info()}")
    def gotResults_dap_start(self, words, fullResults):
        pd.start_dap()
        print(f"DAP Start: {pd.dap_info()}")
    def gotResults_dap_break(self, words, fullResults):
        pd.dap_breakpoint()
        print(f"DAP Break: {pd.dap_info()}")

    # def gotResults_dap_cmd(self, words, fullResults):
    #     print(f"debug gotResults_dap_cmd words: {words} fullResults {fullResults} ")
    #     dap_cmd=fullResults[2][0]
    #     if dap_cmd=="Start":
    #         pd.start_dap()
    #     if dap_cmd=="Info":
    #         print(f"DAP Info: {pd.dap_info()}")
    #     if dap_cmd == "Break":
    #         print(f"DAP Break: {pd.dap_info()}")
    #         pd.dap_breakpoint()



    def gotBegin(self,moduleInfo):
        pass

#this IS the way!
# standard stuff Joel (adapted for possible empty gramSpec, QH, unimacro)
debug_grammar = DebugGrammar()
if debug_grammar.gramSpec:
    print(f'debug_grammar initialize')
    debug_grammar.initialize()
else:
    print(f'debug_grammar not initialize, no gramSpec found')
    debug_grammar = None

def unload():
    global debug_grammar
    debug_grammar = None