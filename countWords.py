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
    
    
    varchar = sqlalchemy.types.String(length=255)
    warnings.simplefilter("ignore")
    
    db = dataset.connect(c.LOCATIONDB)
    
    batch = 3000
    nPosts = int(24*43131671.0/100.0) 
    offsets = xrange(0, nPosts, batch)
    
    #bigrams = Counter() 
    #trirams = Counter() 
    
    transtab = string.maketrans("ABCDEFGHIJKLMNOPQRSTUVXYZÅÄÖÉ",
                                "abcdefghijklmnopqrstuvxyzåäöé")
    punkter = string.punctuation
    
    print "Räknar ord bland den första procenten i", region
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

    # Coordinates on form: (urcrnrlon, urcrnrlat, llcrnrlon, llcrnrlat)

    # Sweden total    
    count_words_in_region("country", (26, 69.5, 8, 54.5))
    # Skåne
    count_words_in_region("skaune", (14.653015, 56.256273, 12.551880, 55.349353))
    # Norrland
    count_words_in_region("norrland", (25.975690, 69.173527, 12.372609, 62.213702))
    # Småland
    count_words_in_region("smauland", (16.880994, 58.143755, 13.349390, 56.624219))
    # Göteborg
    count_words_in_region("gotlaborg", (13.867365, 59.393105, 11.401765, 56.482094))
    # Mälardalen
    count_words_in_region("malardalen", (18.532594, 59.933278, 14.962038, 58.497572))
    # Mälardalen
    count_words_in_region("finland", (26.971690, 65.189505, 20.643567, 59.497556))
    # Dalarna
    count_words_in_region("dalarna", (16.539451, 61.911557, 12.672264, 60.002842))
    # Dalarna
    count_words_in_region("gotland", (19.593651, 58.081954, 17.739940, 56.724710))

    