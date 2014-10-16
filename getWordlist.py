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

if __name__ == "__main__":

    batch = 1000
    varchar = sqlalchemy.types.String(length=255)
    warnings.simplefilter("ignore")
    
    db = dataset.connect(c.LOCATIONDB)
    
    #nPosts = 50000
    #nPosts = 43131671
    nPosts = int(float(43131671)/float(100)) # only count a percent
    offsets = xrange(0, nPosts, batch)
    
    #bigrams = Counter() 
    #trirams = Counter() 
    
    transtab = string.maketrans("ABCDEFGHIJKLMNOPQRSTUVXYZÅÄÖÉ",
                                "abcdefghijklmnopqrstuvxyzåäöé")
    punkter = string.punctuation
    
    print "Räknar ord"
    try:
        result = db.query("drop table tempngrams")
        print "Tog bort tabellen tempngrams för att göra rum för nytt."
    except:
        pass
    
    for offset in offsets:
        start = time.time()
        onegrams = Counter() 
        result = db.query("SELECT text from posts limit "
                          ""+str(batch)+" offset " + str(offset))
        
        for row in result:
            words = row['text'].translate(transtab, punkter).split()
            #words = [w.strip() for w in words]
            onegrams.update(words)
            
            #newbigrams = nltk.bigrams(words)
            #newtrigrams = nltk.trigrams(words)
            
            #bigrams.update(newbigrams)
            #trigrams.update(newtrigrams)

        i = 0
        rows = []
        
        for token, frq in onegrams.items():
            i += 1
            rows.append(dict(token=token, 
                             frequency=frq, 
                             ngram=1))
            
            if i % batch == 0: # Skickar in i DB i batchar
                db['tempngrams'].insert_many(rows,
                                             types={'token': varchar})
                rows = []
        
        del onegrams
        remainingBatches = (nPosts - offset)/batch
        print str(100*offset/nPosts)[0:4], "%", "- Tog:", (time.time() - start), "sekunder."
    
       
    # Rensa lite
    try:
        result = db.query("CREATE INDEX ind_token ON tempngrams(token);")
        print "Index skapades"

    except:
        pass
    try:
        result = db.query("drop table ngrams")
        print "Den gamla ngramtabellen togs bort"
    except:
        pass

    print "Databasen räknar ord. Ha tålamod."
    result = db.query("SELECT token, SUM(frequency) as frq "
                      "FROM tempngrams "
                      "GROUP BY token")
    i = 0                  
    rows = []
    print "Sparar in slutgiltiga ordfrekvenser" 
    for row in result:
        i += 1
        rows.append(dict(token=row['token'], 
                         frequency=int(row['frq']), 
                         ngram=1))
        if i % batch == 0:
            db['ngrams'].insert_many(rows,
                                     types={'token': varchar})
            rows = []

    try:
        result = db.query("CREATE INDEX ind_token ON ngrams(token);") 
        result = db.query("drop table tempngrams")
    except:
        pass
    print "Ngramtabellen är nu populerad med nytt fräscht!"