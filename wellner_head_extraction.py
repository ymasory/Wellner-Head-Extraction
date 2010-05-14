#!/usr/bin/python

# scans through pdtb and ptb concurrently, extracting heads from pdtb arguments, using Wellner 2009 rules
#
# uses auxilliary files pdtb_file_parser.py and apply_head_rules.py
# the script returns one "__ STUCK __" head for an unusual sentence for which the Wellner rules do not work
# the script skips over all NP arguments; Wellner doesn't handle them
#
# @author Yuvi Masory

import glob
import os.path
import getopt
import random
import re
import sys

import apply_head_rules       
import pdtb_file_parser   
from nltk.corpus import BracketParseCorpusReader

# takes in an nltk tree, and an address (e.g., [0,1,0,2], NOT including tree number) and returns the appropriate nltk subtree#
def get_node(tree, address):
    if address == []:
        return tree
    else:
        return get_node(tree[address[0]], address[1:])
    
# takes in a list of argument addresses (e.g., [[22, 0, 1], [23, 0]] INCLUDING tree number), a list of nltk sentence trees for the document, and returns a the appropriate LCA tree #
def make_lca_tree(argAddresses, docSents):
    treeNum = argAddresses[0][0]
    firstTreeAddresses = []
    for address in argAddresses:
        if address[0] == treeNum:
            firstTreeAddresses.append(address)
    treeNum = firstTreeAddresses[0][0]
    if len(firstTreeAddresses) == 1:
        return get_node(docSents[treeNum], firstTreeAddresses[0][1:])
    else:
        for address in firstTreeAddresses:
            if len(address) <= 1:
                # Error in the PDTB
                print 'Skipping sole defective case.'
                return None
        superTree = docSents[treeNum]
        blackTree = blacken_tree(superTree.copy(True), firstTreeAddresses, treeNum)
        prune([blackTree])

        curVert = blackTree

        # descend from the root so the lca tree starts at the lca, not the root of the whole sentence! this hurts overall performance for some reason in tres subtraction application
        hitNP = False;
        while(True):
            if curVert.node.startswith('NP'):
                hitNP = True
            go_on = True;
            for child in curVert:
                if isinstance(child, str):
                    go_on = False
            if go_on:
                if(len(curVert)) == 1:
                    curVert = curVert[0]
                else:
                    break
# this is for demonstration of one of treesubtraction's weaknesses - non-constituent arguments with an NP between the LCA and the root of the sentence
#         if hitNP:
#             print docSents[treeNum]
#             print '#' * 30
#             print blackTree
#             print '#' * 20
#             print curVert
#             raw_input()
#             print '\n'*100

        return curVert

# takes in an nltk tree some of whose nodes (at any depth) have been blackened with None. returns a tree with all the None nodes deleted #
def prune(vertices):
    if len(vertices) == 0:
        return
    newVerts = []
    for vert in vertices:
        if isinstance(vert, str):
            continue
        while None in vert:
            vert.remove(None)
        for child in vert:
            newVerts.append(child)
    prune(newVerts)

# takes in a nltk sentence tree along with a list of argument addresses from the PDTB, returning a nltk tree in which any nodes that won't be in the eventual LCA tree are blackened #
def blacken_tree(superTree, addresses, treeNum):
    blacken_tree_helper(superTree, [treeNum], addresses)
    return superTree

def blacken_tree_helper(vertex, growingAddress, addresses):
    if isinstance(vertex, str):
        return
    for i, vert in enumerate(vertex):
        if listMatches(growingAddress + [i], addresses):
            blacken_tree_helper(vert, growingAddress + [i], addresses)
        else:
            vertex[i] = None

# decides whether lst is a prefix of some list in doubleLst, or whether some list in doubleLst is a prefix of lst #
def listMatches(lst, doubleLst):
    for dl in doubleLst:
        if isPrefix(lst, dl) or isPrefix(dl, lst):
            return True
    return False

def isPrefix(lst1, lst2):
    if len(lst1) > len(lst2):
        return False
    else:
        for i in range(len(lst1)):
            if lst1[i] != lst2[i]:
                return False
        return True

# Wellner states that in multi-clause sequences the head is taken from the first clause, by convention
# It is not clear what algorithm Wellner implements at a lower level, so this is just a reasonable guess
def extract_first_clause(tree):
    stop = False
    goOn = True
    for child in tree:
        if isinstance(child, str):
            goOn = False
    if goOn:
        treeLabs = [child.node for child in tree]
        numS = 0
        numSBAR = 0
        numVP = 0
        numCC = 0
        for tl in treeLabs:
            if re.match(r'S(-.*)*$', tl) != None and '-ADV' not in tl:
                numS = numS + 1
            if re.match(r'SBAR(-.*)*$', tl) != None:
                numSBAR = numSBAR + 1
            if re.match(r'VP(-.*)*$', tl) != None and "TPC" not in tl:
                numVP = numVP + 1
            if re.match(r'CC(-.*)*$', tl) != None or re.match(r'CONJP(-.*)*$', tl) != None:
                        numCC = numCC + 1
        
        # argument is [*[..S..S..]]
        # I do NOT require explicit coordination with CC/CONJP or punctuation
        # I DO require the root to be S. The only other cases are SINV, but they are very few in number and only in one case truly multi-clause
        # The procedure chooses the first S
        if numS > 1:
            if re.match(r'S(-.*)*$', tree.node) != None:
                for child in tree:
                    if re.match(r'S(-.*)*$', child.node) != None and '-ADV' not in child.node:
                        return child

        # argument is [*[..SBAR..SBAR..]]
        # I require explicit coordination with CC/CONJP
        # The procedure chooses the first SBAR
        if numSBAR > 1 and numCC == 0:
            for child in tree:
                if re.match(r'SBAR(-.*)*$', child.node) != None:
                    return child

        # argument is [*[..VP..VP..]]
        # I require explicit coordination with CC/CONJP
        # SINV arguments are excluded as not truly multi-clause
        if numVP > 1 and numCC > 0:
            if not tree.node.startswith("SINV"):
                return tree

        return tree

    else:
        return tree

