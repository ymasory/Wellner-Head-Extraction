#!/usr/bin/python

# parses pdtb annotations
# @author Yuvi Masory

import glob
import re
import sys

entryPattern = r'________________________________________________________.*?____(.*?)____.*?____Arg1____\n(.*?)\n(.*?)\n.*?#### Text ####\n(.*?)\n##############.*?____Arg2____\n(.*?)\n(.*?)\n.*?#### Text ####\n(.*?)\n##############.*?________________________________________________________'

def parse(path):
    doc = open(path).read()
    entries = re.findall(entryPattern, doc, re.DOTALL)
    assert len(entries) > 0
    docEntries = []
    for entry in entries:
        conType = entry[0]
        assert conType in ('Explicit', 'Implicit', 'EntRel', 'AltLex', 'NoRel')
        arg1SpansTmp = re.split(r';', entry[1])
        arg1Spans = []
        for sp in arg1SpansTmp:
            arg1Spans.append(re.split(r'\.\.', sp))
        arg2SpansTmp = re.split(r';', entry[4])
        arg2Spans = []
        for sp in arg2SpansTmp:
            arg2Spans.append(re.split(r'\.\.', sp))
        arg1NodesTmp = re.split(r';', entry[2])
        arg1Nodes = []
        for sp in arg1NodesTmp:
            arg1Nodes.append(re.split(r',', sp))
        arg2NodesTmp = re.split(r';', entry[5])
        arg2Nodes = []
        for sp in arg2NodesTmp:
            arg2Nodes.append(re.split(r',', sp))

        # convert everything to ints
        for spanList in (arg1Spans, arg2Spans):
            for span in spanList:
                span[0] = int(span[0])
                span[1] = int(span[1])
        for nodeList in (arg1Nodes, arg2Nodes):
            for nl in nodeList:
                for i in range(len(nl)):
                    nl[i] = int(nl[i])

        arg1Text = entry[3]
        arg2Text = entry[6]

        docEntries.append((conType, arg1Spans, arg1Nodes, arg1Text, arg2Spans, arg2Nodes, arg2Text))
    return docEntries
