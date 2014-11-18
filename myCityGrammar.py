#!/usr/bin/python
# -*- coding: utf-8 -*- 
from __future__ import division
import nltk
import dataset
import re
import numpy as np
from collections import Counter
import time
import string 
import sqlalchemy
import warnings
import config as c
from sets import Set
import codecs

def window(words, around, windowSize):
    """ Give a window of items around an item in a list 
        E.g window(['i', 'love', 'cats', 'omg'], 2, 2)
        gives ['i', 'love'], ['omg']
        i.e. one list before the item and one after. 
    """
    ngramsBefore = []
    ngramsAfter = []
    ngramsAround = []
    
    # Before
    for offset in range(windowSize):
        try:
            before = words[around-windowSize+offset:around]
            break
        except KeyError:
            pass   
    
    for offset in range(len(before)):
        ngramsBefore.append(" ".join(before[offset:]))
    
    # After
    for offset in range(windowSize):
        try:
            after = words[around+1:1+around+windowSize-offset]
            break
        except KeyError:
            pass 
    
    for offset in range(len(after)):
        ngramsAfter.append(" ".join(after[:-offset]))
    
    
    # Around
    nafter = len(after)
    nbefore = len(before)
    around = before + ['**PLATS**'] + after
    
    for offset in range(1,windowSize+1):
        ngramsAround.append(" ".join(around[nbefore-offset:nbefore+1+offset]))    
    
    return ngramsBefore, ngramsAfter, ngramsAround
        
        
if __name__ == "__main__":     

    databaseuri = c.LOCATIONDB+ "?charset=utf8"
    #databaseuri = "sqlite:///nattstad.db"

    # Add all Swedish villages/citys to a set
    o = Set()
    f = codecs.open("orter.txt", encoding="utf-8")
    for line in f:
        o.add(line.lower().strip())
        
    transtab = string.maketrans("ABCDEFGHIJKLMNOPQRSTUVXYZÅÄÖÉ",
                                "abcdefghijklmnopqrstuvxyzåäöé")
    punkter = string.punctuation
    db = dataset.connect(databaseuri)
    
    start = time.time()
    
    ngramsBefore = Counter() # Ngrams before
    ngramsAfter = Counter() # Ngrams after
    ngramsAround = Counter() # Ngrams around
    
    if "nattstad" in databaseuri:
        result = db.query("SELECT * FROM blogs WHERE LENGTH(presentation) > 1 "
                          "AND manuellStad is NULL order by id asc")
    else:
        result = db.query("SELECT text FROM posts ORDER by id asc LIMIT 1000000")
    
    for row in result:
        if "nattstad" in databaseuri:
            words = row['presentation'].encode('utf-8').translate(transtab, punkter).split()
        else:
            words = row['text'].encode('utf-8').translate(transtab, punkter).split()

        for i, word in enumerate(words):
            if word in o:
                before, after, around = window(words, i, 6)
                ngramsBefore.update(before)
                ngramsAfter.update(after)
                ngramsAround.update(around)
        
    top = 200    
    
    print "### Top 200 ngrams före ort ###"    
    for utterance, frq in ngramsBefore.most_common(top):
        print utterance + " **PLATS**"
    
    print "\n### Top 200 ngrams efter ort ###"
    for utterance, frq in ngramsAfter.most_common(top):
        print "**PLATS** " + utterance
    
    print "\n### Top 200 ngrams runt ort ###"
    for utterance, frq in ngramsAround.most_common(top):
        print utterance