# prints useful output to stdout
def give_output(tree, fileName, prods, head):
    banner(tree, fileName)
    print_productions(prods, head)

# takes in a list of productions (e.g., ['V', 'S', 'JJ']) and a head (e.g., 'visited') and prints them nicely #
def print_productions(prods, head):
    print 'PRODUCTIONS: ',
    for i in range(0, len(prods)):
        print prods[i] + ' -->',
    if head == '__ STUCK __':
        print '*' * 5 + ' STUCK ' + '*' * 5
    elif head == '__ UNRECOGNIZED __':
        print '*' * 5 + ' UNRECOGNIZED ' + '*' * 5
    elif head == '__ NP __':
        print '*' * 5 + ' NP ' + '*' * 5
    else:
        print head

# nicely prints the full argument tree, the argument text (from PDTB file), the file name, and the entry number within the file #
def banner(tree, fileName):
    print 'File: ' + fileName
    print '#' * 40
    print tree
    print '#' * 40
#     print 'TEXT: ' + argText

# master function
def wellner_head_extraction(docSents, argAddresses):
    treeNum = argAddresses[0][0]
    sentenceTree = docSents[treeNum]
    #-- argument is one vertex only --#
    if len(argAddresses) == 1:
        tree = get_node(sentenceTree, argAddresses[0][1:])
    #-- argument is multiple vertices, including multi-sentence case --#
    else:
        tree = make_lca_tree(argAddresses, docSents)
        if tree == None:
            return (None, None, None)
    #-- multi-clause sequence handling --#
    firstClause = extract_first_clause(tree)
    (prods, head) = apply_head_rules.apply_head_rules(firstClause)
    return (prods, head, firstClause)


def getGalFromString(strgal):
    argAddresses = []
    strgal = strgal.strip('\n')
    if strgal == '':
        return None
    for sa in strgal.split(';'):
        addy = []
        for num in sa.split(','):
            addy.append(int(num))
        argAddresses.append(addy)
    return argAddresses


# fixme this usage of getopt is not correct, it relies on -p coming before the args

usage_str = '''
usage:
python wellner_head_extraction.py input.txt output.txt
python wellner_head_extraction.py -p requests.txt output.txt
'''

def usage():
    print usage_str
    sys.exit(1)

if len(sys.argv) < 3:
    usage()

preprocess = False
try:
    opts, args = getopt.getopt(sys.argv[1:], "ph", [])
except getopt.GetoptError, err:
    # print help information and exit:
    print str(err) # will print something like "option -a not recognized"
    sys.exit(2)
output = None
verbose = False
for o, a in opts:
    if o == "-h":
        print usage_str
        sys.exit(0)
    if o == "-p":
        if len(sys.argv) < 4:
            usage()
        preprocess = True

if preprocess == False:
    inpath = sys.argv[1]
    instring = open(inpath).read()
    inargs = instring.split('\t')

    ptb_path = inargs[0]
    stringAddresses = inargs[1]
    argAddresses = getGalFromString(stringAddresses)
    if argAddresses == None:
        print 'no address provided'
        sys.exit(1)

    docSents = BracketParseCorpusReader(os.path.dirname(ptb_path), os.path.basename(ptb_path)).parsed_sents()
    (prods, head, processedArgTree) = wellner_head_extraction(docSents, argAddresses)
    if prods == None:
        sys.exit(1)
    give_output(processedArgTree, os.path.splitext(os.path.basename(ptb_path))[0], prods, head)

    outfile = open(sys.argv[2], 'w')
    outfile.write(head + '\n')
    outfile.close()

else:
    reqpath = sys.argv[2]
    outpath = sys.argv[3]
    outfile = open(outpath, 'w')

    reqfile = open(reqpath)
    curPtbPath = ""
    docSents = None
    for req in reqfile:
        (ptb_path, goldGalStr, tsGalStr, oneOrTwo) = req.split('\t')
        if ptb_path != curPtbPath:
            docSents = BracketParseCorpusReader(os.path.dirname(ptb_path), os.path.basename(ptb_path)).parsed_sents()
            curPtbPath = ptb_path
        
        outfile.write(ptb_path + "\t")
        
        goldGal = getGalFromString(goldGalStr)
        tsGal = getGalFromString(tsGalStr)
        for gal in (goldGal, tsGal):
            if gal == None:
                outfile.write("__ NONE __")
            else:
                (prods, head, processedArgTree) = wellner_head_extraction(docSents, gal)
                if prods == None:
                    sys.exit(1)
                outfile.write(head)
                # give_output(processedArgTree, os.path.splitext(os.path.basename(ptb_path))[0], prods, head)
            outfile.write("\t")
        if oneOrTwo == 'arg1\n':
            outfile.write('arg1\n')
        elif oneOrTwo == 'arg2\n':
            outfile.write('arg2\n')
        else:
            print 'arg1/2 statement unexpected format'
            sys.exit(1)
        
    outfile.close()

print 'exiting nicely'
