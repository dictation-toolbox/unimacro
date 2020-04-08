#! /usr/bin/env python
# -*- coding: latin-1 -*-

"""iban.py 1.5 - Create or check International Bank Account Numbers (IBAN).

Copyright (C) 2002-2010, Thomas Günther <tom@toms-cafe.de>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License along
with this program; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

Usage as module:
    from iban import *

    code, bank, account = "DE", "12345678", "123456789"
    try:
        iban = create_iban(code, bank, account)
    except IBANError, err:
        print err
    else:
        print "  Correct IBAN: %s << %s ?? %s %s" % (iban, code, bank, account)

    iban = "DE58123456780123456789"
    try:
        code, checksum, bank, account = check_iban(iban)
    except IBANError, err:
        print err
    else:
        print "  Correct IBAN: %s >> %s %s %s %s" % (iban, code, checksum,
                                                     bank, account)
"""
from functools import reduce

__all__ = ["create_iban", "check_iban", "IBANError"]

usage = \
"""Create or check International Bank Account Numbers (IBAN).

Usage: iban <iban>
       iban <country> <bank/branch> <account>
       iban -h | -f | -e | -t

 e.g.: iban DE58123456780123456789
       iban DE 12345678 123456789

       <iban>         is the International Bank Account Number (IBAN)
       <country>      is the Country Code from ISO 3166
       <bank/branch>  is the Bank/Branch Code part of the IBAN from ISO 13616
       <account>      is the Account Number including check digits

       iban -h        prints this message
       iban -f        prints a table with the country specific iban format
       iban -e        prints an example for each country
       iban -t        prints some test data

Information about IBAN are from European Committee for Banking Standards
(www.ecbs.org/iban.htm). IBAN is an ISO standard (ISO 13616: 1997).
"""

class Country:
    """Class for country specific iban data."""

    def __init__(self, name, code, bank_form, acc_form):
        """Constructor for Country objects.

        Arguments:
            name      - Name of the country
            code      - Country Code from ISO 3166
            bank_form - Format of bank/branch code part (e.g. "0 4a 0 ")
            acc_form  - Format of account number part (e.g. "0  11  2n")
        """
        self.name = name
        self.code = code
        self.bank = self._decode_format(bank_form)
        self.acc  = self._decode_format(acc_form)

    def bank_lng(self):
        return reduce(lambda sum, part: sum + part[0], self.bank, 0)

    def acc_lng(self):
        return reduce(lambda sum, part: sum + part[0], self.acc, 0)

    def total_lng(self):
        return 4 + self.bank_lng() + self.acc_lng()

    def _decode_format(self, form):
        form_list = []
        for part in form.split(" "):
            if part:
                typ = part[-1]
                if typ in ("a", "n"):
                    part = part[:-1]
                else:
                    typ = "c"
                lng = int(part)
                form_list.append((lng, typ))
        return tuple(form_list)

# BBAN data from ISO 13616, Country codes from ISO 3166 (www.iso.org).
iban_data = (Country("Andorra",        "AD", "0  4n 4n", "0  12   0 "),
             Country("Albania",        "AL", "0  8n 0 ", "0  16   0 "),
             Country("Austria",        "AT", "0  5n 0 ", "0  11n  0 "),
             Country("Bosnia and Herzegovina",
                                       "BA", "0  3n 3n", "0   8n  2n"),
             Country("Belgium",        "BE", "0  3n 0 ", "0   7n  2n"),
             Country("Bulgaria",       "BG", "0  4a 4n", "2n  8   0 "),
             Country("Switzerland",    "CH", "0  5n 0 ", "0  12   0 "),
             Country("Cyprus",         "CY", "0  3n 5n", "0  16   0 "),
             Country("Czech Republic", "CZ", "0  4n 0 ", "0  16n  0 "),
             Country("Germany",        "DE", "0  8n 0 ", "0  10n  0 "),
             Country("Denmark",        "DK", "0  4n 0 ", "0   9n  1n"),
             Country("Estonia",        "EE", "0  2n 0 ", "2n 11n  1n"),
             Country("Spain",          "ES", "0  4n 4n", "2n 10n  0 "),
             Country("Finland",        "FI", "0  6n 0 ", "0   7n  1n"),
             Country("Faroe Islands",  "FO", "0  4n 0 ", "0   9n  1n"),
             Country("France",         "FR", "0  5n 5n", "0  11   2n"),
             Country("United Kingdom", "GB", "0  4a 6n", "0   8n  0 "),
             Country("Georgia",        "GE", "0  2a 0 ", "0  16n  0 "),
             Country("Gibraltar",      "GI", "0  4a 0 ", "0  15   0 "),
             Country("Greenland",      "GL", "0  4n 0 ", "0   9n  1n"),
             Country("Greece",         "GR", "0  3n 4n", "0  16   0 "),
             Country("Croatia",        "HR", "0  7n 0 ", "0  10n  0 "),
             Country("Hungary",        "HU", "0  3n 4n", "1n 15n  1n"),
             Country("Ireland",        "IE", "0  4a 6n", "0   8n  0 "),
             Country("Israel",         "IL", "0  3n 3n", "0  13n  0 "),
             Country("Iceland",        "IS", "0  4n 0 ", "2n 16n  0 "),
             Country("Italy",          "IT", "1a 5n 5n", "0  12   0 "),
             Country("Kuwait",         "KW", "0  4a 0 ", "0  22   0 "),
             Country("Kazakhstan",     "KZ", "0  3n 0 ", "0  13   0 "),
             Country("Lebanon",        "LB", "0  4n 0 ", "0  20   0 "),
             Country("Liechtenstein",  "LI", "0  5n 0 ", "0  12   0 "),
             Country("Lithuania",      "LT", "0  5n 0 ", "0  11n  0 "),
             Country("Luxembourg",     "LU", "0  3n 0 ", "0  13   0 "),
             Country("Latvia",         "LV", "0  4a 0 ", "0  13   0 "),
             Country("Monaco",         "MC", "0  5n 5n", "0  11   2n"),
             Country("Montenegro",     "ME", "0  3n 0 ", "0  13n  2n"),
             Country("Macedonia, Former Yugoslav Republic of",
                                       "MK", "0  3n 0 ", "0  10   2n"),
             Country("Mauritania",     "MR", "0  5n 5n", "0  11n  2n"),
             Country("Malta",          "MT", "0  4a 5n", "0  18   0 "),
             Country("Mauritius",      "MU", "0  4a 4n", "0  15n  3a"),
             Country("Netherlands",    "NL", "0  4a 0 ", "0  10n  0 "),
             Country("Norway",         "NO", "0  4n 0 ", "0   6n  1n"),
             Country("Poland",         "PL", "0  8n 0 ", "0  16n  0 "),
             Country("Portugal",       "PT", "0  4n 4n", "0  11n  2n"),
             Country("Romania",        "RO", "0  4a 0 ", "0  16   0 "),
             Country("Serbia",         "RS", "0  3n 0 ", "0  13n  2n"),
             Country("Saudi Arabia",   "SA", "0  2n 0 ", "0  18   0 "),
             Country("Sweden",         "SE", "0  3n 0 ", "0  16n  1n"),
             Country("Slovenia",       "SI", "0  5n 0 ", "0   8n  2n"),
             Country("Slovak Republic",
                                       "SK", "0  4n 0 ", "0  16n  0 "),
             Country("San Marino",     "SM", "1a 5n 5n", "0  12   0 "),
             Country("Tunisia",        "TN", "0  2n 3n", "0  13n  2n"),
             Country("Turkey",         "TR", "0  5n 0 ", "1  16   0 "))

