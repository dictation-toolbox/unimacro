
################################################################################
# IIPyhonUtils
#
# A library of Python utility classes developped by the
# Interactive Information Group of the Institute for Information Technology
# at the National Research Council of Canada (NRC).
#
#
# (c) National Research Council of Canada, 2000
# taken for unimacro/natlink tests by Quintijn Hoogenboom march
# adapt for Python2/Python3 integration. Quintijn april 2018
################################################################################
import os
import re
import types
import unittest
from pprint import pformat
import filecmp
import itertools
from natlinkcore import readwritefile

class AssertStringEqualsFailed(AssertionError):
    def __init__(self, exp_string, got_string, first_diff, orig_message):
        self.exp_string = exp_string
        self.got_string = got_string
        self.first_diff = first_diff
        self.orig_message = orig_message

    def __str__(self):
        if (self.first_diff < 0):
            format = "%s\nOne string was empty but not the other.\n" + \
                     "   Expected: \n%s\n" + \
                     "   Got: \n%s\n"
            message = format % (self.orig_message, repr(self.exp_string), repr(self.got_string))
        else:
            exp_with_tilde = self.exp_string[:self.first_diff] + '~~~' + self.exp_string[self.first_diff:]
            got_with_tilde = self.got_string[:self.first_diff] + '~~~' + self.got_string[self.first_diff:]
            format = "%s\n----\nStrings differed. See triple tilde (~~~) position below.\n" + \
                      "Expected:\n" + \
                      "   '%s'\n" + \
                      "Got:\n" + \
                      "   '%s'\n"
            message = format % (self.orig_message, repr(exp_with_tilde), repr(got_with_tilde))
        return message

