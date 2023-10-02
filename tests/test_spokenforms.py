#
#
# tested with test_spokenforms.py in tests directory of
# unimacro (pytest)
# testing the Unimacro mechanism to switch back and forth
# with numbers to spoken forms
# see spokenforms.py in the Unimacro directory
#pylint:disable=C0209, R0904
import pytest

from unimacro import spokenforms
from dtactions.unimacro import inivars

expected_n2s =    {0: ['oh', 'zero'],
 1: ['on\xe9'],
 2: ['two', 'too'],
 3: ['three'],
 4: ['four', 'for'],
 5: ['five'],
 6: ['six'],
 7: ['seven'],
 8: ['eight'],
 9: ['nine'],
 10: ['ten'],
 11: ['eleven'],
 12: ['twelve'],
 13: ['thirteen'],
 14: ['fourteen'],
 15: ['fifteen'],
 16: ['sixteen'],
 17: ['seventeen'],
 18: ['eighteen'],
 19: ['nineteen'],
 20: ['twenty'],
 21: ['twenty-one'],
 22: ['twenty-two'],
 23: ['twenty-three'],
 24: ['twenty-four'],
 25: ['twenty-five'],
 26: ['twenty-six'],
 27: ['twenty-seven'],
 28: ['twenty-eight'],
 29: ['twenty-nine'],
 30: ['thirty'],
 31: ['thirty-one'],
 32: ['thirty-two'],
 33: ['thirty-three'],
 34: ['thirty-four'],
 35: ['thirty-five'],
 36: ['thirty-six'],
 37: ['thirty-seven'],
 38: ['thirty-eight'],
 39: ['thirty-nine'],
 40: ['forty'],
 41: ['forty-one'],
 42: ['forty-two'],
 43: ['forty-three'],
 44: ['forty-four'],
 45: ['forty-five'],
 46: ['forty-six'],
 47: ['forty-seven'],
 48: ['forty-eight'],
 49: ['forty-nine'],
 50: ['fifty'],
 51: ['fifty-one'],
 52: ['fifty-two'],
 53: ['fifty-three'],
 54: ['fifty-four'],
 55: ['fifty-five'],
 56: ['fifty-six'],
 57: ['fifty-seven'],
 58: ['fifty-eight'],
 59: ['fifty-nine'],
 60: ['sixty'],
 61: ['sixty-one'],
 62: ['sixty-two'],
 63: ['sixty-three'],
 64: ['sixty-four'],
 65: ['sixty-five'],
 66: ['sixty-six'],
 67: ['sixty-seven'],
 68: ['sixty-eight'],
 69: ['sixty-nine'],
 70: ['seventy'],
 71: ['seventy-one'],
 72: ['seventy-two'],
 73: ['seventy-three'],
 74: ['seventy-four'],
 75: ['seventy-five'],
 76: ['seventy-six'],
 77: ['seventy-seven'],
 78: ['seventy-eight'],
 79: ['seventy-nine'],
 80: ['eighty'],
 81: ['eighty-one'],
 82: ['eighty-two'],
 83: ['eighty-three'],
 84: ['eighty-four'],
 85: ['eighty-five'],
 86: ['eighty-six'],
 87: ['eighty-seven'],
 88: ['eighty-eight'],
 89: ['eighty-nine'],
 90: ['ninety'],
 91: ['ninety-one'],
 92: ['ninety-two'],
 93: ['ninety-three'],
 94: ['ninety-four'],
 95: ['ninety-five'],
 96: ['ninety-six'],
 97: ['ninety-seven'],
 98: ['ninety-eight'],
 99: ['ninety-nine'],
 100: ['hundred', 'one hundred'],
 1000: ['thousand', 'one thousand'],
 10000: ['ten thousand'],
 100000: ['hundredthousand'],
 1000000: ['million', 'one million']}

