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
    
    for offset in range(windowSize):
        try:
            before = words[around-windowSize+offset:around]
            break
        except KeyError:
            pass   
            
    ngramsbefore = []
    
    for offset in range(len(before)):
        ngramsbefore.append(" ".join(before[offset:]))
    
    for offset in range(windowSize):
        try:
            after = words[around+1:1+around+windowSize-offset]
            break
        except KeyError:
            pass 
            
    ngramsafter = []
    
    for offset in range(len(after)):
        ngramsafter.append(" ".join(after[:-offset]))
    
    return ngramsbefore, ngramsafter
        
        
if __name__ == "__main__":     

    # Add all Swedish villages/citys to a set
    o = Set()
    f = codecs.open("orter.txt", encoding="utf-8")
    for line in f:
        o.add(line.lower().strip())
        
    transtab = string.maketrans("ABCDEFGHIJKLMNOPQRSTUVXYZÅÄÖÉ",
                                "abcdefghijklmnopqrstuvxyzåäöé")
    punkter = string.punctuation
    db = dataset.connect("sqlite:///nattstad.db")
    
    start = time.time()
    
    ngramsB = Counter() # Ngrams before
    ngramsA = Counter() # Ngrams after
    
    result = db.query("SELECT * FROM blogs WHERE LENGTH(presentation) > 1 "
                      "AND manuellStad is NULL order by id asc")
    
    for row in result:
        words = row['presentation'].encode('utf-8').translate(transtab, punkter).split()
        for i, word in enumerate(words):
            if word in o:
                before, after = window(words, i, 6)
                ngramsB.update(before)
                ngramsA.update(after)
        
    top = 200    
    
    print "### Top 200 ngrams före ort ###"    
    for utterance, frq in ngramsB.most_common(top):
        print utterance
    
    print "\n### Top 200 ngrams efter ort ###"
    for utterance, frq in ngramsA.most_common(top):
        print utterance