def country_data(code):
    """Search the country code in the iban_data list."""
    for country in iban_data:
        if country.code == code:
            return country
    return None

def mod97(digit_string):
    """Modulo 97 for huge numbers given as digit strings.

    This function is a prototype for a JavaScript implementation.
    In Python this can be done much easier: long(digit_string) % 97.
    """
    m = 0
    for d in digit_string:
        m = (m * 10 + int(d)) % 97
    return m

def fill0(s, l):
    """Fill the string with leading zeros until length is reached."""
    return s.zfill(l)

def strcmp(s1, s2):
    """Compare two strings respecting german umlauts."""
    chars = "AaÄäBbCcDdEeFfGgHhIiJjKkLlMmNnOoÖöPpQqRrSsßTtUuÜüVvWwXxYyZz"
    lng = min(len(s1), len(s2))
    for i in range(lng):
        d = chars.find(s1[i]) - chars.find(s2[i]);
        if d != 0:
            return d
    return len(s1) - len(s2)

def country_index_table():
    """Create an index table of the iban_data list sorted by country names."""
    tab = list(range(len(iban_data)))
    for i in range(len(tab) - 1, 0, -1):
        for j in range(i):
            if strcmp(iban_data[tab[j]].name, iban_data[tab[j+1]].name) > 0:
                t = tab[j]; tab[j] = tab[j+1]; tab[j+1] = t
    return tab

def checksum_iban(iban):
    """Calculate 2-digit checksum of an IBAN."""
    code     = iban[:2]
    checksum = iban[2:4]
    bban     = iban[4:]

    # Assemble digit string
    digits = ""
    for ch in bban.upper():
        if ch.isdigit():
            digits += ch
        else:
            digits += str(ord(ch) - ord("A") + 10)
    for ch in code:
        digits += str(ord(ch) - ord("A") + 10)
    digits += checksum

    # Calculate checksum
    checksum = 98 - mod97(digits)
    return fill0(str(checksum), 2)

def fill_account(country, account):
    """Fill the account number part of IBAN with leading zeros."""
    return fill0(account, country.acc_lng())

def invalid_part(form_list, iban_part):
    """Check if syntax of the part of IBAN is invalid."""
    for lng, typ in form_list:
        if lng > len(iban_part):
            lng = len(iban_part)
        for ch in iban_part[:lng]:
            a = ("A" <= ch <= "Z")
            n = ch.isdigit()
            c = n or a or ("a" <= ch <= "z")
            if (not c and typ == "c") or \
               (not a and typ == "a") or \
               (not n and typ == "n"):
                return 1
        iban_part = iban_part[lng:]
    return 0

def invalid_bank(country, bank):
    """Check if syntax of the bank/branch code part of IBAN is invalid."""
    return len(bank) != country.bank_lng() or \
           invalid_part(country.bank, bank)

def invalid_account(country, account):
    """Check if syntax of the account number part of IBAN is invalid."""
    return len(account) > country.acc_lng() or \
           invalid_part(country.acc, fill_account(country, account))

def calc_iban(country, bank, account, alternative = 0):
    """Calculate the checksum and assemble the IBAN."""
    account = fill_account(country, account)
    checksum = checksum_iban(country.code + "00" + bank + account)
    if alternative:
        checksum = fill0(str(mod97(checksum)), 2)
    return country.code + checksum + bank + account

def iban_okay(iban):
    """Check the checksum of an IBAN."""
    return checksum_iban(iban) == "97"

class IBANError(Exception):
    def __init__(self, errmsg):
        Exception.__init__(self, errmsg)

def create_iban(code, bank, account, alternative = 0):
    """Check the input, calculate the checksum and assemble the IBAN.

    Return the calculated IBAN.
    Return the alternative IBAN if alternative is true.
    Raise an IBANError exception if the input is not correct.
    """
    err = None
    country = country_data(code)
    if not country:
        err = "Unknown Country Code: %s" % code
    elif len(bank) != country.bank_lng():
        err = "Bank/Branch Code length %s is not correct for %s (%s)" % \
              (len(bank), country.name, country.bank_lng())
    elif invalid_bank(country, bank):
        err = "Bank/Branch Code %s is not correct for %s" % \
              (bank, country.name)
    elif len(account) > country.acc_lng():
        err = "Account Number length %s is not correct for %s (%s)" % \
              (len(account), country.name, country.acc_lng())
    elif invalid_account(country, account):
        err = "Account Number %s is not correct for %s" % \
              (account, country.name)
    if err:
        raise IBANError(err)
    return calc_iban(country, bank, account, alternative)