expected_s2n =  {'eight': 8,
 'eighteen': 18,
 'eighty': 80,
 'eighty-eight': 88,
 'eighty-five': 85,
 'eighty-four': 84,
 'eighty-nine': 89,
 'eighty-one': 81,
 'eighty-seven': 87,
 'eighty-six': 86,
 'eighty-three': 83,
 'eighty-two': 82,
 'eleven': 11,
 'fifteen': 15,
 'fifty': 50,
 'fifty-eight': 58,
 'fifty-five': 55,
 'fifty-four': 54,
 'fifty-nine': 59,
 'fifty-one': 51,
 'fifty-seven': 57,
 'fifty-six': 56,
 'fifty-three': 53,
 'fifty-two': 52,
 'five': 5,
 'for': 4,
 'forty': 40,
 'forty-eight': 48,
 'forty-five': 45,
 'forty-four': 44,
 'forty-nine': 49,
 'forty-one': 41,
 'forty-seven': 47,
 'forty-six': 46,
 'forty-three': 43,
 'forty-two': 42,
 'four': 4,
 'fourteen': 14,
 'hundred': 100,
 'hundredthousand': 100000,
 'million': 1000000,
 'nine': 9,
 'nineteen': 19,
 'ninety': 90,
 'ninety-eight': 98,
 'ninety-five': 95,
 'ninety-four': 94,
 'ninety-nine': 99,
 'ninety-one': 91,
 'ninety-seven': 97,
 'ninety-six': 96,
 'ninety-three': 93,
 'ninety-two': 92,
 'oh': 0,
 'on\xe9': 1,
 'one hundred': 100,
 'one million': 1000000,
 'one thousand': 1000,
 'seven': 7,
 'seventeen': 17,
 'seventy': 70,
 'seventy-eight': 78,
 'seventy-five': 75,
 'seventy-four': 74,
 'seventy-nine': 79,
 'seventy-one': 71,
 'seventy-seven': 77,
 'seventy-six': 76,
 'seventy-three': 73,
 'seventy-two': 72,
 'six': 6,
 'sixteen': 16,
 'sixty': 60,
 'sixty-eight': 68,
 'sixty-five': 65,
 'sixty-four': 64,
 'sixty-nine': 69,
 'sixty-one': 61,
 'sixty-seven': 67,
 'sixty-six': 66,
 'sixty-three': 63,
 'sixty-two': 62,
 'ten': 10,
 'ten thousand': 10000,
 'thirteen': 13,
 'thirty': 30,
 'thirty-eight': 38,
 'thirty-five': 35,
 'thirty-four': 34,
 'thirty-nine': 39,
 'thirty-one': 31,
 'thirty-seven': 37,
 'thirty-six': 36,
 'thirty-three': 33,
 'thirty-two': 32,
 'thousand': 1000,
 'three': 3,
 'too': 2,
 'twelve': 12,
 'twenty': 20,
 'twenty-eight': 28,
 'twenty-five': 25,
 'twenty-four': 24,
 'twenty-nine': 29,
 'twenty-one': 21,
 'twenty-seven': 27,
 'twenty-six': 26,
 'twenty-three': 23,
 'twenty-two': 22,
 'two': 2,
 'zero': 0}


expected_spoken2char = {'Alpha': 'a', 'Bravo': 'b', 'Charlie': 'c', 'Delta': 'd', 'Echo': 'e'}

expected_char2spoken =   {'a': ['Alpha'],
                            'b': ['Bravo'],
                            'c': ['Charlie'],
                            'd': ['Delta'],
                            'e': ['Echo']}

expected_abbrev2spoken =  {'enx': ['E N X', 'enx'], 'fra': ['F R A'], 'nld': ['N L D'], 'qh': ['Q H']}

expected_spoken2abbrev =    {'E N X': 'enx', 'F R A': 'fra', 'Q H': 'qh', 'N L D': 'nld', 'enx': 'enx'}

expected_spoken2ext =     {'I N I': ['ini'],
                                'P why': ['py'],
                                'P why W': ['pyw'],
                                'X L S': ['xls'],
                                'X L S X': ['xlsx'],
                                'doc': ['doc'],
                                'doc X': ['docx'],
                                'excel': ['xls', 'xlsx'],
                                'python': ['py', 'pyw'],
                                'word': ['doc', 'docx']}


expected_ext2spoken =     {'doc': ['word', 'doc'],
                                'docx': ['word', 'doc X'],
                                'ini': ['I N I'],
                                'py': ['python', 'P why'],
                                'pyw': ['python', 'P why W'],
                                'xls': ['excel', 'X L S'],
                                'xlsx': ['excel', 'X L S X']}

expected_spoken2punct =     {'colon': ':', 'exclamation mark': '!', 'point': '.', 'semi colon': ';'}

expected_punct2spoken =     {'!': ['exclamation mark'],
                            '.': ['point'],
                            ':': ['colon'],
                            ';': ['semi colon']}

def test_basic_dicts(unimacro_setup):
    """try to convert tests from unittest to pytest
    """
    spokenforms.resetSpokenformsGlobals()
    numbers = spokenforms.SpokenForms('test')
    
    assert expected_s2n ==  numbers.s2n