class TestCaseWithHelpers(unittest.TestCase):
    """A subclass of pyUnit TestCase, that has helper method to
    facilitate unit testing.
    """

    def __init__(self, name):
        unittest.TestCase.__init__(self, name)

    def remind_me_to_implement_this_test(self):
        self.fail("DON'T FORGET TO IMPLEMENT THIS TEST!!!")

    def assert_equal(self, expected, got, mess="", epsilon=0):

        try:
            self.assert_equal_dispatch_according_to_type(expected, got, mess, epsilon)
        except RuntimeError as err:
            err = self.check_for_infinite_recursion_error(err)
            raise err

    def assert_equal_dispatch_according_to_type(self, expected, got, mess, epsilon):
        self.assertTrue(self.isnumber(epsilon), "assert_equal called with a value of epsilon that was not a number. Type of epsilon was: %s, value was %s" % (self.what_class(epsilon), epsilon))
        class_exp, class_got = self.what_class(expected), self.what_class(got)
        if class_exp != class_got:
            if self.isnumber(expected) and self.isnumber(got):
                pass
            elif self.isstringlike(expected) and self.isstringlike(got):
                pass
                # print('got PY2 str, expected unicode: %s'% got)
            else:
                mess = mess + "\n----\nThe two objects were not of same type"
                mess = mess + "\nExpected type: %s, Got type:  %s" % (type(expected), type(got))
                mess = mess + "\nExpected:\n   %s\nGot:\n   %s" % (expected, got)

                self.fail(mess)
        if type(expected) is None and type(got) is None:
            return

        if (self.issequence(expected)):
            self.assert_equal_sequence(expected, got, mess, epsilon)
        elif (self.isset(expected)):
            self.assert_equal_set(expected, got, mess, epsilon)
        elif (self.isdictionary(expected)):
            self.assert_equal_dictionary(expected, got, mess, epsilon)
        elif (self.isnumber(expected)):
            mess = mess + "\n----\nThe two numbers differed significantly."
            mess = mess + "\nExpected:\n   %s\nGot:\n   %s" % (expected, got)
            if epsilon == 0:
                self.assertTrue(expected == got, mess)
            else:
                self.assertTrue((got <= expected + epsilon) and (got >= expected - epsilon),
                         mess + "\nValue was not within epsilon=%s range of expected value." % epsilon)
        elif (self.isstring(expected)):
            self.assert_equal_string(expected, got, mess)
        elif (self.isbasetype(expected)):
            self.assertTrue(expected == got, mess)
        else:
            self.assert_equal_objects(expected, got, mess, epsilon)


    def assert_equal_string(self, exp_string, got_string, message=''):
        if self.isbinary(got_string):
            mess = "WARNING, got binary string expectied str, %s "% got_string
            got_string = str(got_string)
        first_diff = self.find_first_diff_char(got_string, exp_string)

        if first_diff != None:
            raise AssertStringEqualsFailed(exp_string, got_string, first_diff, message)

    def assert_equal_sequence(self, expected, got, mess="", epsilon=0):
        mess = mess + "\n----\nThe two sequences differred\nExpected sequence:\n   %s\nGot sequence:\n   %s" % \
               (pformat(expected), pformat(got))

        if len(expected) != len(got):
            mess = mess + "\nlengths differ, len(expected): %s, len(got): %s"% (len(expected), len(got))
            if len(expected) > len(got):
                mess = mess + "\nextra in expected: %s"% expected[len(got):]
            else:
                mess = mess + "\nextra in got: %s"% got[len(expected):]
        self.assert_equal(len(expected), len(got), mess + "\nThe two sequences did not have the same length.")


        for ii in range(len(expected)):
            mess_ii = mess + "\nThe two sequences differed at element ii=%s." % (ii)
            self.assert_equal(expected[ii], got[ii], mess_ii, epsilon)

    def assert_equal_set(self, expected, got, mess="", epsilon=0):
        mess = mess + "\n----\nThe two sets differ\nExpected sequence:\n   %s\nGot sequence:\n   %s" % \
               (pformat(expected), pformat(got))
        union = expected & got
        restexpected = expected - union
        restgot = got - union

        if union != expected:
            mess = mess + "\nonly in expected: %s"% restexpected
        if union != got:
            mess = mess + "\nonly in got: %s"% restgot
        self.assertEqual(expected, got, mess)


    def assert_equal_dictionary(self, expected, got, mess="", epsilon=0):
        expected_keys = set(expected.keys())
        got_keys = set(got.keys())
        # expected_keys = sorted(expected.keys())
        # got_keys = sorted(got.keys())

        mess = mess + "\n----\nThe two dictionaries differed"
        mess = mess + "\nExpected:\n   %s\nGot:\n   %s" % (pformat(expected), pformat(got))

        # NOTE: Keys must be exactly equal, even if epsilon is greater than 0.
        self.assert_equal(expected_keys, got_keys,
                              mess + "\nDictionaries did not have the same list of keys.")
        for a_key in expected_keys:
            self.assert_equal(expected[a_key], got[a_key],
                    mess + "\nValues of dictionaries differed at key '%s'" % a_key,
                    epsilon)


    def assert_equal_objects(self, expected, got, mess, epsilon=0):
        self.assert_equal(self.what_class(expected), self.what_class(got),
                           mess + "\n----\nThe two objects were not of the same class or type.")
        
        result = expected == got
        self.assert_equal(True, result,
                           mess + "\n----\nObjects differ"
                                + "\nExpected:\n   %s\nGot:\n   %s" % (repr(expected), repr(got)))

    def check_for_infinite_recursion_error(self, err):
        if (isinstance(err, RuntimeError) and
            err.args == ('maximum recursion depth exceeded', )):
            err.args = \
               ("maximum recursion depth exceeded.\n" + \
                "Error happened while doing an assert_equal().\n" + \
                "Maybe one of the arguments of assert_equal() has an infinite loop in its composition structure?",
                )
        return err

    def assert_not_equal(self, not_expected, got, mess):
        if got == not_expected:
            mess = mess + "\nValues were equal when they should not have been. Got: %s" % got
            self.fail(mess)

    def assert_string_contains(self, pattern, the_string, mess=''):
        self.assertTrue(the_string.find(pattern) != -1,
                     mess + "\nSubstring: '%s' was not found in string: '%s'" % (pattern, the_string))

    def assert_sequences_have_same_length(self, expected, got, mess):
        display_both_lists_mess = \
           "\nExpected list:\n   %s\nGot list:\n   %s" % (pformat(expected), pformat(got))

        if len(expected) != len(got):
            self.fail(mess + "\nExpeted sequence of length %s, but got sequence of length %s"
                      % (len(expected), len(got)) + \
                      display_both_lists_mess)

    def assert_equal_files(self, expected_file, actual_file, mess):
        """check contents of both files, to be equal

        a small issue (class=copyright) is in here because of the WhatCanISayTest files...

        """
        trunk, ext = os.path.splitext(str(expected_file))
        if ext in [".html", ".htm", ".txt", ".js", ".css", ".ini", ".log"]:
            encodingexp, bomexp, contentexp = readwritefile.readAnything(expected_file)
            encodinggot, bomgot, contentgot = readwritefile.readAnything(actual_file)
            if encodinggot != encodingexp:
                print("warning: different encoding found\n---exp: %s: %s\n+++got: %s: %s"%
                                  (expected_file, encodingexp, actual_file, encodinggot))
            if bomgot != bomexp:
                print("warning: different bom found\n---exp: %s: %s\n+++got: %s: %s"%
                                  (expected_file, bomexp, actual_file, bomgot))
            # 
            # 
            # with open(expected_file) as k:
            #     with open(actual_file) as l:
            gotlines = contentgot.split('\n')
            explines = contentexp.split('\n')
            for i, (kline, lline) in enumerate(zip(gotlines, explines)):
                if ext in [".html", ".htm"] and \
                        kline.find('class="copyright"') >= 0 and \
                        lline.find('class="copyright"') >= 0:
                    continue
                self.assert_equal(kline, lline, mess + '\nthe two files------------\n%s\nand\n %s should have been equal\nThey differ in line %s'%
                            (expected_file, actual_file, i+1))
        else:
            if not filecmp.cmp(expected_file, actual_file):
                message = mess + '\nthe two files------------\n%s\nand\n%s should have been equal\n--- comparison with filecmp.cmp ---'% \
                                    (expected_file, actual_file)
            self.fail(message)

    def assert_dicts_have_same_keys(self, expected_dict, got_dict, mess):
        expected_keys = list(expected_dict.keys())
        expected_keys.sort()
        got_keys = list(got_dict.keys())
        got_keys.sort()
        self.assert_equal(expected_keys, got_keys,
                                               "%s\nThe two dictionaries did not have the same keys" % mess)

    def find_first_diff_char(self, string1, string2):

        if string1 == None:
            string1 = ''
        if string2 == None:
            string2 = ''

        if (string1 == string2):
            return None
        if (len(string1) < len(string2)):
            upto = len(string1)-1;
        else:
            upto = len(string2)-1;
        if (upto < 0):
            # one of the strings was empty but not the other
            return -1

        for ii in range(upto+1):
            char1 = string1[ii]
            char2 = string2[ii]
            if char1 != char2:
                return ii;
        if (upto < len(string1)-1 or upto < len(string2)-1):
            return upto + 1;
        else:
            return undef;



    def assert_file_exists(self, fpath, mess):
        if not os.path.exists(fpath):
            self.fail(mess + "\nFile '%s' did not exist." % fpath)
        elif not os.path.isfile(fpath):
            self.fail(mess + "\nPath '%s' is not a file." % fpath)

    def assert_file_content_is(self, fpath, expected_content, message):
        self.assert_file_exists(fpath, message)
        file = open(fpath, 'r')
        got_content = file.read()
        file.close()
        self.assert_equal(expected_content, got_content, message)

    def assert_file_contains_N_lines(self, fpath, exp_N_lines, mess):
        self.assert_file_exists(fpath, mess)
        file = open(fpath, 'r')
        content = file.read()
        file.close()
        got_N_lines = len(content.split("\n"))
        self.assert_equal(exp_N_lines, got_N_lines, mess + "\nNumber of lines in the file was not as expected.")

    def make_empty_dir_for_file(self, fpath):
        directory = self.makedirs_for_file(fpath)
        files = os.listdir(directory)
        for file in files:
            if os.path.isfile(file):
                os.remove(file)
            elif os.path.isdir(file):
                os.removedirs(file)
            else:
                pass

    def makedirs_for_file(self, fpath):
        head, tail = os.path.split(fpath)
        try:
            os.makedirs(head)
        except:
            # Presumably, directory already existed
            pass
        return head

