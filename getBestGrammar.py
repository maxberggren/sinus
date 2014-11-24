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


RE_NORMAL = re.compile(ur"[a-zA-ZåäöÅÄÖé]")
RE_HIGH = re.compile(ur"[^\u0000-\u00ff]")

LATINIZE_TABLE = dict([
    (unicode(cr.encode('utf-8'), 'latin1'), cr)
    for cr in u"åäöÅÄÖéüÜ"])

RE_LATINIZE = re.compile(ur"|".join(LATINIZE_TABLE.keys()))

def count_normal(s):
    return len(RE_NORMAL.findall(s))

def latinize(s):
    try:
        latinized = unicode(s.encode('latin1'), 'utf-8')
        if count_normal(latinized) > count_normal(s):
            return latinized
    except (UnicodeDecodeError, UnicodeEncodeError):
        pass
    return None

def robertFix(post):
    latinized = latinize(post)
    if latinized != None:
        post = latinized
    else:
        post = RE_LATINIZE.sub(
            lambda m: LATINIZE_TABLE[m.group()], post)
    return post


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
    
    return r.json()['meangrammars'] 


if __name__ == "__main__":
    model = tweetLoc(c.LOCATIONDB) 
    db = dataset.connect(c.LOCATIONDB)
    result = db.query("set names 'utf8'")
    
    
    result = db.query("select * from blogs "
                      "WHERE rank <> 9999")
    
    for row in result:
        try:
            blogId = row['id']
            posts = db.query("SELECT * FROM posts WHERE "
                             "blog_id = " + str(blogId) + " limit 200;")
            
            text = u""
            for post in posts:
                text = text + u"\n\n" + maxFix(post['text'])
            
            print "Testar " + row['url'] + "..."
            
            meangrammars = None 
            
            while True: 
                try:
                    meangrammars = predictViaAPI(text, path="findbestgrammar")

                    break
                except requests.exceptions.ConnectionError:
                    print "Kunde inte koppla mot api:et. Väntar 5 sek." 
                    time.sleep(5)
                    pass
            
            print meangrammars
            
            
        except KeyboardInterrupt:
            print "Avslutar"
            break  
        
                    
