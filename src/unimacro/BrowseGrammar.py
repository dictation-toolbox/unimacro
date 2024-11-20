# (unimacro - natlink macro wrapper/extensions)
# (c) copyright 2003 Quintijn Hoogenboom (quintijn@users.sourceforge.net)
#                    Ben Staniford (ben_staniford@users.sourceforge.net)
#                    Bart Jan van Os (bjvo@users.sourceforge.net)
#
# This file is part of a SourceForge project called "unimacro" see
# http://unimacro.SourceForge.net).
#
# "unimacro" is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License, see:
# http://www.gnu.org/licenses/gpl.txt
#
# "unimacro" is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; See the GNU General Public License details.
#
# "unimacro" makes use of another SourceForge project "natlink",
# which has the following copyright notice:
#
# Python Macro Language for Dragon NaturallySpeaking
#   (c) Copyright 1999 by Joel Gould
#   Portions (c) Copyright 1999 by Dragon Systems, Inc.
# 
# Python Macro Language for Dragon NaturallySpeaking
#   (c) Copyright 1999 by Joel Gould
#   Portions (c) Copyright 1999 by Dragon Systems, Inc.
#

# This file implements a base classes for a dialog/window to browse NatLink grammars
# The browser is based upon a tree dialog, adapted from the hiertest demo
# Author: Bart Jan van Os, Version: 1.0

# The quality of the code is unsatisfactory.
# . One of the issues is that possibly too many copies of some items are made.
# . Some of the identifiers are misleading names
# . The GrammarElement class should be partitioned into several subclasses.
#   (By now, I know how it should have been done)
# . Only one dictionary can be defined for a rule. If you need more you need
#   to split the rule into subrules.
"""This file implements a base classes for a dialog/window to browse
NatLink grammars

The browser is based upon a tree dialog, adapted from the hiertest demo
"""

import os
import copy
import re
import types
from natlinkcore import natlinkutils
from natlinkcore import gramparser  # for splitApartLines

ListCode = 0    # List
SeqCode = 1     # sequence
AltCode = 2     # alternative
RepCode = 3     # repeat
OptCode = 4     # optional
RuleCode = 5    # Rule
StartForCode='{ (([<'
EndForCode=  '} ))];'
MaxUnfoldLen=40



def IsText(value):
    return isinstance(value, str)

def GrammarElementKey(item):
    if type(item) == str:
        return item.lower()
    return item.GetName().lower()
    

