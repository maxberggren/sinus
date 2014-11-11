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
    result = db.query("SELECT * FROM blogs "
                      "WHERE longitude is not NULL "
                      "AND latitude is not NULL "
                      "AND rank = 2 ")
    
    fel = []
    i = 0
    acceptableAnswer = 0
    chooseToAnswer = 0
    
    for row in result:
        i += 1
    
        blogurl = row['url']
        blogid = row['rowid']
        
        posts = db.query("SELECT * FROM posts WHERE blog_id = " + str(blogid) + ";") 
        
        text = ""   
        #sdsda
        for post in posts:
            text = text + "\n\n" + post['text']
            
        predictedCoordinate, score, mostUsefulWords, mentions = predictViaAPI(text)
        
        if predictedCoordinate and score > 0.0:

            chooseToAnswer += 1
            print "Förutspår koordinat från " + str(len(text)) + " tecken. Nr #"+str(i)
            
            if haversine([row['longitude'], row['latitude']], predictedCoordinate) < 100:
                acceptableAnswer += 1
            
            fel.append(haversine([row['longitude'], row['latitude']], 
                                 predictedCoordinate))

            print "Förutspådd koordinat: " + str(predictedCoordinate) 
            print "Platsighet: " + str(score) 
            
            mostUsefulWords = OrderedDict(sorted(mostUsefulWords.items(), 
                                                 key=lambda x: x[1]))
            
            for word, score in mostUsefulWords.iteritems():
                print word.encode('utf-8'), score, "(",mentions[word],"),",
            
                
            print "\nFel: " + str(haversine([row['longitude'], row['latitude']], predictedCoordinate)) + " km"
            print "-----"
            print "Median: " + str(np.median(fel))
            print "Medelv: " + str(np.mean(fel))
            print "Acceptabelt svar totalt: " + str(float(acceptableAnswer)/float(i))
            print "Acceptabelt svar av svarade: " + str(float(acceptableAnswer)/float(chooseToAnswer))
            print "Svarsprocent: " + str(float(chooseToAnswer)/float(i))
            print "-----"
    