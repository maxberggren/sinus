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

"""
Test 1
======

testa GMM som ej slår ihop de tre densitetsfunktionerna
"""

def predictViaAPI(text, path="tag"):
    payload = json.dumps({'text': text})
    headers = {'content-type': 'application/json'}
    
    while True:
        try:     
            r = requests.post("http://ext-web.gavagai.se:5001/geotag/api/v1.0/"+path, 
                               data=payload, headers=headers)
            break
        except requests.exceptions.ConnectionError:
            time.sleep(5)
            pass 
         
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
    felenT1, felenT2, felenT3 = [], [], []
    i = 0
    acceptableAnswerT1, acceptableAnswerT2, acceptableAnswerT3 = 0, 0, 0
    chooseToAnswerT1, chooseToAnswerT2, chooseToAnswerT3 = 0, 0, 0
    
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
                pattern = "{id:>4} | {blogid:>7} | {tecken:>8} | {T2:<35} | {text:<70}"
                head = pattern.format(id="-"*4,
                                      blogid="-"*7, 
                                      tecken="-"*8, 
                                      T2="-"*35,
                                      text="-"*70)
                print head
            
                head = pattern.format(id="#", 
                                      blogid="Blogid", 
                                      tecken="Tecken", 
                                      T2=testhead,
                                      text="Bästa orden")
                print head
            
                head = pattern.format(id="-"*4, 
                                      blogid="-"*7, 
                                      tecken="-"*8, 
                                      T2="-"*35, 
                                      text="-"*70)
                print head


                            
            # Test 2: släpp igenom ord med platsighet
            # men slå ej ihop GMMer först...
            data2 = predictViaAPI(text, path="tagnogmmmerging/threshold/1e20")
            predictedCoordinateT2, scoreT2, mostUsefulWordsT2, mentionsT2 = data2
    
        
            # Test 2
            if predictedCoordinateT2 and scoreT2 > 0.0:
                chooseToAnswerT2 += 1
               
                fel = haversine([row['latitude'], row['longitude']], predictedCoordinateT2)
                
                if fel < 100: # Acceptabelt fel
                    acceptableAnswerT2 += 1
                
                felenT2.append(fel)
    
                pattern = ("{test:<4} {fel:<4,.00f} {median:<4,.00f} {medelv:<4,.00f} "
                           "{AST:<4,.02f} {ASV:<4,.02f} {SP:<3,.02f}")
                T2 = pattern.format(fel=fel,
                                    median=np.median(felenT2), 
                                    medelv=np.mean(felenT2), 
                                    AST=float(acceptableAnswerT2)/float(i), 
                                    ASV=float(acceptableAnswerT2)/float(chooseToAnswerT2), 
                                    SP=float(chooseToAnswerT2)/float(i), 
                                    test="T2")
    
                
            else:
                T2 = "###"
    
                
    
            pattern = "{id:>4} | {blogid:>7} | {tecken:>8} | {T2:<35} | {text:<70}" 
            row = pattern.format(tecken=len(text),
                                 blogid=blogid, 
                                 T2=T2, 
                                 id=i,
                                 text="")
            print row
    
            