class GrammarElement:

    def Init(self,GramType,Name):
        self.GramType=GramType
        self.Included=[]
        self.Name=Name
        self.ObjIncluded=0
        self.IsLA=0
        self.AlternativesDict={}

    def SetAlternativesDict(self,AlternativesDict):
        if self.AreAlternatives():
            self.AlternativesDict=AlternativesDict

    def Append(self,NewElement):
        self.Included.append(NewElement)
        self.ObjIncluded=self.ObjIncluded or not IsText(NewElement)
        pass        

    def Insert(self,NewElement):
        self.Included.insert(0,NewElement)
        self.ObjIncluded=self.ObjIncluded or not IsText(NewElement)
        pass
    def Sort(self):
        self.Included.sort(key=GrammarElementKey)
        pass
    
    def SetToAllText(self,Text):
        AllText = [str(t) for t in Text]
        self.Included=AllText
        self.ObjIncluded=0

    def SetIsAllText(self):
        if self.ObjIncluded:
            for x in self.Included:
                if not IsText(x): return
        self.ObjIncluded=0

    def GetName(self):
        if self.Name!='':
            if self.GramType==RuleCode:
                if self.IsRuleContainer():
                    return self.Name
                else:
                    return '<'+self.Name+'>'
            elif self.GramType==ListCode:
                return '{'+self.Name+'}'                
            else:
                return self.Name
        else:
            return ''


    def AreAllWordsOrLists(self,contents=''):
        if contents=='':
            contents=self.GetAllIncluded(1,Unfold=0)
        return (not '<' in contents)

    def AreAllWords(self,contents=''): #might be combination of seq and alt
        if not self.ObjIncluded: return 1
        if contents=='':
            contents=self.GetAllIncluded(1,Unfold=0)
        return (not '<' in contents) and (not '{' in contents)

    def IsAllText(self):
        if self.ObjIncluded: return False
        if len(self.Included)>0:
            # print 'IsAllText: %s'% self.Included
            return True
        return False

    def IsInnerRule(self):
        return self.GramType==ListCode or self.GramType==RuleCode or self.IsLongAlternative()

    def IsRuleContainer(self):
        for x in self.Included:
            if (IsText(x)) or x.GramType!=RuleCode: return 0
        return 1

    def IsAltOrList(self):
        return (self.GramType==ListCode) or self.IsLongAlternative()


    def AreAlternatives(self):
        return (self.GramType==AltCode) or (self.GramType==ListCode)

    def SetIsLongAlternative(self):
        if self.GramType==AltCode:
            self.IsLA=self.IsAllText() and (len(u' | '.join(self.Included))>MaxUnfoldLen)
            if not self.IsLA and (self.AlternativesDict!={}):
                count=0
                for x in self.Included:
                    if x in self.AlternativesDict:
                        count += 1
                self.IsLA=self.IsLA or ((1.0*count/len(self.Included))>0.45)
        else:
            self.IsLA=0

    def IsLongAlternative(self):
        return self.IsLA

    def FoldLongAlternatives(self,a):
        #Called once, after parsing and creating the Grammar Elements
        self.SetIsLongAlternative()
        if self.IsLongAlternative():
            a=a+1
            if a==1:
                self.Name='<alternatives>'
            else:
                self.Name='<alternatives'+str(a)+'>'
        else:
            for x in self.Included:
                if not IsText(x):
                    x.FoldLongAlternatives(a)

    def FillInRules(self,DefRules,UsedRules):
        #Called once, after parsing and creating the Grammar Elements
        #Replaces rule references by full Rule objects
        for x in self.Included:
            if not IsText(x):
                if x.GramType==RuleCode:
                    i=self.Included.index(x)
                    if x.Name in DefRules:
                        self.Included[i]=DefRules[x.Name]
                        if not x.Name in UsedRules:
                            UsedRules.append(x.Name)
                else:
                    x.FillInRules(DefRules,UsedRules)



    def GetAllInnerRules(self,maxLevel,InnerRules):
        for x in self.Included:
            if not IsText(x):
                if x.GramType==RuleCode:
                    InnerRules.append(x)
                    if maxLevel>0:
                        x.GetAllInnerRules(maxLevel-1,InnerRules)
                elif x.IsAltOrList():
                    InnerRules.append(x)
                else:
                    x.GetAllInnerRules(maxLevel,InnerRules)

    def RemoveDuplicates(self,AllRules):