#         assert expected_n2s, numbers.n2s, "numbers, numbers2spoken is not as expected")

        # alphabet:
    assert expected_char2spoken == numbers.char2spoken
    assert expected_spoken2char == numbers.spoken2char

        # abbrevs:
    assert expected_abbrev2spoken == numbers.abbrev2spoken
    assert expected_spoken2abbrev == numbers.spoken2abbrev

        # extensions:
    assert expected_ext2spoken == numbers.ext2spoken
    assert expected_spoken2ext == numbers.spoken2ext
        
        # punctuation:
    assert expected_punct2spoken == numbers.punct2spoken
    assert expected_spoken2punct == numbers.spoken2punct
        
        # next instance:
    second_instance = spokenforms.SpokenForms('test')
    assert expected_s2n == second_instance.s2n
        

def test_make_mixed_list(unimacro_setup):
    spokenforms.resetSpokenformsGlobals()
    numbers = spokenforms.SpokenForms('test')

    L = [1, 2, 4, 5, 6]
    got = numbers.getMixedList(L)
    expected =     ['on\xe9', 'two', 'too', 'four', 'for', 'five', 'six']
    assert expected == numbers.getMixedList(L)

    # non existing language:        
    print('\nexpect messages from spokenforms.ini, as language is unknown')
    m = spokenforms.SpokenForms('othertest')

    got = numbers.getMixedList(L)
    expected =    ['1', '2', '4', '5', '6']
    assert expected == m.getMixedList(L)

    # back to previous:
    numbers = spokenforms.SpokenForms('test')
    expected = ['on\xe9', 'two', 'too', 'four', 'for', 'five', 'six']

    assert expected == numbers.getMixedList(L)
    print('----end of these expected messages')


def test_get_number_back_from_spoken_form(unimacro_setup):
    """the reverse process, occurring after a recognition
    """
    spokenforms.resetSpokenformsGlobals()
    numbers = spokenforms.SpokenForms('test')

    expected = 1
    input = 'on\xe9'
    assert expected == numbers.getNumberFromSpoken(input)
    
    expected = 5
    assert expected == numbers.getNumberFromSpoken(5)

    # with original list:
    originalList = [1, 2, 5, 6, 7]
    expected = None
    assert expected == numbers.getNumberFromSpoken('foo', originalList)

    expected = 7
    assert expected == numbers.getNumberFromSpoken('7', originalList)

    expected = None   ## 8 not in originalList
    assert expected == numbers.getNumberFromSpoken('8', originalList)

    expected = 2
    assert expected == numbers.getNumberFromSpoken('2', originalList)

    expected = 2
    assert expected == numbers.getNumberFromSpoken('too', originalList)
    
    # real check! in instance, but not in originalList:
    expected = None
    assert expected == numbers.getNumberFromSpoken('four', originalList)
    
    # originalList ints:
    originalList = [0,1,2]
    expected = None
    input = 'four'
    assert expected == numbers.getNumberFromSpoken(input, originalList)
    expected = 1
    
    input = 'on\xe9'
    assert expected == numbers.getNumberFromSpoken(input, originalList)
    expected = 1
    assert expected == numbers.getNumberFromSpoken(1, originalList)
    expected = None
    assert expected == numbers.getNumberFromSpoken(10, originalList)

         
def test_get_list_of_spoken_forms_larger_number(unimacro_setup):
    """construct a list of spoken forms for numbers up to 10000
    """
    spokenforms.resetSpokenformsGlobals()
    numbers = spokenforms.SpokenForms('test')
    func = numbers.generateSpokenFormsFromNumber

    assert func(123) == ['hundred twenty-three', 'on\xe9 twenty-three']
    assert func(203) == ['two oh three', 'too oh three', 'two hundred three', 'too hundred three']
    assert func(300) == ['three hundred']
    assert func(301) == ['three oh on\xe9', 'three hundred on\xe9']
    assert func(323) == ['three hundred twenty-three', 'three twenty-three']
    #assert func(1000) == ['one thousand'])  # should not go through this function
    assert func(1003) == ['on\xe9 oh oh three', 'thousand three', 'one thousand three']
    assert func(1011) == ['thousand eleven', 'one thousand eleven', 'ten eleven']
    assert func(2303) == ['twenty-three oh three']
    assert func(2003) == ['two oh oh three',
                        'too oh oh three',
                        'two thousand three',
                        'too thousand three']
    assert func(2010) == ['two thousand ten', 'too thousand ten', 'twenty ten']
    assert func(2310) == ['twenty-three ten']



    
# def doTestDictOfSpokenForms(self, List, ExpDict):
#     """test the automatic generation of a dict of spoken forms for given values list
#     """
#     func = self.numbers.getDictOfMixedSpokenForms
#     result = func(List)
#     assert ExpDict, result, "test getDictOfMixedSpokenForms test failed for List: %s"% List)
    

