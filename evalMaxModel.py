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
    db = dataset.connect(c.LOCATIONDB+ "?charset=utf8") #  + "?charset=utf8"
    db.query("set names 'utf8'")
    result = db.query("SELECT b.* FROM blogs b "
                      "WHERE (SELECT count(*) FROM posts p WHERE " 
                      "       p.blog_id=b.id) > 0 "
                      "AND rank = 2 AND "
                      "longitude is not NULL AND "
                      "latitude is not NULL "
                      "ORDER by id DESC")
    felen = []
    i = 0
    acceptableAnswer = 0
    chooseToAnswer = 0
    headpattern = "{test:<4} {fel:<4} {median:<4} {medelv:<4} {AST:<4} {ASV:<4} {SP:<3}".format(fel="fel",median="mdn", medelv="mdv", AST="AST", ASV="ASV", SP="SP", test="#T")
    
    for row in result:
        i += 1
        
        if i % 10 or i == 1:
            pattern = "{id:>4}  |  {tecken:>8}  |  {T1:<35}  |  {T2:<35}"
            head = pattern.format(id="#", 
                                  tecken="Tecken", 
                                  T1=headpattern, 
                                  T2=headpattern)
            print head
        
        blogid = row['id']
        
        posts = db['posts'].find(blog_id=blogid)
        text = ""   
        for post in posts:
            text = text + u"\n\n" + post['text']
            
        # Test 1: släpp igenom ord med platsighet > 1e40
        predictedCoordinate, score, mostUsefulWords, mentions = predictViaAPI(text)
        
        #print row['url']
        #print text[0:200].encode('utf-8').strip()
        #print "Förutspår koordinat från {} tecken. Nr #{}".format(len(text), i)
        
        if predictedCoordinate and score > 0.0:
            chooseToAnswer += 1
           
            fel = haversine([row['latitude'], row['longitude']], 
                            predictedCoordinate)
            
            if fel < 100: # Acceptabelt fel
                acceptableAnswer += 1
            
            felen.append(fel)
            
            """
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
            """
            
            pattern = "{test:<4} {fel:<4,.00f} {median:<4,.00f} {medelv:<4,.00f} {AST:<4,.02f} {ASV:<4,.02f} {SP:<3,.02f}"
            T1 = pattern.format(fel=fel,
                                median=np.median(felen), 
                                medelv=np.mean(felen), 
                                AST=float(acceptableAnswer)/float(i), 
                                ASV=float(acceptableAnswer)/float(chooseToAnswer), 
                                SP=float(chooseToAnswer)/float(i), 
                                test="T1")
    
            pattern = "{id:>4}  |  {tecken:>8}  |  {T1:<35}  |  {T2:<35}"
            row = pattern.format(tecken=len(text), 
                                 T1=T1, 
                                 T2=T1, 
                                 id=i)
    
            print row

            
        else:
            pattern = "{id:>4}  |  {tecken:>8}  |  {T1:<35}  |  {T2:<35}"
            row = pattern.format(tecken=len(text), 
                                 T1="###", 
                                 T2="###", 
                                 id=i)