#!/usr/bin/python
# -*- coding: utf-8 -*- 
from __future__ import division
#import nltk
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
from textLoc26 import *

RE_NORMAL = re.compile(ur"[a-zA-ZåäöÅÄÖé]")
RE_HIGH = re.compile(ur"[^\u0000-\u00ff]")

LATINIZE_TABLE = dict([
    (unicode(cr.encode('utf-8'), 'latin1'), cr)
    for cr in u"åäöÅÄÖéüÜ"])

RE_LATINIZE = re.compile(ur"|".join(LATINIZE_TABLE.keys()))

def count_normal(s):
    return len(RE_NORMAL.findall(s))

def latinize(s):
    try:
        latinized = unicode(s.encode('latin1'), 'utf-8')
        if count_normal(latinized) > count_normal(s):
            return latinized
    except (UnicodeDecodeError, UnicodeEncodeError):
        pass
    return None

def robertFix(post):
    latinized = latinize(post)
    if latinized != None:
        post = latinized
    else:
        post = RE_LATINIZE.sub(
            lambda m: LATINIZE_TABLE[m.group()], post)
    return post

def maxFix(text):
    if text is None:
        return u""
    else:
        if isinstance(text, unicode):
            return text
        elif isinstance(text, str):
        
            try:
                assumedLatin1 = text.decode('latin-1') # unicode
            except UnicodeDecodeError:
                assumedLatin1 = u""
                
            try:    
                assumedUTF8 = text.decode('utf-8') # unicode
            except UnicodeDecodeError:
                assumedUTF8 = u""
            
            if count_normal(assumedLatin1) > count_normal(assumedUTF8):
                return assumedLatin1
            else:
                return assumedUTF8
        else:
            return u""
            
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
    around = before + [wildcard] + after
    
    for offset in range(1,windowSize+1):
        ngramsAround.append(" ".join(around[nbefore-offset:nbefore+1+offset]))    
    
    return ngramsBefore, ngramsAfter, ngramsAround 
            
def predictViaAPI(text, path="tag"):
    payload = json.dumps({'text': text})
    headers = {'content-type': 'application/json'}
    r = requests.post("http://ext-web.gavagai.se:5001/geotag/api/v1.0/"+path, 
                       data=payload, headers=headers)
    
    return r.json()['meangrammars'] 

        
if __name__ == "__main__":     

    wildcard = "(\S{2,30})"
    databaseuri = c.LOCATIONDB+ "?charset=utf8"
    db = dataset.connect(databaseuri)
    result = db.query("set names 'utf8'")
    
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
        result = db.query("SELECT text FROM posts ORDER by id asc LIMIT 10000")
    
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
    
    regexpes = []
    
    print "### Top 200 ngrams före ort ###"    
    for utterance, frq in ngramsBefore.most_common(top):
        print utterance + " " + wildcard
        regexpes.append(utterance + " " + wildcard)
    
    print "\n### Top 200 ngrams efter ort ###"
    for utterance, frq in ngramsAfter.most_common(top):
        print wildcard + " " + utterance
        regexpes.append(wildcard + " " + utterance)
    
    print "\n### Top 200 ngrams runt ort ###"
    for utterance, frq in ngramsAround.most_common(top):
        print utterance
        regexpes.append(utterance)


    # Now let's check the regexpes
    print len(regexpes)  
    print regexpes
    regexpscores = None
    model = tweetLoc(c.LOCATIONDB, regexpes=regexpes) 
    
    result = db.query("select * from blogs "
                      "WHERE rank <> 9999")
    
    for row in result:
        try:
            blogId = row['id']
            posts = db.query("SELECT * FROM posts WHERE "
                             "blog_id = " + str(blogId) + " limit 200;")
            
            text = u""
            for post in posts:
                text = text + u"\n\n" + maxFix(post['text'])
            
            print "Testar " + row['url'] + "..."
            
            meangrammars = None 
            
            while True: 
                try:
                    #meangrammars = predictViaAPI(text, path="findbestgrammar")
                    meangrammars = model.findBestGrammar(text)

                    break
                except requests.exceptions.ConnectionError:
                    print "Kunde inte koppla mot api:et. Väntar 5 sek." 
                    time.sleep(5)
                    pass
            
            if not regexpscores:
                regexpscores = np.zeros_like(np.array(meangrammars))
            
            regexpscores = regexpscores + np.log10(np.array(meangrammars)+1)
            print regexpscores.astype(int)
            
        except KeyboardInterrupt:
            print "Avslutar"
            break  
 
    