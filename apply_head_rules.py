#!/usr/bin/python

# returns the head of an argument represented as a set of non-overlapping subtrees, using the head identification rules in Wellner 2009
# @author Yuvi Masory

import re
import sys

# Table 4.1 from Wellner (2009), page 60
# Q: Does the -PRD have to be at the end to match? Assuming not.
# Q: There needs to be an NP rule!
# Q: Prefix problem, JJS will match JJ, etc., rewrite regexps to only tolerate - and = after tag
# Q: Are there any gold standard heads to compare this algorithm to?
rules = [
[r'^ADJP([-=].*)*$', '<', [r'^NNS([-=].*)*$', r'^QP([-=].*)*$', r'^NN([-=].*)*$', r'^\$', r'^ADVP([-=].*)*$', r'^JJ([-=].*)*$', r'^VBN([-=].*)*$', r'^VBG([-=].*)*$', r'^ADJP([-=].*)*$', r'^JJR([-=].*)*$', r'^NP([-=].*)*$', r'^JJS([-=].*)*$', r'^DT([-=].*)*$', r'^FW([-=].*)*$', r'^RBR([-=].*)*$', r'^RBS([-=].*)*$', r'^SBAR([-=].*)*$', r'^RB([-=].*)*$']],
[r'^ADVP([-=].*)*$', '>', [r'^RB([-=].*)*$', r'^RBR([-=].*)*$', r'^RBS([-=].*)*$', r'^FW([-=].*)*$', r'^ADVP([-=].*)*$', r'^TO([-=].*)*$', r'^CD([-=].*)*$', r'^JJR([-=].*)*$', r'^JJS([-=].*)*$', r'^IN([-=].*)*$', r'^NP([-=].*)*$', r'^JJS([-=].*)*$', r'^NN([-=].*)*$']],
[r'^CONJP([-=].*)*$', '>', [r'^CC([-=].*)*$', r'^RB([-=].*)*$', r'^IN([-=].*)*$']],
[r'^FRAG', '>', [r'^NN([-=].*)*$|^NP([-=].*)*$', r'^W.*', r'^SBAR([-=].*)*$', r'^PP([-=].*)*$|^IN([-=].*)*$', r'^ADJP([-=].*)*$|^JJ([-=].*)*$', r'^ADVP([-=].*)*$', r'^PP([-=].*)*$']],
[r'^INTJ([-=].*)*$', '<', [r'.*']],
[r'^LST([-=].*)*$', '>', [r'^LS([-=].*)*$', r'^:']],
[r'^NAC([-=].*)*$', '<', [r'^NN([-=].*)*$', r'^NP([-=].*)*$', r'^NAC([-=].*)*$', r'^EX([-=].*)*$', r'^\$', r'^CD([-=].*)*$', r'^QP([-=].*)*$', r'^PRP([-=].*)*$', r'^VBG([-=].*)*$', r'^JJ([-=].*)*$', r'^JJS([-=].*)*$', r'^JJR([-=].*)*$', r'^ADJP([-=].*)*$', r'^FW([-=].*)*$']],
[r'^PP([-=].*)*$', '>', [r'^IN([-=].*)*$', r'^TO([-=].*)*$', r'^VBG([-=].*)*$', r'^VBN([-=].*)*$', r'^RP([-=].*)*$', r'^FW([-=].*)*$']],
[r'^WHPP([-=].*)*$', '>', [r'^IN([-=].*)*$', r'^TO([-=].*)*$', r'^VBG([-=].*)*$', r'^VBN([-=].*)*$', r'^RP([-=].*)*$', r'^FW([-=].*)*$']],
[r'^PRN([-=].*)*$', '>', [r'^S.*', r'^N.*', r'^W.*', r'^PP([-=].*)*$|^IN([-=].*)*$', r'^ADJP([-=].*)*$|^JJ([-=].*)*$', r'^ADVP([-=].*)*$|^RB([-=].*)*$']],
[r'^PRT([-=].*)*$', '>', [r'^RP([-=].*)*$']],
[r'^QP([-=].*)*$', '<', [r'^\$|^IN([-=].*)*$|^NNS([-=].*)*$|^NN([-=].*)*$|^JJ([-=].*)*$|^RB([-=].*)*$|^DT([-=].*)*$|^CD([-=].*)*$|^NCD([-=].*)*$|^QP([-=].*)*$|^JJR([-=].*)*$|^JJS([-=].*)*$']],
[r'^RRC([-=].*)*$', '>', [r'^VP([-=].*)*$', r'^NP([-=].*)*$', r'^ADVP([-=].*)*$', r'^ADJP([-=].*)*$', r'^PP([-=].*)*$']],
[r'^S([-=].*)*$', '>', [r'^VP([-=].*)*$', r'.*-PRD([-=].*)*$', r'^S([-=].*)*$', r'^SBAR([-=].*)*$', r'^ADJP([-=].*)*$', r'^UCP([-=].*)*$', r'^NP([-=].*)*$', r'^FRAG([-=].*)*$', r'^SINV([-=].*)*$', r'^PP([-=].*)*$']],
[r'^SBAR([-=].*)*$', '>', [r'^S([-=].*)*$', r'^SQ([-=].*)*$', r'^SINV([-=].*)*$', r'^SBAR([-=].*)*$', r'^FRAG([-=].*)*$', r'^IN([-=].*)*$', r'^DT([-=].*)*$']],
[r'^SBARQ([-=].*)*$', '>', [r'^SW([-=].*)*$', r'^S([-=].*)*$', r'^SINV([-=].*)*$', r'^SBARW([-=].*)*$', r'^FRAG([-=].*)*$', r'^VP([-=].*)*$']],
[r'^SINV([-=].*)*$', '>', [r'^VBZ([-=].*)*$', r'^VBD([-=].*)*$', r'^VBP([-=].*)*$', r'^VB([-=].*)*$', r'^MD([-=].*)*$', r'.*-PRD([-=].*)*$', r'^VP([-=].*)*$', r'^SQ([-=].*)*$', r'^FRAG([-=].*)*$', r'^S([-=].*)*$', r'^SINV([-=].*)*$', r'^SBAR([-=].*)*$', r'^SBARQ([-=].*)*$']],
[r'^SQ([-=].*)*$', '>', [r'^VBZ([-=].*)*$', r'^VBD([-=].*)*$', r'^VBP([-=].*)*$', r'^VB([-=].*)*$', r'^MD([-=].*)*$', r'.*-PRD([-=].*)*$', r'^VP([-=].*)*$', r'^SQ([-=].*)*$', r'^FRAG([-=].*)*$', r'^S([-=].*)*$', r'^SINV([-=].*)*$', r'^SBAR([-=].*)*$', r'^SBARQ([-=].*)*$']],
[r'^UCP([-=].*)*$', '>', [r'.*']],
[r'^VP([-=].*)*$', '>', [r'^VBD([-=].*)*$', r'^VBN([-=].*)*$', r'^MD([-=].*)*$', r'^VBZ([-=].*)*$', r'^VB([-=].*)*$', r'^VBG([-=].*)*$', r'^VBP([-=].*)*$', r'^VP([-=].*)*$', r'.*-PRD([-=].*)*$', r'^ADJP([-=].*)*$', r'^NN([-=].*)*$', r'^NNS([-=].*)*$', r'^NP([-=].*)*$', r'^S([-=].*)*$', r'^SINV([-=].*)*$', r'^SBAR([-=].*)*$', r'^SBARQ([-=].*)*$', r'^SQ([-=].*)*$']],
[r'^WHADJP([-=].*)*$', '<', [r'^CC([-=].*)*$', r'^WRB([-=].*)*$', r'^JJ([-=].*)*$', r'^ADJP([-=].*)*$',]],
[r'^WHADVP([-=].*)*$', '>', [r'^CC([-=].*)*$', r'^WRB([-=].*)*$']],
[r'^WHNP([-=].*)*$', '<', [r'^NN([-=].*)*$', r'^WDT([-=].*)*$', r'^WP.*', r'^WHADJP([-=].*)*$', r'^WHPP([-=].*)*$', r'^WHNP([-=].*)*$']],
[r'^X([-=].*)*$', '<', [r'.*']]
]

