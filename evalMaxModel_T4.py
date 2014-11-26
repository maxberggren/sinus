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
    felenT1, felenT2, felenT4 = [], [], []
    i = 0
    acceptableAnswerT1, acceptableAnswerT2, acceptableAnswerT4 = 0, 0, 0
    chooseToAnswerT1, chooseToAnswerT2, chooseToAnswerT4 = 0, 0, 0
    
    for row in result:
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
            pattern = "{id:>4} | {blogid:>7} | {tecken:>8} | {T4:<35} | {text:<70}"
            head = pattern.format(id="-"*4,
                                  blogid="-"*7, 
                                  tecken="-"*8, 
                                  T4="-"*35,
                                  text="-"*70)
            print head
        
            head = pattern.format(id="#", 
                                  blogid="Blogid", 
                                  tecken="Tecken", 
                                  T4=testhead,
                                  text="Bästa orden")
            print head
        
            head = pattern.format(id="-"*4, 
                                  blogid="-"*7, 
                                  tecken="-"*8, 
                                  T4="-"*35,
                                  text="-"*70)
            print head
        
        blogid = row['id']
        
        posts = db['posts'].find(blog_id=blogid)
        text = ""   
        for post in posts:
            text = text + u"\n\n" + post['text']
            
        
        # Test 3: grammatik matat in i platsighetsmodulen
        data3 = predictViaAPI(text, path="tagbygrammar/threshold/1e30")
        predictedCoordinateT4, scoreT4, mostUsefulWordsT4, mentionsT4 = data3        
    
        # Test 3
        if predictedCoordinateT4 and scoreT4 > 0.0:
            chooseToAnswerT4 += 1
 
            mostUsefulWordsT4 = OrderedDict(sorted(mostUsefulWordsT4.items(), 
                                                 key=lambda x: x[1]))
            bestWordsT4 = []
            for word, scoreT4 in mostUsefulWordsT4.iteritems():
                bestWordsT4.append(word.encode('utf-8'))
                
            bestWordsT4 = ", ".join(bestWordsT4[::-1][0:6])
 
           
            fel = haversine([row['latitude'], row['longitude']], predictedCoordinateT4)
            
            if fel < 100: # Acceptabelt fel
                acceptableAnswerT4 += 1
            
            felenT4.append(fel)

            pattern = ("{test:<4} {fel:<4,.00f} {median:<4,.00f} {medelv:<4,.00f} "
                       "{AST:<4,.02f} {ASV:<4,.02f} {SP:<3,.02f}")
            T4 = pattern.format(fel=fel,
                                median=np.median(felenT4), 
                                medelv=np.mean(felenT4), 
                                AST=float(acceptableAnswerT4)/float(i), 
                                ASV=float(acceptableAnswerT4)/float(chooseToAnswerT4), 
                                SP=float(chooseToAnswerT4)/float(i), 
                                test="T4")

            
        else:
            T4 = "###"
            bestWordsT4 = ""
            

        pattern = "{id:>4} | {blogid:>7} | {tecken:>8} | {T4:<35} | {text:<70}" 
        row = pattern.format(tecken=len(text),
                             blogid=blogid, 
                             T4=T4,
                             id=i,
                             text=bestWordsT4)
        print row

            