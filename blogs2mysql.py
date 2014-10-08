#!/usr/bin/python
# -*- coding: utf-8 -*- 

from textLoc26 import *
import sys
import dataset
import re
from geocode import latlon
import numpy as np
import urllib2
import requests
import json
import datetime
import config as c

RE_NORMAL = re.compile(ur"[a-zA-ZåäöÅÄÖé]")
RE_HIGH = re.compile(ur"[^\u0000-\u00ff]")

LATINIZE_TABLE = dict([
    (unicode(c.encode('utf-8'), 'latin1'), c)
    for c in u"åäöÅÄÖéüÜ"])

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
    

if __name__ == "__main__":
    batch = 1000
    
    db = dataset.connect('sqlite:///db.sqlite')
    #mysqldb = dataset.connect(c.DOCDB_URI)
    mysqldb = dataset.connect(c.DOCDB_URI_LOCAL)

    print "Räknar antalet bloggar som ska importeras (tar ett par minuter)"
    result = db.query("SELECT count(*) as c from blogs")
    for row in result:
        print "Ska nu importera " + str(row['c']) + " st källor." 
        sources = row['c']
        
    offsets = xrange(0, sources, batch)
    print "Lägger in i bloggtabell"
    for offset in offsets:
        
        result = db.query("SELECT blogs.url, blogs.rowid, metadata.Ort, metadata.Land, metadata.Intressen, metadata.Ln, metadata.Kommun, metadata.text FROM blogs LEFT OUTER JOIN metadata ON blogs.url=metadata.url LIMIT "+str(batch)+" OFFSET " + str(offset))
        
        print str(100*offset/sources)[0:4] + " %"
        rows = []
        for row in result:
            #print row
            if row['url']: 
                url=row['url'].encode('utf-8') 
            else: url="" 
            
            if row['Ort']: 
                city=row['Ort'].encode('utf-8') 
            else: city="" 
            
            if row['Land']: 
                country=row['Land'].encode('utf-8')
            else: country="" 
            
            if row['Intressen']: 
                intrests=row['Intressen'].encode('utf-8') 
            else: intrests="" 
            
            if row['Ln']: county=row['Ln'].encode('utf-8') 
            else: county="" 
            
            if row['Kommun']:
                municipality=row['Kommun'].encode('utf-8') 
            else: municipality="" 
            
            if row['text']:
                presentation=row['text'].encode('utf-8') 
            else: presentation="" 
            
            rowid=row['rowid']
                
            encodedDict = dict(id=rowid,
                               url=url, 
                               rowid=rowid, 
                               city=city,
                               country=country,
                               intrests=intrests,
                               county=county,
                               municipality=municipality,
                               presentation=presentation)
                               
            rows.append(encodedDict)
                               
        mysqldb['blogs2'].insert_many(rows)
        