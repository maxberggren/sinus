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

if __name__ == "__main__":
    db = dataset.connect(c.LOCATIONDB+ "?charset=utf8")
    db.query("set names 'utf8'")
    result = db.query("SELECT b.* FROM blogs b "
                      "WHERE (SELECT count(*) FROM posts p WHERE " 
                      "       p.blog_id=b.id) > 0 AND "
                      "character_length(b.gender) > 0")
    
    for row in result:        
        posts = db['posts'].find(blog_id=row['id'])
        text = ""   
        for post in posts:
            text = text + u"\n\n" + post['text']
            
        if len(text) > 1000:
            tokens = nltk.word_tokenize(text)
            bgs = nltk.bigrams(tokens)
            fdist = nltk.FreqDist(bgs)
            for k,v in fdist.items():
                print k,v
            break