######################################################################
# Some introspection methods needed by TestCaseWithHelpers.
# We put them here instead of in a separate class, in order to make
# TestCaseWithHelpers self-contained.
######################################################################

    def what_class(self, instance):
        """Returns a string describing the class of an instance.

        It works with any Python class or Python standard data types (int, float,
        string, etc.), but not with extension classes."""

        is_class = 'unknown'
        try:
            tmp = instance.__class__
            is_class = tmp
        except AttributeError:
            #
            # The instance is not a python class. Maybe one of the
            # standard python data types?
            #
            is_class = type(instance)

        return str(is_class)

    def isnumber(self, instance):
        return isinstance(instance, int) or isinstance(instance, float)

    def issequence(self, instance):
        return isinstance(instance, list) or \
               isinstance(instance, tuple)

    def isset(self, instance):
        return isinstance(instance, set)

    def isdictionary(self, instance):
        return isinstance(instance, dict)

    # new QH, conversion python 2 to python 3:
    def isstring(self, instance):
        return type(instance) == str
    def isbinary(self, instance):
        return type(instance) == bytes

    def isstringlike(self, instance):
        return type(instance) == str


    def isbasetype(self, instance):
        return re.search("^\<type ", repr(self.what_class(instance)))

######################################################################
# Old deprecated names for some methods. Still supported for backward
# compatibility.
######################################################################

    def assert_equals(self, expected, got, mess, epsilon=0):
        print("\nWARNING: Call to deprecated method TestCaseWithHelpers.assert_equals()\n")
        self.assert_equal(expected, got, mess, epsilon)

    def assert_string_equals(self, exp_string, got_string, message=''):
        print("\nWARNING: Call to deprecated method TestCaseWithHelpers.assert_string_equals\n")
        self.assert_equal_string(exp_string, got_string, message)

    def assert_dicts_have_same_content(self, expected_dict, got_dict, mess):
        print("\nWARNING: Call to deprecated method TestCaseWithHelpers.assert_dicts_have_same_content\n")
        self.assert_equals(expected_dict, got_dict, mess)

    def assert_sequences_have_same_content(self, expected, got, mess):
        print("\nWARNING: Call to deprecated method TestCaseWithHelpers.assert_sequences_have_same_content\n")
        self.assert_equal(expected, got, mess)

