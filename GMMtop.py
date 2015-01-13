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
GMMtop
======

undersöka toppen av GMMerna
"""

def predictViaAPI(text, path="tag", correctCoord=None):
    payload = json.dumps({'text': text, 'coord': correctCoord})
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
    # Add all Swedish villages/citys to a set
    o = Set()
    f = codecs.open("orter.txt", encoding="utf-8")
    for line in f:
        o.add(line.lower().strip())
        
    # Hello mr DB
    db = dataset.connect(c.LOCATIONDB+ "?charset=utf8")
    db.query("set names 'utf8'")
    result = db.query("SELECT * from GMMs order by scoring desc LIMIT 10")
    
    for row in result:
        text = row['word']