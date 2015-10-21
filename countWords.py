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

db = dataset.connect(c.LOCATIONDB)

def count_words_in_region(region, bounding_box, percent=50):

    urcrnrlon, urcrnrlat, llcrnrlon, llcrnrlat = bounding_box
    
    
    varchar = sqlalchemy.types.String(length=255)
    warnings.simplefilter("ignore")

    # Find number of documents
    result = db.query("SELECT count(*) as count "
                      "FROM posts INNER JOIN blogs ON "
                      "blogs.id=posts.blog_id "
                      "WHERE blogs.latitude is not NULL "
                      "AND blogs.longitude is not NULL "
                      "AND blogs.rank <= 4 "
                      "AND blogs.longitude > " + str(llcrnrlon) + " "
                      "AND blogs.longitude < " + str(urcrnrlon) + " "
                      "AND blogs.latitude > " + str(llcrnrlat) + " "
                      "AND blogs.latitude < " + str(urcrnrlat) + " "
                      "AND blogs.source <> 'fotosidan' ")

    for row in result:
        nPosts = row['count']
    print "{} dokument finns i rutan {}".format(nPosts, region) 
    
    batch = 100000
    print "Räknar ord i {} procent av dem i batchar om {}".format(percent, batch)

    nPosts = int(percent*nPosts/100.0) 
    offsets = xrange(0, nPosts, batch)
    
    #bigrams = Counter() 
    #trirams = Counter() 
    
    transtab = string.maketrans("ABCDEFGHIJKLMNOPQRSTUVXYZÅÄÖÉ",
                                "abcdefghijklmnopqrstuvxyzåäöé")
    punkter = string.punctuation
    
    try:
        result = db.query("drop table tempwordcounts")
        #delete from tempwordcounts
        print "Tog bort tabellen tempwordcounts för att göra rum för nytt."
    except:
        pass
    
    for offset in offsets:
        start = time.time()
        onegrams = Counter() 
        #result = db.query("SELECT text from posts limit "
        #                  ""+str(batch)+" offset " + str(offset))
        
        result = db.query("SELECT posts.text "
                          "FROM posts INNER JOIN blogs ON "
                          "blogs.id=posts.blog_id "
                          "WHERE blogs.latitude is not NULL "
                          "AND blogs.longitude is not NULL "
                          "AND blogs.rank <= 4 "
                          "AND blogs.longitude > " + str(llcrnrlon) + " "
                          "AND blogs.longitude < " + str(urcrnrlon) + " "
                          "AND blogs.latitude > " + str(llcrnrlat) + " "
                          "AND blogs.latitude < " + str(urcrnrlat) + " "
                          "AND blogs.source <> 'fotosidan' "
                          "LIMIT "+ str(batch) +" offset " + str(offset))
        
        for row in result:
            words = row['text'].translate(transtab, punkter).split()
            words = [w.strip() for w in words]
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
        print str(100*offset/nPosts)[0:4], "%", "- Tog:", int((time.time() - start)), "sekunder. Region:", region
    
       
    # Rensa lite
    try:
        result = db.query("CREATE INDEX ind_token ON tempwordcounts(token);")
        print "Index skapades"

    except:
        pass
    try:
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
    #count_words_in_region("country", (26, 69.5, 8, 54.5), percent=100)
    # Skåne
    #count_words_in_region("skaune2", (14.653015, 56.256273, 12.551880, 55.349353), percent=100)
    # Norrland
    #count_words_in_region("norrland", (25.975690, 69.173527, 12.372609, 62.213702), percent=100)
    # Småland 
    #count_words_in_region("smauland", (16.880994, 58.143755, 13.349390, 56.624219), percent=100)
    # Göteborg
    #count_words_in_region("gotlaborg", (13.867365, 59.393105, 11.401765, 56.482094), percent=100)
    # Mälardalen
    #count_words_in_region("malardalen", (18.532594, 59.933278, 14.962038, 58.497572), percent=100)
    # Mälardalen
    #count_words_in_region("finland", (26.971690, 65.189505, 20.643567, 59.497556), percent=100)
    # Dalarna
    #count_words_in_region("dalarna", (16.539451, 61.911557, 12.672264, 60.002842), percent=100)
    # Dalarna
    #count_words_in_region("gotland666", (19.593651, 58.081954, 17.739940, 56.724710), percent=100)

    # Genererade
    count_words_in_region('Vaestra Goetaland', (12.125, 58.7666666667, 9.5, 57.7), percent=100)
    count_words_in_region('JoenkoepingGislaveds Kommun', (14.75, 57.7, 12.125, 56.6333333333), percent=100)
    count_words_in_region('Vaestra GoetalandFalkopings Kommun', (14.75, 58.7666666667, 12.125, 57.7), percent=100)
    count_words_in_region('VaermlandHammaro Kommun', (14.75, 59.8333333333, 12.125, 58.7666666667), percent=100)
    count_words_in_region('VaermlandHagfors Kommun', (14.75, 60.9, 12.125, 59.8333333333), percent=100)
    count_words_in_region('DalarnaAlvdalens Kommun', (14.75, 61.9666666667, 12.125, 60.9), percent=100)
    count_words_in_region('JaemtlandAre kommun', (14.75, 63.0333333333, 12.125, 61.9666666667), percent=100)
    count_words_in_region('BlekingeKarlskrona Kommun', (17.375, 56.6333333333, 14.75, 55.5666666667), percent=100)
    count_words_in_region('KalmarHogsby Kommun', (17.375, 57.7, 14.75, 56.6333333333), percent=100)
    count_words_in_region('OEstergoetlandAtvidabergs Kommun', (17.375, 58.7666666667, 14.75, 57.7), percent=100)
    count_words_in_region('VaestmanlandKungsoers kommun', (17.375, 59.8333333333, 14.75, 58.7666666667), percent=100)
    count_words_in_region('DalarnaHedemora Kommun', (17.375, 60.9, 14.75, 59.8333333333), percent=100)
    count_words_in_region('GaevleborgOvanakers Kommun', (17.375, 61.9666666667, 14.75, 60.9), percent=100)
    count_words_in_region('VaesternorrlandAnge Kommun', (17.375, 63.0333333333, 14.75, 61.9666666667), percent=100)
    count_words_in_region('JaemtlandRagunda Kommun', (17.375, 64.1, 14.75, 63.0333333333), percent=100)
    count_words_in_region('VaesterbottenDorotea Kommun', (17.375, 65.1666666667, 14.75, 64.1), percent=100)
    count_words_in_region('VaesterbottenStorumans Kommun', (17.375, 66.2333333333, 14.75, 65.1666666667), percent=100)
    count_words_in_region('StockholmVarmdo Kommun', (20.0, 59.8333333333, 17.375, 58.7666666667), percent=100)
    count_words_in_region('UppsalaOsthammars Kommun', (20.0, 60.9, 17.375, 59.8333333333), percent=100)
    count_words_in_region('VaesternorrlandKramfors Kommun', (20.0, 63.0333333333, 17.375, 61.9666666667), percent=100)
    count_words_in_region('VaesternorrlandOErnskoeldsviks Kommun', (20.0, 64.1, 17.375, 63.0333333333), percent=100)
    count_words_in_region('VaesterbottenLycksele kommun', (20.0, 65.1666666667, 17.375, 64.1), percent=100)
    count_words_in_region('NorrbottenArvidsjaurs Kommun', (20.0, 66.2333333333, 17.375, 65.1666666667), percent=100)
    count_words_in_region('NorrbottenArjeplogs Kommun', (20.0, 67.3, 17.375, 66.2333333333), percent=100)
    count_words_in_region('VaesterbottenSkelleftea Kommun', (22.625, 65.1666666667, 20.0, 64.1), percent=100)
    count_words_in_region('NorrbottenAlvsbyns Kommun', (22.625, 66.2333333333, 20.0, 65.1666666667), percent=100)
    count_words_in_region('NorrbottenGallivare Kommun', (22.625, 67.3, 20.0, 66.2333333333), percent=100)
    count_words_in_region('NorrbottenHaparanda Kommun', (25.25, 66.2333333333, 22.625, 65.1666666667), percent=100)
    