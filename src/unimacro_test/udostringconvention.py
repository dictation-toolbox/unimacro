#!/usr/bin/env python
import re

UdoMoves = re.compile(r'[A-Z]\d*')

UdoDict = dict(D='down', U='up', L='left', R='right')

def UdoToUnimacro(s):
    """convert D3 to {down 3} etc
    
>>> UdoToUnimacro('abcd3')
'abcd3'
>>> UdoToUnimacro('L1D3')
'{left}{down 3}'
>>> UdoToUnimacro('L3;;;U1;R123')
'{left 3};;;{up};{right 123}'
    
    """
    if UdoMoves.search(s):
        s = UdoMoves.sub(UdoSub, s)
    return s

def UdoSub(pat):
    """return substituted pattern of a part of the match
    
    """
    text = pat.group()
    if len(text) == 0:
        return text
    elif len(text) == 1:
        direction = text
        count = 1
    else:
        direction, count = text[0], int(text[1:])
    if direction in UdoDict:
        d = UdoDict[direction]
        if count == 1:
            return '{%s}'% d
        else:
            return '{%s %s}'% (d, count)
    return pat

def _test():
    import doctest
    return doctest.testmod()

if __name__ == "__main__":
    _test()