def check_iban(iban):
    """Check the syntax and the checksum of an IBAN.

    Return the parts of the IBAN: Country Code, Checksum, Bank/Branch Code and
    Account number.
    Raise an IBANError exception if the input is not correct.
    """
    err = None
    code     = iban[:2]
    checksum = iban[2:4]
    bban     = iban[4:]
    country = country_data(code)
    if not country:
        err = "Unknown Country Code: %s" % code
    elif len(iban) != country.total_lng():
        err = "IBAN length %s is not correct for %s (%s)" % \
              (len(iban), country.name, country.total_lng())
    else:
        bank_lng = country.bank_lng()
        bank     = bban[:bank_lng]
        account  = bban[bank_lng:]
        if invalid_bank(country, bank):
            err = "Bank/Branch Code %s is not correct for %s" % \
                  (bank, country.name)
        elif invalid_account(country, account):
            err = "Account Number %s is not correct for %s" % \
                  (account, country.name)
        elif not(checksum.isdigit()):
            err = "IBAN Checksum %s is not numeric" % checksum
        elif not iban_okay(iban):
            err = "Incorrect IBAN: %s >> %s %s %s %s" % \
                  (iban, code, checksum, bank, account)
    if err:
        raise IBANError(err)
    return code, checksum, bank, account

def print_new_iban(code, bank, account):
    """Check the input, calculate the checksum, assemble and print the IBAN."""
    try:
        iban = create_iban(code, bank, account)
    except IBANError as err:
        print(err)
        return ""
    print("  Correct IBAN: %s << %s ?? %s %s" % (iban, code, bank, account))
    return iban

def print_iban_parts(iban):
    """Check the syntax and the checksum of an IBAN and print the parts."""
    try:
        code, checksum, bank, account = check_iban(iban)
    except IBANError as err:
        print(err)
        return ()
    print("  Correct IBAN: %s >> %s %s %s %s" % (iban, code, checksum,
                                                 bank, account))
    return code, checksum, bank, account

def print_format():
    """Print a table with the country specific iban format."""
    print("IBAN-Format (a = A-Z, n = 0-9, c = A-Z/a-z/0-9):")
    print("                    | Bank/Branch-Code      | Account Number")
    print(" Country       Code | check1  bank  branch  |" + \
          " check2 number check3")
    print("--------------------|-----------------------|" + \
          "---------------------")
    for idx in country_index_table():
        country = iban_data[idx]
        if len(country.name) <= 14:
            print(country.name.ljust(14), "|", country.code, "|", end=' ')
        else:
            print(country.name)
            print("               |", country.code, "|", end=' ')
        for lng, typ in country.bank:
            if lng:
                print(str(lng).rjust(3), typ.ljust(2), end=' ')
            else:
                print("  -   ", end=' ')
        print(" |", end=' ')
        for lng, typ in country.acc:
            if lng:
                print(str(lng).rjust(3), typ.ljust(2), end=' ')
            else:
                print("  -   ", end=' ')
        print()

def print_test_data(*data):
    """Print a table with iban test data."""
    for code, bank, account, checksum in data:
        created_iban = print_new_iban(code, bank, account)
        if created_iban:
            iban = code + checksum + bank + \
                   fill_account(country_data(code), account)
            print_iban_parts(iban)
            if iban != created_iban:
                if iban == create_iban(code, bank, account, 1):
                    print("  Alternative IBAN")
                else:
                    print("  Changed IBAN")

def print_examples():
    print("IBAN-Examples:")
    print_test_data(("AD", "00012030",    "200359100100",         "12"),
                    ("AL", "21211009",    "0000000235698741",     "47"),
                    ("AT", "19043",       "00234573201",          "61"),
                    ("BA", "129007",      "9401028494",           "39"),
                    ("BE", "539",         "007547034",            "68"),
                    ("BG", "BNBG9661",    "1020345678",           "80"),
                    ("CH", "00762",       "011623852957",         "93"),
                    ("CY", "00200128",    "0000001200527600",     "17"),
                    ("CZ", "0800",        "0000192000145399",     "65"),
                    ("DE", "37040044",    "0532013000",           "89"),
                    ("DK", "0040",        "0440116243",           "50"),
                    ("EE", "22",          "00221020145685",       "38"),
                    ("ES", "21000418",    "450200051332",         "91"),
                    ("FI", "123456",      "00000785",             "21"),
                    ("FO", "6460",        "0001631634",           "62"),
                    ("FR", "2004101005",  "0500013M02606",        "14"),
                    ("GB", "NWBK601613",  "31926819",             "29"),
                    ("GE", "NB",          "0000000101904917",     "29"),
                    ("GI", "NWBK",        "000000007099453",      "75"),
                    ("GL", "6471",        "0001000206",           "89"),
                    ("GR", "0110125",     "0000000012300695",     "16"),
                    ("HR", "1001005",     "1863000160",           "12"),
                    ("HU", "1177301",     "61111101800000000",    "42"),
                    ("IE", "AIBK931152",  "12345678",             "29"),
                    ("IL", "010800",      "0000099999999",        "62"),
                    ("IS", "0159",        "260076545510730339",   "14"),
                    ("IT", "X0542811101", "000000123456",         "60"),
                    ("KW", "CBKU",        "0000000000001234560101", "81"),
                    ("KZ", "125",         "KZT5004100100",        "86"),
                    ("LB", "0999",        "00000001001901229114", "62"),
                    ("LI", "08810",       "0002324013AA",         "21"),
                    ("LT", "10000",       "11101001000",          "12"),
                    ("LU", "001",         "9400644750000",        "28"),
                    ("LV", "BANK",        "0000435195001",        "80"),
                    ("MC", "1273900070",  "0011111000h79",        "11"),
                    ("ME", "505",         "000012345678951",      "25"),
                    ("MK", "250",         "120000058984",         "07"),
                    ("MR", "0002000101",  "0000123456753",        "13"),
                    ("MT", "MALT01100",   "0012345MTLCAST001S",   "84"),
                    ("MU", "BOMM0101",    "101030300200000MUR",   "17"),
                    ("NL", "ABNA",        "0417164300",           "91"),
                    ("NO", "8601",        "1117947",              "93"),
                    ("PL", "10901014",    "0000071219812874",     "61"),
                    ("PT", "00020123",    "1234567890154",        "50"),
                    ("RO", "AAAA",        "1B31007593840000",     "49"),
                    ("RS", "260",         "005601001611379",      "35"),
                    ("SA", "80",          "000000608010167519",   "03"),
                    ("SE", "500",         "00000058398257466",    "45"),
                    ("SI", "19100",       "0000123438",           "56"),
                    ("SK", "1200",        "0000198742637541",     "31"),
                    ("SM", "U0322509800", "000000270100",         "86"),
                    ("TN", "10006",       "035183598478831",      "59"),
                    ("TR", "00061",       "00519786457841326",    "33"))

