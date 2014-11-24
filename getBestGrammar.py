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
import time

def maxFix(text):
    if text is None:
        return u""
    else:
        if isinstance(text, unicode):
            return text
        elif isinstance(text, str):
        
            try:
                assumedLatin1 = text.decode('latin-1') # unicode
            except UnicodeDecodeError:
                assumedLatin1 = u""
                
            try:    
                assumedUTF8 = text.decode('utf-8') # unicode
            except UnicodeDecodeError:
                assumedUTF8 = u""
             
            #print assumedLatin1
            #print assumedUTF8   
            #print type(assumedLatin1)
            #print type(assumedUTF8)
            
            if count_normal(assumedLatin1) > count_normal(assumedUTF8):
                #print "It's probably latin-1"
                #print count_normal(assumedLatin1)
                #print "vs"
                #print count_normal(assumedUTF8)
                return assumedLatin1
            else:
                #print "It's probably utf-8"
                #print count_normal(assumedLatin1)
                #print "vs"
                #print count_normal(assumedUTF8)
                return assumedUTF8
        else:
            return u""
            
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
    model = tweetLoc(c.LOCATIONDB) 
    db = dataset.connect(c.LOCATIONDB)
    result = db.query("set names 'utf8'")
    
    
    result = db.query("select * from blogs "
                      "rank <> 9999")
    
    for row in result:
        try:
            blogId = row['id']
            posts = db.query("SELECT * FROM posts WHERE "
                             "blog_id = " + str(blogId) + " limit 200;")
            
            text = u""
            for post in posts:
                text = text + u"\n\n" + maxFix(post['text'])
            
            print "Belägger " + row['url'] + "..."
            
            while True: 
                try:
                    meangrammars = predictViaAPI(text, path="findbestgrammar")

                    break
                except requests.exceptions.ConnectionError:
                    print "Kunde inte koppla mot api:et. Väntar 5 sek." 
                    time.sleep(5)
                    pass
            
            if meangrammars:
                print meangrammars                
            
            
            else:
                print "Errlol"
            
            
        except KeyboardInterrupt:
            print "Avslutar"
            break  
        
                    
