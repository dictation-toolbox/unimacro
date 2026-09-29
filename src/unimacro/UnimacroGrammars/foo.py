from unimacro.natlinkutilsbj import grammar_log
from icecream import ic
 

class A:
    def __init__(self):
        self.a="A"
    
class B:
    def __init__(self):
        self.b="B"
    def c(self):
        pass
    

x=A()
y=B()

ic(hasattr(x,'a'))
ic(hasattr(y,'a'))
ic(hasattr(x,'b'))
ic(hasattr(y,'b'))
ic(B.__module__)
ic(y.__module__)
#ic(y.__name__)