def test_get_mixed_list_of_spoken_forms_abbrevs(unimacro_setup):
    """construct a list of spoken forms from filenames etc

    very complicated function, hopefully works now (QH 2023-10-02)
   
    """
    spokenforms.resetSpokenformsGlobals()
    numbers = spokenforms.SpokenForms('test')
    func = numbers.generateMixedListOfSpokenForms
    assert func("QH Company") == ["Q H Company"]
    assert func("Unimacro_qh") == ["Unimacro Q H"]
    
    assert func("Foto's") == ["Fotoos"]
    assert func("Foto's le\u0301rlingenavond Pau") == ["Fotoos l\xe9rlingenavond Pau"]
    assert func('file fra 100') == ['file F R A hundred', 'file F R A one hundred']
    assert func('file enx') == ['file E N X', 'file enx']
    assert func('file enx 100') == ['file E N X hundred', 'file E N X one hundred',
                              'file enx hundred', 'file enx one hundred']

def test_get_mixed_list_of_spoken_forms_skip_numbers(unimacro_setup):
    """construct a list of spoken forms from filenames etc with skipping numbers
    
    
    1_hello should skip the 1 and also include
    testing (2) should skip the (2) (AND also include)
    """
    spokenforms.resetSpokenformsGlobals()
    numbers = spokenforms.SpokenForms('test')
    func = numbers.generateMixedListOfSpokenForms
    assert func('1_file.txt') == ['file txt', 'oné file txt']
    assert func('2_dir') == ['dir', 'two dir', 'too dir']
    
    assert func('directory avp (3)') == ['directory avp', 'directory avp three']
    assert func('file (4).doc') ==  ['file four doc', 'file for doc']




def test_get_mixed_list_of_spoken_forms_skip_start_letters(unimacro_setup):
    """construct a list of spoken forms from filenames etc with skipping start letters
    
    a_test should be a test and test
    b_file.txt should be b file txt and file txt
    """
    spokenforms.resetSpokenformsGlobals()
    numbers = spokenforms.SpokenForms('test')
    func = numbers.generateMixedListOfSpokenForms

    assert func('a_test directory') == ['test directory', 'a test directory']
    assert func('b_file.txt') == ['file txt', 'b file txt']

    assert func('az_test directory') == ['test directory', 'az test directory']
    assert func('bb_file.txt') == ['file txt', 'bb file txt']
    
    # but:
    
    assert func('this_file.txt') == ['this file txt']
#         
# 
def test_get_dict_of_spoken_forms(unimacro_setup):
    """construct a dict of spoken forms from a list of values (sheets in excel)
    """
    spokenforms.resetSpokenformsGlobals()
    numbers = spokenforms.SpokenForms('test')
    func = numbers.getDictOfMixedSpokenForms
    
    assert func(['Sheet1', 'Sheet2']) == {'Sheet on\xe9': 'Sheet1', 'Sheet too': 'Sheet2', 'Sheet two': 'Sheet2'}

def test_get_list_of_spoken_forms_sorted_by_number_values(unimacro_setup):
    """list of spoken forms, check numbers behind the items and sort by numbers
    """
    spokenforms.resetSpokenformsGlobals()
    numbers = spokenforms.SpokenForms('test')
    func = numbers.sortedByNumbersValues
    assert func(['on\xe9', 'two', 'unknown word']) is None
    assert func(['on\xe9', 'two', 'three']) ==  ['oné', 'two', 'three']
    assert func(['on\xe9', 'two', 'three'], valueSpokenDict=1) == {1: ['on\xe9'], 2: ['two'], 3: ['three']}

    
def test_format_spoken_forms_from_numbers_dict(unimacro_setup):
    """
    """
    func = inivars.formatReverseNumbersDict
    assert func({1: ['on\xe9'], 2: ['two'], 3: ['three']}) == 'on\xe9 ... three'

def test_get_punctuation_list(unimacro_setup):
    """test the punctuation from the punctuationreverse section
    """
    spokenforms.resetSpokenformsGlobals()
    numbers = spokenforms.SpokenForms('test')
    func = numbers.getPunctuationFromSpoken

    # ok, 'colon' returns ':'
    assert func('colon') == ":"

    # not in the list:
    assert func('comma') is None  # 'comma' is not in the list in hte test_spokenforms.ini


    # with the originalList given:
    assert func('colon', originalList=[':', '.']) == ":"
    assert func('colon', originalList=':.') == ":"
    assert func('colon', originalList='.') is None
    assert func('colon', originalList='') == ":"
    assert func('colon', originalList=None) == ":"

    
def run():
    # print('starting UnittestNumbersSpokenForms')
    # unittest.main()
    pytest.main(['test_spokenforms.py'])      

if __name__ == "__main__":
    run()
