#!/usr/bin/python
# -*- coding: utf-8 -*- 

from textLoc26 import *
#import sys
import dataset
import re
from geocode import latlon
import numpy as np
import urllib2
import requests
import json
from collections import OrderedDict
import config as c
import tabulate

def predictViaAPI(text):
    payload = json.dumps({'text': text})
    headers = {'content-type': 'application/json'}
    r = requests.post("http://ext-web.gavagai.se:5001/geotag/api/v1.0/tag", 
                       data=payload, headers=headers)
    
    try:
        lat = r.json()['latitude']
        lon = r.json()['longitude']
        placeness = r.json()['placeness']
        mostUsefulWords = r.json()['mostUsefulWords']
        mentions = r.json()['mentions']
        return [lon, lat], placeness, mostUsefulWords, mentions
    except:
        return None, None, None, None


if __name__ == "__main__":
    db = dataset.connect(c.LOCATIONDB)
    db.query("set names 'utf8'")
    result = db.query("SELECT * FROM blogs "
                      "WHERE longitude is not NULL "
                      "AND latitude is not NULL "
                      "AND rank = 2 ")
    
    felen = []
    i = 0
    acceptableAnswer = 0
    chooseToAnswer = 0
    
    for row in result:
        i += 1
        blogid = row['id']
        
        posts = db['posts'].find(blog_id=blogid)
        text = ""   
        for post in posts:
            text = text + u"\n\n" + post['text'].decode('latin-1')
            
        predictedCoordinate, score, mostUsefulWords, mentions = predictViaAPI(text)
        
        if predictedCoordinate and score > 0.0:

            chooseToAnswer += 1
            print "Förutspår koordinat från {} tecken. Nr #{}".format(len(text), i)
            fel = haversine([row['latitude'], row['longitude']], predictedCoordinate)
            
            if fel < 100: # Acceptabelt fel
                acceptableAnswer += 1
            
            felen.append(fel)

            print "Förutspådd koordinat: {}".format(predictedCoordinate) 
            print "Riktig koordinat: {}".format([row['latitude'], row['longitude']]) 
            print "Platsighet: {}".format(score) 
            
            mostUsefulWords = OrderedDict(sorted(mostUsefulWords.items(), 
                                                 key=lambda x: x[1]))
            
            for word, score in mostUsefulWords.iteritems():
                print word.encode('utf-8'), score, "(",mentions[word],"),",
            
                
            print "\nFel: {} km".format(fel)
            print "-----"
            print "Median: {}".format(np.median(felen))
            print "Medelv: {}".format(np.mean(felen))
            print "Acceptabelt svar totalt: {}".format(float(acceptableAnswer)/float(i))
            print "Acceptabelt svar av svarade: {}".format(float(acceptableAnswer)/
                                                           float(chooseToAnswer))
            print "Svarsprocent: {}".format(float(chooseToAnswer)/float(i))
            print "-----"
            
            print tabulate.tabulate([i, predictedCoordinate, [row['latitude'], row['longitude']]],[u"#", u"Förutspådd", u"Riktig"], "rst", floatfmt=".0f")

    