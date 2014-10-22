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

def predictViaAPI(text):
    try:
        payload = json.dumps({'text': text})
        headers = {'content-type': 'application/json'}
        r = requests.post("http://ext-web.gavagai.se:5000/localize/api/v1.0/localize", 
                           data=payload, headers=headers)
        
        
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
    result = db.query("select * from blogs WHERE country = '' "
                      "and municipality = '' and county = '' and "
                      "city = '' and "
                      "longitude is NULL and "
                      "latitude is NULL")
    
    for row in result:
        posts = db.query("SELECT * FROM posts WHERE blog_id = " + str(row['id']) + ";")
        
        text = ""
        for post in posts:
            text = text + "\n\n" + post['text']
            
        predictedCoordinate, score, mostUsefulWords, mentions = predictViaAPI(text)
        
        if predictedCoordinate and score > 0.0:
            print predictedCoordinate