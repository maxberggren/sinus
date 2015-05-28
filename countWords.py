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


def count_words_in_region(region, bounding_box):

    urcrnrlon, urcrnrlat, llcrnrlon, llcrnrlat = bounding_box
    
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
    
    print "Räknar ord bland den första procenten"
    try:
        result = db.query("drop table tempwordcounts")
        print "Tog bort tabellen tempwordcounts för att göra rum för nytt."
    except:
        pass
    
    for offset in offsets:
        start = time.time()
        onegrams = Counter() 
        #result = db.query("SELECT text from posts limit "
        #                  ""+str(batch)+" offset " + str(offset))
        
        result = db.query("SELECT blogs.longitude, "
                          "blogs.latitude, "
                          "blogs.rank, "
                          "blogs.id, "
                          "posts.text "
                          "FROM posts INNER JOIN blogs ON "
                          "blogs.id=posts.blog_id "
                          "WHERE blogs.latitude is not NULL "
                          "AND blogs.longitude is not NULL "
                          "AND blogs.rank <= 3 "
                          "AND blogs.longitude > " + str(llcrnrlon) + " "
                          "AND blogs.longitude < " + str(urcrnrlon) + " "
                          "AND blogs.latitude > " + str(llcrnrlat) + " "
                          "AND blogs.latitude < " + str(urcrnrlat) + " "
                          "LIMIT "+ str(batch) +" offset " + str(offset))
        
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
                             ngram=1,
                             region=region))
            
            if i % batch == 0: # Skickar in i DB i batchar
                db['tempwordcounts'].insert_many(rows,
                                             types={'token': varchar})
                rows = []
        
        del onegrams
        remainingBatches = (nPosts - offset)/batch
        print str(100*offset/nPosts)[0:4], "%", "- Tog:", int((time.time() - start)), "sekunder."
    
       
    # Rensa lite
    try:
        result = db.query("CREATE INDEX ind_token ON tempwordcounts(token);")
        print "Index skapades"

    except:
        pass
    try:
        #result = db.query("drop table wordcounts")
        result = db.query("delete from wordcounts WHERE region = '{}'".format(region))
        print "I wordcounttabellen togs rader bort som var av samma typ som de som nu ska in"
    except:
        pass

    print "Databasen räknar ord. Ha tålamod."
    result = db.query("SELECT token, SUM(frequency) as frq "
                      "FROM tempwordcounts "
                      "WHERE region = '" + region + "' "
                      "GROUP BY token")
    i = 0                  
    rows = []
    print "Sparar in slutgiltiga ordfrekvenser" 
    for row in result:
        i += 1
        rows.append(dict(token=row['token'], 
                         frequency=int(row['frq']), 
                         ngram=1,
                         region=region))
        if i % batch == 0:
            db['wordcounts'].insert_many(rows,
                                     types={'token': varchar})
            rows = []

    try:
        result = db.query("CREATE INDEX ind_token ON wordcounts(token);") 
        result = db.query("drop table tempwordcounts")
    except:
        pass
    print "wordcountstabellen är nu populerad med nytt fräscht!"
    
if __name__ == "__main__":

    # Bounding box of Sweden
    llcrnrlon = 8
    llcrnrlat = 54.5
    urcrnrlon = 26
    urcrnrlat = 69.5
    
    count_words_in_region("country", (urcrnrlon, urcrnrlat, llcrnrlon, llcrnrlat))
    count_words_in_region("skaune", (14.653015, 56.256273, 12.551880, 55.349353))