#------------------------------------------------------------
def assert_equal(expected, got, mess="", epsilon=0):
    if expected == got: return
    try:
        assert_equal_dispatch_according_to_type(expected, got, mess, epsilon)
    except RuntimeError as err:
        err = self.check_for_infinite_recursion_error(err)
        raise err

def assert_equal_dispatch_according_to_type(expected, got, mess, epsilon):
    assert isnumber(epsilon), "assert_equal called with a value of epsilon that was not a number. Type of epsilon was: %s, value was %s" % (what_class(epsilon), epsilon)
    class_exp, class_got = what_class(expected), what_class(got)
    if class_exp != class_got:
        if self.isnumber(expected) and self.isnumber(got):
            pass
        elif self.isstringlike(expected) and self.isstringlike(got):
            pass
            # print('got PY2 str, expected unicode: %s'% got)
        else:
            mess = mess + "\n----\nThe two objects were not of same type"
            mess = mess + "\nExpected type: %s, Got type:  %s" % (type(expected), type(got))
            mess = mess + "\nExpected:\n   %s\nGot:\n   %s" % (expected, got)

            raise ValueError(mess)

    if (issequence(expected)):
        assert_equal_sequence(expected, got, mess, epsilon)
    elif (isset(expected)):
        assert_equal_set(expected, got, mess, epsilon)
    elif (isdictionary(expected)):
        assert_equal_dictionary(expected, got, mess, epsilon)
    elif (isnumber(expected)):
        mess = mess + "\n----\nThe two numbers differed significantly."
        mess = mess + "\nExpected:\n   %s\nGot:\n   %s" % (expected, got)
        if epsilon == 0:
            assert expected == got, mess
        else:
            assert (got <= expected + epsilon) and (got >= expected - epsilon), mess + "\nValue was not within epsilon=%s range of expected value." % epsilon
    elif (isstring(expected)):
        assert_equal_string(expected, got, mess)
    elif (isbasetype(expected)):
        assert expected == got, mess
    else:
        assert_equal_objects(expected, got, mess, epsilon)


def assert_equal_string(exp_string, got_string, mess=''):
    if isbinary(exp_string):
        raise ValueError("expected string should be unicode: %s"% exp_string)
    
    if isbinary(got_string):
        mess = "WARNING, got binary string expectied str, %s "% got_string
        got_string = utilsqh.convertToUnicode(got_string)
    if exp_string == got_string: return
    
    first_diff = find_first_diff_char(got_string, exp_string)

    if first_diff != None:
        expch = exp_string[:first_diff] + "~~~" + exp_string[first_diff:]
        gotch = got_string[:first_diff] + "~~~" + got_string[first_diff:]
        mess = mess + "\nStrings differ at position %s"% first_diff
        mess = mess + "\nexp: |%s|"% expch
        mess = mess + "\ngot: |%s|"% gotch
        raise ValueError(mess)

