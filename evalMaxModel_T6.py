#!/usr/bin/python
# -*- coding: utf-8 -*- 

from textLoc26 import *
#import sys
import dataset
import re
from geocode import latlon
import geocode
import numpy as np
import urllib2
import requests
import json
from collections import OrderedDict
import config as c
import tabulate
import time

def predictViaAPI(text, path="tag"):
    payload = json.dumps({'text': text})
    headers = {'content-type': 'application/json'}
    r = requests.post("http://ext-web.gavagai.se:5001/geotag/api/v1.0/"+path, 
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
    db = dataset.connect(c.LOCATIONDB+ "?charset=utf8")
    db.query("set names 'utf8'")
    result = db.query("SELECT b.* FROM blogs b "
                      "WHERE (SELECT count(*) FROM posts p WHERE " 
                      "       p.blog_id=b.id) > 0 "
                      "AND rank = 2 AND "
                      "longitude is not NULL AND "
                      "latitude is not NULL "
                      "ORDER by id DESC")
    felenT1, felenT6, felenT6 = [], [], []
    i = 0
    acceptableAnswerT1, acceptableAnswerT6, acceptableAnswerT6 = 0, 0, 0
    chooseToAnswerT1, chooseToAnswerT6, chooseToAnswerT6 = 0, 0, 0
    
    for row in result:
    
        blogid = row['id']
        
        posts = db['posts'].find(blog_id=blogid)
        text = ""   
        for post in posts:
            text = text + u"\n\n" + post['text']
        
        
        if len(text) > 10000:
                
            i += 1

            headpattern = "{test:<4} {fel:<4} {median:<4} {medelv:<4} {AST:<4} {ASV:<4} {SP:<3}"
            
            testhead = headpattern.format(fel="fel",
                                          median="mdn", 
                                          medelv="mdv", 
                                          AST="AST", 
                                          ASV="ASV", 
                                          SP="SP", 
                                          test="T#")
            
            if (i-1) % 10 == 0: 
                pattern = "{id:>4} | {blogid:>7} | {tecken:>8} | {T6:<35} | {text:<70}"
                head = pattern.format(id="-"*4,
                                      blogid="-"*7, 
                                      tecken="-"*8, 
                                      T6="-"*35,
                                      text="-"*70)
                print head
            
                head = pattern.format(id="#", 
                                      blogid="Blogid", 
                                      tecken="Tecken", 
                                      T6=testhead,
                                      text="Bästa orden")
                print head
            
                head = pattern.format(id="-"*4, 
                                      blogid="-"*7, 
                                      tecken="-"*8, 
                                      T6="-"*35,
                                      text="-"*70)
                print head
        

            
            while True:
                try:
                    data3 = predictViaAPI(text, path="tagbytown")
                    break
                except requests.exceptions.ConnectionError:
                    time.sleep(5)
                    pass
                    
            predictedCoordinateT6, scoreT6, mostUsefulWordsT6, mentionsT6 = data3        
    
            # Test 3
            if predictedCoordinateT6 and scoreT6 > 0.0:
                chooseToAnswerT6 += 1
     
                mostUsefulWordsT6 = OrderedDict(sorted(mostUsefulWordsT6.items(), 
                                                     key=lambda x: x[1]))
                bestWordsT6 = []
                for word, scoreT6 in mostUsefulWordsT6.iteritems():
                    bestWordsT6.append(word.encode('utf-8'))
                    
                bestWordsT6 = ", ".join(bestWordsT6[::-1][0:6])
               
                fel = haversine([row['latitude'], row['longitude']], predictedCoordinateT6)
                
                if fel < 100: # Acceptabelt fel
                    acceptableAnswerT6 += 1
                
                felenT6.append(fel)
    
                pattern = ("{test:<4} {fel:<4,.00f} {median:<4,.00f} {medelv:<4,.00f} "
                           "{AST:<4,.02f} {ASV:<4,.02f} {SP:<3,.02f}")
                T6 = pattern.format(fel=fel,
                                    median=np.median(felenT6), 
                                    medelv=np.mean(felenT6), 
                                    AST=float(acceptableAnswerT6)/float(i), 
                                    ASV=float(acceptableAnswerT6)/float(chooseToAnswerT6), 
                                    SP=float(chooseToAnswerT6)/float(i), 
                                    test="T6")
    
                
            else:
                T6 = "###"
                bestWordsT6 = ""
                
    
            pattern = "{id:>4} | {blogid:>7} | {tecken:>8} | {T6:<35} | {text:<70}" 
            row = pattern.format(tecken=len(text),
                                 blogid=blogid, 
                                 T6=T6,
                                 id=i,
                                 text=bestWordsT6)
            print row
    
            