#        AllNames = map(lambda x: x.Name,AllRules) # my first map and lambda; alas! no longer needed :-)
        Rules=[]
        RuleNames=[]
        for x in AllRules:
            if not (x in Rules or x.GetName() in RuleNames):
                    Rules.append(x)
                    RuleNames.append(x.GetName())
        return Rules

    def GetInnerRules(self,maxLevel):
        InnerRules=[]
        self.GetAllInnerRules(maxLevel,InnerRules)
        InnerRules=self.RemoveDuplicates(InnerRules)
        return InnerRules


    def GetIncluded(self,i,maxLevel,Unfold):
        try:
            x=self.Included[i]
            if IsText(x):
                return x
            else:
                return x.GetContents(maxLevel-(x.GramType==RuleCode),Unfold)
        except:
            return ''

    def ReduceLongAlternatives(self,contents):
        if len(contents)>MaxUnfoldLen:
            p=contents[MaxUnfoldLen:].find('|')
            contents=contents[:MaxUnfoldLen+p]+',...'
        return contents

    def GetAllIncluded(self,maxLevel,Unfold):
        if len(self.Included)==0:
            if (self.GramType==ListCode):
                contents='???'
            else:
                contents=''
        # this if clause gives a significant speedup for long lists                
        elif not self.ObjIncluded:
            if (not Unfold) and self.IsLongAlternative():
                contents=self.Name
            else:
                if (self.GramType==AltCode) or (self.GramType==ListCode):
                    contents=u' | '.join(self.Included)
                else:
                    contents=u' '.join(self.Included)
                contents=self.ReduceLongAlternatives(contents)
        else:
            contents=self.GetIncluded(0,maxLevel,Unfold)
            for i in range(1,len(self.Included)):
                if self.AreAlternatives():
                    contents=contents+' | '+self.GetIncluded(i,maxLevel,Unfold)
                else:
                    contents=contents+' '+self.GetIncluded(i,maxLevel,Unfold)
            if self.IsLongAlternative():
                contents=self.ReduceLongAlternatives(contents)
        return contents

    def GetContents(self,maxLevel,Unfold=0):
        #Unfold controls forced unfolding of alternatives
        #max Level controls the deepness of rule unfolding, 0=rulename;1=innerule names
        #beyond the max Level, Unfold tries to unfold short rules more levels
        includedContents=self.GetAllIncluded(maxLevel,Unfold)        
        if self.GramType!=RuleCode:
            contents=StartForCode[self.GramType]
            if (self.GramType==ListCode) and not Unfold:
                contents= contents+self.Name
            else:
                contents=contents+includedContents
            c=contents=contents+EndForCode[self.GramType]
            if self.GramType==RepCode:
                if len(c)>3: # try to remove redundant parens
                    Remove=c[1]=='{' and (c[-2]=='}') and (not '{' in c[2:-2])
                    Remove=Remove or (c[1]=='[' and (c[-2]==']') and (not ']' in c[2:-2]))
                    if Remove: contents=contents[1:-1]
                contents=contents+'+'
        else:
            contents= '<'+self.Name
            if (maxLevel<=0):
                if (Unfold): #Try to go deeper one level at a time, until too long
                    l=maxLevel
                    NiC=self.GetAllIncluded(l,0)
                    includedContents=''
                    while (len(NiC)< MaxUnfoldLen) and (includedContents!=NiC):
                        l=l+1
                        includedContents=NiC
                        NiC=self.GetAllIncluded(l,0)
                    if l==maxLevel:
                        contents=contents+'>'
                    else:
                        contents=includedContents
                else:
                    contents=contents+'>'
            else:
                contents=includedContents+';'
        return contents

    def GetTextChunks(self):
        #Gets all Text included that is not included in Inner Rules
        #(+lists+alternatives)
        Chunks=[]
        for x in self.Included:
            if IsText(x):
                i=self.Included.index(x)
                PreviousWasText=(i>0) and IsText(self.Included[i-1])
                if (self.GramType==SeqCode) and PreviousWasText:
                    Chunks[-1]=Chunks[-1]+' '+x
                else:
                    Chunks.append(x)
            elif x.IsAllText():
                Chunks.extend(x.Included)
            else:
                if not x.IsInnerRule():
                    Chunks.extend(x.GetTextChunks())
        return Chunks


    def FindLargestRulePath(self,Rules):
        largestPath=[]
        objPath=[]
        for r in self.Included:
            if not IsText(r):
                newobjPath=[r]
                if r.Name in Rules:
                    newPath=[r.Name]
                    newRules=copy.copy(Rules)
                    del newRules[Rules.index(r.Name)]
                    if len(newRules)==0:
                        return newPath,newobjPath
                    else:
                        n,o=r.FindLargestRulePath(newRules)
                        newPath.extend(n)
                        newobjPath.extend(o)
                        if len(newPath)>len(largestPath):
                            largestPath=newPath
                            objPath=newobjPath
                else:
                    newPath,o=r.FindLargestRulePath(Rules)
                    newobjPath.extend(o)
                    if len(newPath)>len(largestPath):
                        largestPath=newPath
                        objPath=newobjPath
        return largestPath,objPath
    

    def FindRulePath(self,Start):
        if self.IsRuleContainer():
            for x in self.Included:
                if x.Name==Start[0]:
                    #We should actually search for the largest Tree,
                    #but this is sufficient for most cases
                    Path,objPath=x.FindLargestRulePath(Start[1])
                    objPath.insert(0,x)
                    return x,Path,objPath
        return None,[],[]

# def caseIndependentSort(something, other):
#     something, other= repr(something).lower(),repr(other).lower()
#     return cmp(something, other)

def RemoveDuplicatesOfSortedList(List):
    for i in range(len(List)-1,-1,-1):
        if i>0:
            if List[i]==List[i-1]: del List[i]    