def assert_equal_sequence(expected, got, mess="", epsilon=0):
    if expected == got: return
    mess = mess + "\n----\nThe two sequences differred\nExpected sequence:\n   %s\nGot sequence:\n   %s" % \
           (pformat(expected), pformat(got))

    if len(expected) != len(got):
        mess = mess + "\nlengths differ, len(expected): %s, len(got): %s"% (len(expected), len(got))
        if len(expected) > len(got):
            mess = mess + "\nextra in expected: %s"% expected[len(got):]
        else:
            mess = mess + "\nextra in got: %s"% got[len(expected):]
    for i in range(min(len(expected), len(got))):
        if expected[i] != got[i]:
            mess = mess + "\nsequences differ at index %s"% i
            mess = mess + "\nexpected[%s]: |%s|"% (i, expected[i])
            mess = mess + "\n     got[%s]: [%s]"% (i, got[i])
            break
    raise ValueError(mess)

def assert_equal_set(expected, got, mess="", epsilon=0):
    if expected == got:
        return
    mess = mess + "\n----\nThe two sets differ\nExpected sequence:\n   %s\nGot sequence:\n   %s" % \
           (pformat(expected), pformat(got))
    union = expected & got
    restexpected = expected - union
    restgot = got - union

    if union != expected:
        mess = mess + "\nonly in expected: %s"% restexpected
    if union != got:
        mess = mess + "\nonly in got: %s"% restgot
    raise ValueError(mess)

def assert_equal_dictionary(expected, got, mess="", epsilon=0):
    """stand alone version of test
    """
    if expected == got: return
    expected_keys = set(expected.keys())
    got_keys = set(got.keys())

    mess = mess + "\n----\nThe two dictionaries differ"
    mess = mess + "\nExpected:\n   %s\nGot:\n   %s" % (pformat(expected), pformat(got))

    # NOTE: Keys must be exactly equal, even if epsilon is greater than 0.
    assert_equal_set(expected_keys, got_keys,
                          mess + "\nDictionaries did not have the same set of keys.")
    for a_key in expected_keys:
        assert_equal(expected[a_key], got[a_key],
                mess + "\nValues of dictionaries differed at key '%s'" % a_key,
                epsilon)

def find_first_diff_char(string1, string2):

    if string1 == None:
        string1 = ''
    if string2 == None:
        string2 = ''

    if (string1 == string2):
        return None
    if (len(string1) < len(string2)):
        upto = len(string1)-1;
    else:
        upto = len(string2)-1;
    if (upto < 0):
        # one of the strings was empty but not the other
        return -1

    for ii in range(upto+1):
        char1 = string1[ii]
        char2 = string2[ii]
        if char1 != char2:
            return ii;
    if (upto < len(string1)-1 or upto < len(string2)-1):
        return upto + 1;
    else:
        return undef;

def isnumber(instance):
    return isinstance(instance, int) or isinstance(instance, float)

def issequence(instance):
    return isinstance(instance, list) or \
           isinstance(instance, tuple)

def isset(instance):
    return isinstance(instance, set)

def isdictionary(instance):
    return isinstance(instance, dict)

# new QH, conversion python 2 to python 3:
def isstring(instance):
    return type(instance) == str
def isbinary(instance):
    return type(instance) == bytes

def isstringlike(instance):
    return type(instance) == str

def what_class(instance):
    """Returns a string describing the class of an instance.

    It works with any Python class or Python standard data types (int, float,
    string, etc.), but not with extension classes."""

    is_class = 'unknown'
    try:
        tmp = instance.__class__
        is_class = tmp
    except AttributeError:
        #
        # The instance is not a python class. Maybe one of the
        # standard python data types?
        #
        is_class = type(instance)

    return is_class

if __name__ == "__main__":
    import sys
    print("version", sys.version)
    print("test expects to go wrong!!!!!")
    # print(assert_equal("hello", "helloo"))
    # assert_equal([1,2,3], [1,2,4])
    d1 = dict(a=1, b=2, c=3)
    d2 = dict(a=1, b=2, c=4)
    assert_equal(d1, d2)