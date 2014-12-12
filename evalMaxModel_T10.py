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
Test 10
======

röstningsförfarandet för alla ord, mot gramatik kört i röstningsförf
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


                
            # Test 1: tagbyvote1
            data = predictViaAPI(text, path="tagbyvote1/threshold/1e20")
            predictedCoordinateT1, scoreT1, mostUsefulWordsT1, mentionsT1 = data
            
            # Test 2: tagbyvote2
            data2 = predictViaAPI(text, path="tagbyvote2/threshold/1e20")
            predictedCoordinateT2, scoreT2, mostUsefulWordsT2, mentionsT2 = data2   
                
        
            # Test 1
            if predictedCoordinateT1 and scoreT1 > 0.0:
                chooseToAnswerT1 += 1
               
                fel = haversine([row['latitude'], row['longitude']], predictedCoordinateT1)
                correctCoordinateT1 = [row['latitude'], row['longitude']]
                
                if fel < 100: # Acceptabelt fel
                    acceptableAnswerT1 += 1
                
                felenT1.append(fel)
                mostUsefulWordsT1 = OrderedDict(sorted(mostUsefulWordsT1.items(), 
                                                     key=lambda x: x[1]))
                bestWordsT1 = []
                for word, scoreT1 in mostUsefulWordsT1.iteritems():
                    bestWordsT1.append(word.encode('utf-8'))
                    
                bestWordsT1 = ", ".join(bestWordsT1[::-1][0:6])
                
                pattern = ("{test:<4} {fel:<4,.00f} {median:<4,.00f} {medelv:<4,.00f} "
                           "{AST:<4,.02f} {ASV:<4,.02f} {SP:<3,.02f}")
                T1 = pattern.format(fel=fel,
                                    median=np.median(felenT1), 
                                    medelv=np.mean(felenT1), 
                                    AST=float(acceptableAnswerT1)/float(i), 
                                    ASV=float(acceptableAnswerT1)/float(chooseToAnswerT1), 
                                    SP=float(chooseToAnswerT1)/float(i), 
                                    test="T1")
    
                
            else:
                T1 = "###"
                bestWordsT1 = "###"
    
    
            # Test 2
            if predictedCoordinateT2 and scoreT2 > 0.0:
                chooseToAnswerT2 += 1
               
                fel = haversine([row['latitude'], row['longitude']], predictedCoordinateT2)
                correctCoordinateT2 = [row['latitude'], row['longitude']]

                
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
    

                
    
            pattern = "{id:>4} | {blogid:>7} | {tecken:>8} | {T1:<35} | {T2:<35} | {text:<70}" 
            row = pattern.format(tecken=len(text),
                                 blogid=blogid, 
                                 T1=T1, 
                                 T2=T2, 
                                 id=i,
                                 text="AW: P-{P1} C-{C1}, GR: P-{P2} C-{C2}".format(P1=predictedCoordinateT1, P2=predictedCoordinateT2, C1=correctCoordinateT1, C2=correctCoordinateT2))
            print row
    
            