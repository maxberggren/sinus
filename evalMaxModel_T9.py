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
Test 9
======

röstningsförfarandet på alla ord
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
                pattern = "{id:>4} | {blogid:>7} | {tecken:>8} | {T3:<35} | {text:<70}"
                head = pattern.format(id="-"*4,
                                      blogid="-"*7, 
                                      tecken="-"*8, 
                                      T3="-"*35,
                                      text="-"*70)
                print head
            
                head = pattern.format(id="#", 
                                      blogid="Blogid", 
                                      tecken="Tecken", 
                                      T3=testhead,
                                      text="Bästa orden")
                print head
            
                head = pattern.format(id="-"*4, 
                                      blogid="-"*7, 
                                      tecken="-"*8, 
                                      T3="-"*35,
                                      text="-"*70)
                print head


            
            # Test 3: röstningsförfarandet
            data3 = predictViaAPI(text, path="tagbyvote1/threshold/1e20")
            predictedCoordinateT3, scoreT3, mostUsefulWordsT3, mentionsT3 = data3        
            
            # Test 3
            if predictedCoordinateT3 and scoreT3 > 0.0:
                chooseToAnswerT3 += 1
               
                fel = haversine([row['latitude'], row['longitude']], predictedCoordinateT3)
                
                if fel < 100: # Acceptabelt fel
                    acceptableAnswerT3 += 1
                
                felenT3.append(fel)
    
                pattern = ("{test:<4} {fel:<4,.00f} {median:<4,.00f} {medelv:<4,.00f} "
                           "{AST:<4,.02f} {ASV:<4,.02f} {SP:<3,.02f}")
                T3 = pattern.format(fel=fel,
                                    median=np.median(felenT3), 
                                    medelv=np.mean(felenT3), 
                                    AST=float(acceptableAnswerT3)/float(i), 
                                    ASV=float(acceptableAnswerT3)/float(chooseToAnswerT3), 
                                    SP=float(chooseToAnswerT3)/float(i), 
                                    test="T3")
    
                
            else:
                T3 = "###"
                
    
            pattern = "{id:>4} | {blogid:>7} | {tecken:>8} | {T3:<35} | {text:<70}" 
            row = pattern.format(tecken=len(text),
                                 blogid=blogid, 
                                 T3=T3,
                                 id=i,
                                 text="")
            print row
    
            