def print_test():
    print("IBAN-Test:")
    print_test_data(("XY", "1",           "2",                    "33"),
                    ("AD", "11112222",    "C3C3C3C3C3C3",         "11"),
                    ("AD", "1111222",     "C3C3C3C3C3C3",         "11"),
                    ("AD", "X1112222",    "C3C3C3C3C3C3",         "11"),
                    ("AD", "111@2222",    "C3C3C3C3C3C3",         "11"),
                    ("AD", "1111X222",    "C3C3C3C3C3C3",         "11"),
                    ("AD", "1111222@",    "C3C3C3C3C3C3",         "11"),
                    ("AD", "11112222",    "@3C3C3C3C3C3",         "11"),
                    ("AD", "11112222",    "C3C3C3C3C3C@",         "11"),
                    ("AL", "11111111",    "B2B2B2B2B2B2B2B2",     "54"),
                    ("AL", "1111111",     "B2B2B2B2B2B2B2B2",     "54"),
                    ("AL", "X1111111",    "B2B2B2B2B2B2B2B2",     "54"),
                    ("AL", "1111111@",    "B2B2B2B2B2B2B2B2",     "54"),
                    ("AL", "11111111",    "@2B2B2B2B2B2B2B2",     "54"),
                    ("AL", "11111111",    "B2B2B2B2B2B2B2B@",     "54"),
                    ("AT", "11111",       "22222222222",          "17"),
                    ("AT", "1111",        "22222222222",          "17"),
                    ("AT", "X1111",       "22222222222",          "17"),
                    ("AT", "1111@",       "22222222222",          "17"),
                    ("AT", "11111",       "X2222222222",          "17"),
                    ("AT", "11111",       "2222222222@",          "17"),
                    ("BA", "111222",      "3333333344",           "79"),
                    ("BA", "11122",       "3333333344",           "79"),
                    ("BA", "X11222",      "3333333344",           "79"),
                    ("BA", "11@222",      "3333333344",           "79"),
                    ("BA", "111X22",      "3333333344",           "79"),
                    ("BA", "11122@",      "3333333344",           "79"),
                    ("BA", "111222",      "X333333344",           "79"),
                    ("BA", "111222",      "3333333@44",           "79"),
                    ("BA", "111222",      "33333333X4",           "79"),
                    ("BA", "111222",      "333333334@",           "79"),
                    ("BE", "111",         "222222233",            "93"),
                    ("BE", "11",          "222222233",            "93"),
                    ("BE", "X11",         "222222233",            "93"),
                    ("BE", "11@",         "222222233",            "93"),
                    ("BE", "111",         "X22222233",            "93"),
                    ("BE", "111",         "222222@33",            "93"),
                    ("BE", "111",         "2222222X3",            "93"),
                    ("BE", "111",         "22222223@",            "93"),
                    ("BG", "AAAA2222",    "33D4D4D4D4",           "20"),
                    ("BG", "AAAA222",     "33D4D4D4D4",           "20"),
                    ("BG", "8AAA2222",    "33D4D4D4D4",           "20"),
                    ("BG", "AAA@2222",    "33D4D4D4D4",           "20"),
                    ("BG", "AAAAX222",    "33D4D4D4D4",           "20"),
                    ("BG", "AAAA222@",    "33D4D4D4D4",           "20"),
                    ("BG", "AAAA2222",    "X3D4D4D4D4",           "20"),
                    ("BG", "AAAA2222",    "3@D4D4D4D4",           "20"),
                    ("BG", "AAAA2222",    "33@4D4D4D4",           "20"),
                    ("BG", "AAAA2222",    "33D4D4D4D@",           "20"),
                    ("CH", "11111",       "B2B2B2B2B2B2",         "60"),
                    ("CH", "1111",        "B2B2B2B2B2B2",         "60"),
                    ("CH", "X1111",       "B2B2B2B2B2B2",         "60"),
                    ("CH", "1111@",       "B2B2B2B2B2B2",         "60"),
                    ("CH", "11111",       "@2B2B2B2B2B2",         "60"),
                    ("CH", "11111",       "B2B2B2B2B2B@",         "60"),
                    ("CY", "11122222",    "C3C3C3C3C3C3C3C3",     "29"),
                    ("CY", "1112222",     "C3C3C3C3C3C3C3C3",     "29"),
                    ("CY", "X1122222",    "C3C3C3C3C3C3C3C3",     "29"),
                    ("CY", "11@22222",    "C3C3C3C3C3C3C3C3",     "29"),
                    ("CY", "111X2222",    "C3C3C3C3C3C3C3C3",     "29"),
                    ("CY", "1112222@",    "C3C3C3C3C3C3C3C3",     "29"),
                    ("CY", "11122222",    "@3C3C3C3C3C3C3C3",     "29"),
                    ("CY", "11122222",    "C3C3C3C3C3C3C3C@",     "29"),
                    ("CZ", "1111",        "2222222222222222",     "68"),
                    ("CZ", "111",         "2222222222222222",     "68"),
                    ("CZ", "X111",        "2222222222222222",     "68"),
                    ("CZ", "111@",        "2222222222222222",     "68"),
                    ("CZ", "1111",        "X222222222222222",     "68"),
                    ("CZ", "1111",        "222222222222222@",     "68"),
                    ("DE", "11111111",    "2222222222",           "16"),
                    ("DE", "1111111",     "2222222222",           "16"),
                    ("DE", "X1111111",    "2222222222",           "16"),
                    ("DE", "1111111@",    "2222222222",           "16"),
                    ("DE", "11111111",    "X222222222",           "16"),
                    ("DE", "11111111",    "222222222@",           "16"),
                    ("DK", "1111",        "2222222223",           "79"),
                    ("DK", "111",         "2222222223",           "79"),
                    ("DK", "X111",        "2222222223",           "79"),
                    ("DK", "111@",        "2222222223",           "79"),
                    ("DK", "1111",        "X222222223",           "79"),
                    ("DK", "1111",        "22222222@3",           "79"),
                    ("DK", "1111",        "222222222X",           "79"),
                    ("EE", "11",          "22333333333334",       "96"),
                    ("EE", "1",           "22333333333334",       "96"),
                    ("EE", "X1",          "22333333333334",       "96"),
                    ("EE", "1@",          "22333333333334",       "96"),
                    ("EE", "11",          "X2333333333334",       "96"),
                    ("EE", "11",          "2@333333333334",       "96"),
                    ("EE", "11",          "22X33333333334",       "96"),
                    ("EE", "11",          "223333333333@4",       "96"),
                    ("EE", "11",          "2233333333333X",       "96"),
                    ("ES", "11112222",    "334444444444",         "71"),
                    ("ES", "1111222",     "334444444444",         "71"),
                    ("ES", "X1112222",    "334444444444",         "71"),
                    ("ES", "111@2222",    "334444444444",         "71"),
                    ("ES", "1111X222",    "334444444444",         "71"),
                    ("ES", "1111222@",    "334444444444",         "71"),
                    ("ES", "11112222",    "X34444444444",         "71"),
                    ("ES", "11112222",    "3@4444444444",         "71"),
                    ("ES", "11112222",    "33X444444444",         "71"),
                    ("ES", "11112222",    "33444444444@",         "71"),
                    ("FI", "111111",      "22222223",             "68"),
                    ("FI", "11111",       "22222223",             "68"),
                    ("FI", "X11111",      "22222223",             "68"),
                    ("FI", "11111@",      "22222223",             "68"),
                    ("FI", "111111",      "X2222223",             "68"),
                    ("FI", "111111",      "222222@3",             "68"),
                    ("FI", "111111",      "2222222X",             "68"),
                    ("FO", "1111",        "2222222223",           "49"),
                    ("FO", "111",         "2222222223",           "49"),
                    ("FO", "X111",        "2222222223",           "49"),
                    ("FO", "111@",        "2222222223",           "49"),
                    ("FO", "1111",        "X222222223",           "49"),
                    ("FO", "1111",        "22222222@3",           "49"),
                    ("FO", "1111",        "222222222X",           "49"),
                    ("FR", "1111122222",  "C3C3C3C3C3C44",        "44"),
                    ("FR", "111112222",   "C3C3C3C3C3C44",        "44"),
                    ("FR", "X111122222",  "C3C3C3C3C3C44",        "44"),
                    ("FR", "1111@22222",  "C3C3C3C3C3C44",        "44"),
                    ("FR", "11111X2222",  "C3C3C3C3C3C44",        "44"),
                    ("FR", "111112222@",  "C3C3C3C3C3C44",        "44"),
                    ("FR", "1111122222",  "@3C3C3C3C3C44",        "44"),
                    ("FR", "1111122222",  "C3C3C3C3C3@44",        "44"),
                    ("FR", "1111122222",  "C3C3C3C3C3CX4",        "44"),
                    ("FR", "1111122222",  "C3C3C3C3C3C4@",        "44"),
                    ("GB", "AAAA222222",  "33333333",             "45"),
                    ("GB", "AAAA22222",   "33333333",             "45"),
                    ("GB", "8AAA222222",  "33333333",             "45"),
                    ("GB", "AAA@222222",  "33333333",             "45"),
                    ("GB", "AAAAX22222",  "33333333",             "45"),
                    ("GB", "AAAA22222@",  "33333333",             "45"),
                    ("GB", "AAAA222222",  "X3333333",             "45"),
                    ("GB", "AAAA222222",  "3333333@",             "45"),
                    ("GE", "AA",          "2222222222222222",     "98"),
                    ("GE", "A",           "2222222222222222",     "98"),
                    ("GE", "8A",          "2222222222222222",     "98"),
                    ("GE", "A@",          "2222222222222222",     "98"),
                    ("GE", "AA",          "X222222222222222",     "98"),
                    ("GE", "AA",          "222222222222222@",     "98"))
    print_test_data(("GI", "AAAA",        "B2B2B2B2B2B2B2B",      "72"),
                    ("GI", "AAA",         "B2B2B2B2B2B2B2B",      "72"),
                    ("GI", "8AAA",        "B2B2B2B2B2B2B2B",      "72"),
                    ("GI", "AAA@",        "B2B2B2B2B2B2B2B",      "72"),
                    ("GI", "AAAA",        "@2B2B2B2B2B2B2B",      "72"),
                    ("GI", "AAAA",        "B2B2B2B2B2B2B2@",      "72"),
                    ("GL", "1111",        "2222222223",           "49"),
                    ("GL", "111",         "2222222223",           "49"),
                    ("GL", "X111",        "2222222223",           "49"),
                    ("GL", "111@",        "2222222223",           "49"),
                    ("GL", "1111",        "X222222223",           "49"),
                    ("GL", "1111",        "22222222@3",           "49"),
                    ("GL", "1111",        "222222222X",           "49"),
                    ("GR", "1112222",     "C3C3C3C3C3C3C3C3",     "61"),
                    ("GR", "111222",      "C3C3C3C3C3C3C3C3",     "61"),
                    ("GR", "X112222",     "C3C3C3C3C3C3C3C3",     "61"),
                    ("GR", "11@2222",     "C3C3C3C3C3C3C3C3",     "61"),
                    ("GR", "111X222",     "C3C3C3C3C3C3C3C3",     "61"),
                    ("GR", "111222@",     "C3C3C3C3C3C3C3C3",     "61"),
                    ("GR", "1112222",     "@3C3C3C3C3C3C3C3",     "61"),
                    ("GR", "1112222",     "C3C3C3C3C3C3C3C@",     "61"),
                    ("HR", "1111111",     "2222222222",           "94"),
                    ("HR", "111111",      "2222222222",           "94"),
                    ("HR", "X111111",     "2222222222",           "94"),
                    ("HR", "111111@",     "2222222222",           "94"),
                    ("HR", "1111111",     "X222222222",           "94"),
                    ("HR", "1111111",     "222222222@",           "94"),
                    ("HU", "1112222",     "34444444444444445",    "35"),
                    ("HU", "111222",      "34444444444444445",    "35"),
                    ("HU", "X112222",     "34444444444444445",    "35"),
                    ("HU", "11@2222",     "34444444444444445",    "35"),
                    ("HU", "111X222",     "34444444444444445",    "35"),
                    ("HU", "111222@",     "34444444444444445",    "35"),
                    ("HU", "1112222",     "X4444444444444445",    "35"),
                    ("HU", "1112222",     "3X444444444444445",    "35"),
                    ("HU", "1112222",     "344444444444444@5",    "35"),
                    ("HU", "1112222",     "3444444444444444X",    "35"),
                    ("IE", "AAAA222222",  "33333333",             "18"),
                    ("IE", "AAAA22222",   "33333333",             "18"),
                    ("IE", "8AAA222222",  "33333333",             "18"),
                    ("IE", "AAA@222222",  "33333333",             "18"),
                    ("IE", "AAAAX22222",  "33333333",             "18"),
                    ("IE", "AAAA22222@",  "33333333",             "18"),
                    ("IE", "AAAA222222",  "X3333333",             "18"),
                    ("IE", "AAAA222222",  "3333333@",             "18"),
                    ("IL", "111222",      "3333333344",           "64"),
                    ("IL", "11122",       "3333333344",           "64"),
                    ("IL", "X11222",      "3333333344",           "64"),
                    ("IL", "11@222",      "3333333344",           "64"),
                    ("IL", "111X22",      "3333333344",           "64"),
                    ("IL", "11122@",      "3333333344",           "64"),
                    ("IL", "111222",      "X333333333333",        "64"),
                    ("IL", "111222",      "333333333333@",        "64"),
                    ("IS", "1111",        "223333333333333333",   "12"),
                    ("IS", "111",         "223333333333333333",   "12"),
                    ("IS", "X111",        "223333333333333333",   "12"),
                    ("IS", "111@",        "223333333333333333",   "12"),
                    ("IS", "1111",        "X23333333333333333",   "12"),
                    ("IS", "1111",        "2@3333333333333333",   "12"),
                    ("IS", "1111",        "22X333333333333333",   "12"),
                    ("IS", "1111",        "22333333333333333@",   "12"),
                    ("IT", "A2222233333", "D4D4D4D4D4D4",         "43"),
                    ("IT", "A222223333",  "D4D4D4D4D4D4",         "43"),
                    ("IT", "82222233333", "D4D4D4D4D4D4",         "43"),
                    ("IT", "AX222233333", "D4D4D4D4D4D4",         "43"),
                    ("IT", "A2222@33333", "D4D4D4D4D4D4",         "43"),
                    ("IT", "A22222X3333", "D4D4D4D4D4D4",         "43"),
                    ("IT", "A222223333@", "D4D4D4D4D4D4",         "43"),
                    ("IT", "A2222233333", "@4D4D4D4D4D4",         "43"),
                    ("IT", "A2222233333", "D4D4D4D4D4D@",         "43"),
                    ("KW", "AAAA",        "B2B2B2B2B2B2B2B2B2B2B2", "93"),
                    ("KW", "AAA",         "B2B2B2B2B2B2B2B2B2B2B2", "93"),
                    ("KW", "8AAA",        "B2B2B2B2B2B2B2B2B2B2B2", "93"),
                    ("KW", "AAA@",        "B2B2B2B2B2B2B2B2B2B2B2", "93"),
                    ("KW", "AAAA",        "@2B2B2B2B2B2B2B2B2B2B2", "93"),
                    ("KW", "AAAA",        "B2B2B2B2B2B2B2B2B2B2B@", "93"),
                    ("KZ", "111",         "B2B2B2B2B2B2B",        "21"),
                    ("KZ", "11",          "B2B2B2B2B2B2B",        "21"),
                    ("KZ", "X11",         "B2B2B2B2B2B2B",        "21"),
                    ("KZ", "11@",         "B2B2B2B2B2B2B",        "21"),
                    ("KZ", "111",         "@2B2B2B2B2B2B",        "21"),
                    ("KZ", "111",         "B2B2B2B2B2B2@",        "21"),
                    ("LB", "1111",        "B2B2B2B2B2B2B2B2B2B2", "88"),
                    ("LB", "111",         "B2B2B2B2B2B2B2B2B2B2", "88"),
                    ("LB", "X111",        "B2B2B2B2B2B2B2B2B2B2", "88"),
                    ("LB", "111@",        "B2B2B2B2B2B2B2B2B2B2", "88"),
                    ("LB", "1111",        "@2B2B2B2B2B2B2B2B2B2", "88"),
                    ("LB", "1111",        "B2B2B2B2B2B2B2B2B2B@", "88"),
                    ("LI", "11111",       "B2B2B2B2B2B2",         "73"),
                    ("LI", "1111",        "B2B2B2B2B2B2",         "73"),
                    ("LI", "X1111",       "B2B2B2B2B2B2",         "73"),
                    ("LI", "1111@",       "B2B2B2B2B2B2",         "73"),
                    ("LI", "11111",       "@2B2B2B2B2B2",         "73"),
                    ("LI", "11111",       "B2B2B2B2B2B@",         "73"),
                    ("LT", "11111",       "22222222222",          "15"),
                    ("LT", "1111",        "22222222222",          "15"),
                    ("LT", "X1111",       "22222222222",          "15"),
                    ("LT", "1111@",       "22222222222",          "15"),
                    ("LT", "11111",       "X2222222222",          "15"),
                    ("LT", "11111",       "2222222222@",          "15"),
                    ("LU", "111",         "B2B2B2B2B2B2B",        "27"),
                    ("LU", "11",          "B2B2B2B2B2B2B",        "27"),
                    ("LU", "X11",         "B2B2B2B2B2B2B",        "27"),
                    ("LU", "11@",         "B2B2B2B2B2B2B",        "27"),
                    ("LU", "111",         "@2B2B2B2B2B2B",        "27"),
                    ("LU", "111",         "B2B2B2B2B2B2@",        "27"),
                    ("LV", "AAAA",        "B2B2B2B2B2B2B",        "86"),
                    ("LV", "AAA",         "B2B2B2B2B2B2B",        "86"),
                    ("LV", "8AAA",        "B2B2B2B2B2B2B",        "86"),
                    ("LV", "AAA@",        "B2B2B2B2B2B2B",        "86"),
                    ("LV", "AAAA",        "@2B2B2B2B2B2B",        "86"),
                    ("LV", "AAAA",        "B2B2B2B2B2B2@",        "86"),
                    ("MC", "1111122222",  "C3C3C3C3C3C44",        "26"),
                    ("MC", "111112222",   "C3C3C3C3C3C44",        "26"),
                    ("MC", "X111122222",  "C3C3C3C3C3C44",        "26"),
                    ("MC", "1111@22222",  "C3C3C3C3C3C44",        "26"),
                    ("MC", "11111X2222",  "C3C3C3C3C3C44",        "26"),
                    ("MC", "111112222@",  "C3C3C3C3C3C44",        "26"),
                    ("MC", "1111122222",  "@3C3C3C3C3C44",        "26"),
                    ("MC", "1111122222",  "C3C3C3C3C3@44",        "26"),
                    ("MC", "1111122222",  "C3C3C3C3C3CX4",        "26"),
                    ("MC", "1111122222",  "C3C3C3C3C3C4@",        "26"),
                    ("ME", "111",         "222222222222233",      "38"),
                    ("ME", "11",          "222222222222233",      "38"),
                    ("ME", "X11",         "222222222222233",      "38"),
                    ("ME", "11@",         "222222222222233",      "38"),
                    ("ME", "111",         "X22222222222233",      "38"),
                    ("ME", "111",         "222222222222@33",      "38"),
                    ("ME", "111",         "2222222222222X3",      "38"),
                    ("ME", "111",         "22222222222223@",      "38"),
                    ("MK", "111",         "B2B2B2B2B233",         "41"),
                    ("MK", "11",          "B2B2B2B2B233",         "41"),
                    ("MK", "X11",         "B2B2B2B2B233",         "41"),
                    ("MK", "11@",         "B2B2B2B2B233",         "41"),
                    ("MK", "111",         "@2B2B2B2B233",         "41"),
                    ("MK", "111",         "B2B2B2B2B@33",         "41"),
                    ("MK", "111",         "B2B2B2B2B2X3",         "41"),
                    ("MK", "111",         "B2B2B2B2B23@",         "41"),
                    ("MR", "1111122222",  "3333333333344",        "21"),
                    ("MR", "111112222",   "3333333333344",        "21"),
                    ("MR", "X111122222",  "3333333333344",        "21"),
                    ("MR", "1111@22222",  "3333333333344",        "21"),
                    ("MR", "11111X2222",  "3333333333344",        "21"),
                    ("MR", "111112222@",  "3333333333344",        "21"),
                    ("MR", "1111122222",  "X333333333344",        "21"),
                    ("MR", "1111122222",  "3333333333@44",        "21"),
                    ("MR", "1111122222",  "33333333333X4",        "21"),
                    ("MR", "1111122222",  "333333333334@",        "21"),
                    ("MT", "AAAA22222",   "C3C3C3C3C3C3C3C3C3",   "39"),
                    ("MT", "AAAA2222",    "C3C3C3C3C3C3C3C3C3",   "39"),
                    ("MT", "8AAA22222",   "C3C3C3C3C3C3C3C3C3",   "39"),
                    ("MT", "AAA@22222",   "C3C3C3C3C3C3C3C3C3",   "39"),
                    ("MT", "AAAAX2222",   "C3C3C3C3C3C3C3C3C3",   "39"),
                    ("MT", "AAAA2222@",   "C3C3C3C3C3C3C3C3C3",   "39"),
                    ("MT", "AAAA22222",   "@3C3C3C3C3C3C3C3C3",   "39"),
                    ("MT", "AAAA22222",   "C3C3C3C3C3C3C3C3C@",   "39"))
    print_test_data(("MU", "AAAA2222",    "333333333333333DDD",   "37"),
                    ("MU", "AAAA222",     "333333333333333DDD",   "37"),
                    ("MU", "8AAA2222",    "333333333333333DDD",   "37"),
                    ("MU", "AAA@2222",    "333333333333333DDD",   "37"),
                    ("MU", "AAAAX222",    "333333333333333DDD",   "37"),
                    ("MU", "AAAA222@",    "333333333333333DDD",   "37"),
                    ("MU", "AAAA2222",    "X33333333333333DDD",   "37"),
                    ("MU", "AAAA2222",    "33333333333333@DDD",   "37"),
                    ("MU", "AAAA2222",    "3333333333333338DD",   "37"),
                    ("MU", "AAAA2222",    "333333333333333DD@",   "37"),
                    ("NL", "AAAA",        "2222222222",           "57"),
                    ("NL", "AAA",         "2222222222",           "57"),
                    ("NL", "8AAA",        "2222222222",           "57"),
                    ("NL", "AAA@",        "2222222222",           "57"),
                    ("NL", "AAAA",        "X222222222",           "57"),
                    ("NL", "AAAA",        "222222222@",           "57"),
                    ("NO", "1111",        "2222223",              "40"),
                    ("NO", "111",         "2222223",              "40"),
                    ("NO", "X111",        "2222223",              "40"),
                    ("NO", "111@",        "2222223",              "40"),
                    ("NO", "1111",        "X222223",              "40"),
                    ("NO", "1111",        "22222@3",              "40"),
                    ("NO", "1111",        "222222X",              "40"),
                    ("PL", "11111111",    "2222222222222222",     "84"),
                    ("PL", "1111111",     "2222222222222222",     "84"),
                    ("PL", "X1111111",    "2222222222222222",     "84"),
                    ("PL", "1111111@",    "2222222222222222",     "84"),
                    ("PL", "11111111",    "X222222222222222",     "84"),
                    ("PL", "11111111",    "222222222222222@",     "84"),
                    ("PT", "11112222",    "3333333333344",        "59"),
                    ("PT", "1111222",     "3333333333344",        "59"),
                    ("PT", "X1112222",    "3333333333344",        "59"),
                    ("PT", "111@2222",    "3333333333344",        "59"),
                    ("PT", "1111X222",    "3333333333344",        "59"),
                    ("PT", "1111222@",    "3333333333344",        "59"),
                    ("PT", "11112222",    "X333333333344",        "59"),
                    ("PT", "11112222",    "3333333333@44",        "59"),
                    ("PT", "11112222",    "33333333333X4",        "59"),
                    ("PT", "11112222",    "333333333334@",        "59"),
                    ("RO", "AAAA",        "B2B2B2B2B2B2B2B2",     "91"),
                    ("RO", "AAA",         "B2B2B2B2B2B2B2B2",     "91"),
                    ("RO", "8AAA",        "B2B2B2B2B2B2B2B2",     "91"),
                    ("RO", "AAA@",        "B2B2B2B2B2B2B2B2",     "91"),
                    ("RO", "AAAA",        "@2B2B2B2B2B2B2B2",     "91"),
                    ("RO", "AAAA",        "B2B2B2B2B2B2B2B@",     "91"),
                    ("RS", "111",         "222222222222233",      "48"),
                    ("RS", "11",          "222222222222233",      "48"),
                    ("RS", "X11",         "222222222222233",      "48"),
                    ("RS", "11@",         "222222222222233",      "48"),
                    ("RS", "111",         "X22222222222233",      "48"),
                    ("RS", "111",         "222222222222@33",      "48"),
                    ("RS", "111",         "2222222222222X3",      "48"),
                    ("RS", "111",         "22222222222223@",      "48"),
                    ("SA", "11",          "B2B2B2B2B2B2B2B2B2",   "46"),
                    ("SA", "1",           "B2B2B2B2B2B2B2B2B2",   "46"),
                    ("SA", "X1",          "B2B2B2B2B2B2B2B2B2",   "46"),
                    ("SA", "1@",          "B2B2B2B2B2B2B2B2B2",   "46"),
                    ("SA", "11",          "@2B2B2B2B2B2B2B2B2",   "46"),
                    ("SA", "11",          "B2B2B2B2B2B2B2B2B@",   "46"),
                    ("SE", "111",         "22222222222222223",    "32"),
                    ("SE", "11",          "22222222222222223",    "32"),
                    ("SE", "X11",         "22222222222222223",    "32"),
                    ("SE", "11@",         "22222222222222223",    "32"),
                    ("SE", "111",         "X2222222222222223",    "32"),
                    ("SE", "111",         "222222222222222@3",    "32"),
                    ("SE", "111",         "2222222222222222X",    "32"),
                    ("SI", "11111",       "2222222233",           "92"),
                    ("SI", "1111",        "2222222233",           "92"),
                    ("SI", "X1111",       "2222222233",           "92"),
                    ("SI", "1111@",       "2222222233",           "92"),
                    ("SI", "11111",       "X222222233",           "92"),
                    ("SI", "11111",       "2222222@33",           "92"),
                    ("SI", "11111",       "22222222X3",           "92"),
                    ("SI", "11111",       "222222223@",           "92"),
                    ("SK", "1111",        "2222222222222222",     "66"),
                    ("SK", "111",         "2222222222222222",     "66"),
                    ("SK", "X111",        "2222222222222222",     "66"),
                    ("SK", "111@",        "2222222222222222",     "66"),
                    ("SK", "1111",        "X222222222222222",     "66"),
                    ("SK", "1111",        "222222222222222@",     "66"),
                    ("SM", "A2222233333", "D4D4D4D4D4D4",         "71"),
                    ("SM", "A222223333",  "D4D4D4D4D4D4",         "71"),
                    ("SM", "82222233333", "D4D4D4D4D4D4",         "71"),
                    ("SM", "AX222233333", "D4D4D4D4D4D4",         "71"),
                    ("SM", "A2222@33333", "D4D4D4D4D4D4",         "71"),
                    ("SM", "A22222X3333", "D4D4D4D4D4D4",         "71"),
                    ("SM", "A222223333@", "D4D4D4D4D4D4",         "71"),
                    ("SM", "A2222233333", "@4D4D4D4D4D4",         "71"),
                    ("SM", "A2222233333", "D4D4D4D4D4D@",         "71"),
                    ("TN", "11222",       "333333333333344",      "23"),
                    ("TN", "1122",        "333333333333344",      "23"),
                    ("TN", "X1222",       "333333333333344",      "23"),
                    ("TN", "1@222",       "333333333333344",      "23"),
                    ("TN", "11X22",       "333333333333344",      "23"),
                    ("TN", "1122@",       "333333333333344",      "23"),
                    ("TN", "11222",       "X33333333333344",      "23"),
                    ("TN", "11222",       "333333333333@44",      "23"),
                    ("TN", "11222",       "3333333333333X4",      "23"),
                    ("TN", "11222",       "33333333333334@",      "23"),
                    ("TR", "11111",       "BC3C3C3C3C3C3C3C3",    "95"),
                    ("TR", "1111",        "BC3C3C3C3C3C3C3C3",    "95"),
                    ("TR", "X1111",       "BC3C3C3C3C3C3C3C3",    "95"),
                    ("TR", "1111@",       "BC3C3C3C3C3C3C3C3",    "95"),
                    ("TR", "11111",       "@C3C3C3C3C3C3C3C3",    "95"),
                    ("TR", "11111",       "B@3C3C3C3C3C3C3C3",    "95"),
                    ("TR", "11111",       "BC3C3C3C3C3C3C3C@",    "95"),
                    ("DE", "12345678",    "5",                    "06"),
                    ("DE", "12345678",    "16",                   "97"),
                    ("DE", "12345678",    "16",                   "00"),
                    ("DE", "12345678",    "95",                   "98"),
                    ("DE", "12345678",    "95",                   "01"))

# Main program (executed unless imported as module)
if __name__ == "__main__":
    import sys
    if len(sys.argv) == 4:
        print_new_iban(sys.argv[1], sys.argv[2], sys.argv[3])
    elif len(sys.argv) == 2 and sys.argv[1][0] != "-":
        print_iban_parts(sys.argv[1])
    elif "-f" in sys.argv[1:2]:
        print_format()
    elif "-e" in sys.argv[1:2]:
        print_examples()
    elif "-t" in sys.argv[1:2]:
        print_test()
    else:
        print(usage)