def apply_head_rules(vertex):
    return apply_head_rules_helper(vertex, [])

def apply_head_rules_helper(vertex, productions):
    productions.append(vertex.node)
    if isinstance(vertex[0], str):
        return (productions, vertex[0])
    matchedSomething = False
    for rule in rules:
        curLabel = rule[0]
        direction = rule[1]
        opts = rule[2]
        if re.match(curLabel, vertex.node) != None:
            matchedSomething = True
            for opt in opts:
                if direction == '>':
                    for i in range(0, len(vertex)):
                        if re.match(opt, vertex[i].node) != None:
                            return apply_head_rules_helper(vertex[i], productions)
                else:
                    for i in range(len(vertex) - 1, -1, -1):
                        if re.match(opt, vertex[i].node) != None:
                            return apply_head_rules_helper(vertex[i], productions)
            if direction == '>':
                for i in range(0, len(vertex)):
                    if vertex[i].node not in ('.', ',', ':', '$', '#', "''", '``', '-LRB-', '-RRB-'):
                        return apply_head_rules_helper(vertex[i], productions)
            else:
                for i in range(len(vertex) - 1, -1, -1):
                    if vertex[i].node not in ('.', ',', ':', '$', '#', "''", '``', '-LRB-', '-RRB-'):
                        return apply_head_rules_helper(vertex[i], productions)

    # Left hand matched but not right hand side
    if matchedSomething:
        return (productions, '__ STUCK __')
    # Left hand not even recognized
    else:
        if vertex.node == 'NP' or re.match(r'NP[-=].*', vertex.node) != None:
            return (productions, '__ NP __')
        else:
            return (productions, '__ UNRECOGNIZED __')