def InverseDict(SomeDict):
    InverseDict={}
    for key in SomeDict.keys():
        InverseDict[SomeDict[key]]=key
    return InverseDict

def ParseRuleDefinitions(name,stack,Parser,ParserInfo,Lists,Dicts):
    KnownWords,KnownRules,KnownLists,ImportRules=ParserInfo
    CurElement=GrammarElement()
    CurElement.Init(RuleCode,name)
    stack.insert(0,CurElement)
    for element in Parser.ruleDefines[name]:
        if element[0]=='start':
            NewElement=GrammarElement()
            NewElement.Init(element[1],'')
            if (element[1]==AltCode) and name in Dicts:
                NewElement.SetAlternativesDict(Dicts[name])
            CurElement.Append(NewElement)
            CurElement=NewElement
            stack.insert(0,CurElement)
        elif element[0]=='rule':
            NewElement=GrammarElement()
            RuleName=KnownRules[element[1]]
            NewElement.Init(RuleCode,RuleName)
            if RuleName in ImportRules:
                NewElement.Append('<imported>')
            CurElement.Append(NewElement)
        elif element[0]=='list':
            NewElement=GrammarElement()
            ListName=KnownLists[element[1]]
            NewElement.Init(ListCode,ListName)
            if ListName in Dicts:
                NewElement.SetAlternativesDict(Dicts[ListName])
            if ListName in Lists:
                NewElement.SetToAllText(Lists[ListName])
            CurElement.Append(NewElement)
        elif element[0]=='end':
            #Pack simple text sequences into parent list as multi word item in Included
            if CurElement.IsAllText() and (CurElement.GramType==SeqCode):
                    stack[1].Included[-1]=u' '.join(CurElement.Included)
            else: #make shure object is not turned into AllText
                CurElement.SetIsAllText()
            del stack[0]
            CurElement=stack[0]
        elif element[0]=='word':
            CurElement.Append(KnownWords[element[1]])

# def checkForBinary(line):
#     """ helper for converting to Binary
#     """
#     if type(line) == bytes:
#         return line
#     elif type(line) == str:
#         return utilsqh.convertToBinary(line)
#     else:
#         raise ValueError("BrowseGrammar, checkForBinary should have binary or unicode as input, not: %s (%s)"% (line, type(line)))
# 

def ParseGrammarDefinitions(gramSpec,gramName,Lists,Dicts,activeRules,All=1, Exclusive=0,
                            exclusiveState=0):
    if type(gramSpec)!=type([]): gramSpec=[gramSpec]    
    gramparser.splitApartLines(gramSpec)
##    Parser = natlinkutils.GramParser(gramSpec)
##    Parser.doParse()
    # with gramparserlexyacc:
    Parser = gramparser.GramParser(gramSpec)
    # print '%s, type gramSpec: %s, '% (gramName, type(gramSpec))
    # if type(gramSpec) == list:
    #     gramSpec = [checkForBinary(g) for g in gramSpec]
    Parser.doParse()
    ParserInfo=(InverseDict(Parser.knownWords),InverseDict(Parser.knownRules),
        InverseDict(Parser.knownLists),Parser.importRules)
    stack=[]        
    for name in Parser.ruleDefines.keys():
        ParseRuleDefinitions(name,stack,Parser,ParserInfo,Lists,Dicts)
    DefRules={}                
    for x in stack:
        DefRules[x.Name]=x
    UsedRules=[]
    for x in stack:
        x.FillInRules(DefRules,UsedRules)
        x.FoldLongAlternatives(0)
    Grammar=GrammarElement()
    Grammar.Init(RuleCode,gramName)
    if Exclusive:
        if not exclusiveState:
            return
        # if asking for exclusive, only show the activerules
        All = 0
            
    if All:
        Obsolete=GrammarElement()
        Obsolete.Init(RuleCode,'Obsolete')
        for rule in stack:
            if rule.Name in Parser.exportRules:
                Grammar.Insert(rule)
            elif not rule.Name in UsedRules:
                Obsolete.Insert(rule)
        if len(Obsolete.Included)!=0: Grammar.Append(Obsolete)
    elif activeRules:
        for rule in stack:
            if (rule.Name in activeRules):
                Grammar.Insert(rule)
    else:
        return   # nothing if no active rules QH
    return Grammar
