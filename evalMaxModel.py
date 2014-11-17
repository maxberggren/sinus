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

def predictViaAPI(text, extra=""):
    payload = json.dumps({'text': text})
    headers = {'content-type': 'application/json'}
    r = requests.post("http://ext-web.gavagai.se:5001/geotag/api/v1.0/tag"+extra, 
                       data=payload, headers=headers)
    
    try:
        lat = r.json()['latitude']
        lon = r.json()['longitude']
        placeness = r.json()['placeness']
        mostUsefulWordsT1 = r.json()['mostUsefulWordsT1']
        mentionsT1 = r.json()['mentionsT1']
        return [lon, lat], placeness, mostUsefulWordsT1, mentionsT1
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
    felT1en = []
    i = 0
    acceptableAnswerT1 = 0
    chooseToAnswerT1 = 0
    
    for row in result:
        i += 1
        
        headpattern = "{test:<4} {felT1:<4} {median:<4} {medelv:<4} {AST:<4} {ASV:<4} {SP:<3}"
        
        testhead = headpattern.format(felT1="felT1",
                                      median="mdn", 
                                      medelv="mdv", 
                                      AST="AST", 
                                      ASV="ASV", 
                                      SP="SP", 
                                      test="T#")
        
        if (i-1) % 10 == 0: 
            pattern = "{id:>4} | {blogid:>7} | {tecken:>8} | {T1:<35} | {T2:<35} | {text:<70}"
            head = pattern.format(id="-"*4,
                                  blogid="-"*7, 
                                  tecken="-"*8, 
                                  T1="-"*35, 
                                  T2="-"*35,
                                  text="-"*70)
            print head
        
            head = pattern.format(id="#", 
                                  blogid="Blogid", 
                                  tecken="Tecken", 
                                  T1=testhead, 
                                  T2=testhead,
                                  text="Bästa orden")
            print head
        
            head = pattern.format(id="-"*4, 
                                  blogid="-"*7, 
                                  tecken="-"*8, 
                                  T1="-"*35, 
                                  T2="-"*35,
                                  text="-"*70)
            print head
        
        blogid = row['id']
        
        posts = db['posts'].find(blog_id=blogid)
        text = ""   
        for post in posts:
            text = text + u"\n\n" + post['text']
            
        # Test 1: släpp igenom ord med platsighet > 1e40
        data = = predictViaAPI(text, extra="")
        print data
        predictedCoordinateT1, scoreT1, mostUsefulWordsT1, mentionsT1 = data
    
        if predictedCoordinateT1 and scoreT1 > 0.0:
            chooseToAnswerT1 += 1
           
            felT1 = haversine([row['latitude'], row['longitude']], predictedCoordinateT1)
            
            if felT1 < 100: # Acceptabelt felT1
                acceptableAnswerT1 += 1
            
            felT1en.append(felT1)

            mostUsefulWordsT1 = OrderedDict(sorted(mostUsefulWordsT1.items(), 
                                                 key=lambda x: x[1]))
            bestWordsT1 = []
            for word, scoreT1 in mostUsefulWordsT1.iteritems():
                bestWordsT1.append(word.encode('utf-8'))
                
            bestWordsT1 = ", ".join(bestWordsT1[::-1][0:6])
            
            pattern = ("{test:<4} {felT1:<4,.00f} {median:<4,.00f} {medelv:<4,.00f} "
                       "{AST:<4,.02f} {ASV:<4,.02f} {SP:<3,.02f}")
            T1 = pattern.format(felT1=felT1,
                                median=np.median(felT1en), 
                                medelv=np.mean(felT1en), 
                                AST=float(acceptableAnswerT1)/float(i), 
                                ASV=float(acceptableAnswerT1)/float(chooseToAnswerT1), 
                                SP=float(chooseToAnswerT1)/float(i), 
                                test="T1")
    
            pattern = "{id:>4} | {blogid:>7} | {tecken:>8} | {T1:<35} | {T2:<35} | {text:<70}"
            row = pattern.format(tecken=len(text),
                                 blogid=blogid, 
                                 T1=T1, 
                                 T2=T1, 
                                 id=i,
                                 text=bestWordsT1)
    
            print row

            
        else:
            pattern = "{id:>4} | {blogid:>7} | {tecken:>8} | {T1:<35} | {T2:<35} | {text:<70}"
            bestWordsT1 = "###"
            row = pattern.format(tecken=len(text), 
                                 blogid=blogid, 
                                 T1="###", 
                                 T2="###", 
                                 id=i,
                                 text=bestWordsT1)
            print row
            
            