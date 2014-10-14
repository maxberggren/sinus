#!/usr/bin/python
# -*- coding: utf-8 -*- 

from textLoc26 import *
import sys, traceback
import dataset
import re
import numpy as np
import urllib2
import json
import datetime
import config as c

BLOGSSOURCES = "blogs"
BLOGSOURCE = "blog"
UNIQUENAME = "url"
SOURCE = 'twingly'
SOURCEFILE = "db.sqlite"

unicodeBMPpattern = re.compile(u'[^\u0000-\uD7FF\uE000-\uFFFF]', re.UNICODE)

def only3bytes(unicode_string):
    return unicodeBMPpattern.sub(u'\uFFFD', unicode_string)

RE_NORMAL = re.compile(ur"[a-zA-ZåäöÅÄÖé]")
RE_HIGH = re.compile(ur"[^\u0000-\u00ff]")

LATINIZE_TABLE = dict([
    (unicode(c2.encode('utf-8'), 'latin1'), c2)
    for c2 in u"åäöÅÄÖéüÜ"])

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
    localfile = dataset.connect('sqlite:///'+SOURCEFILE)
    documents = dataset.connect(c.DOCDB_URI_LOCAL)
    documents.query("set names 'utf8';")
     
    try:
        result = localfile.query("SELECT count(*) as c "
                                 "from " + BLOGSSOURCES)
        for row in result:
            print "Importerar " + str(row['c']) + " st källor." 
            sources = row['c']
        
        i, j, k = 0, 0, 0
        print "Inserting blogs"
        rows = []
        #uniqueSources = set()
        
        # Blogs
        for source in localfile.query("SELECT blogs.url, blogs.rowid, "
                                       "metadata.Ort, metadata.Land, "
                                       "metadata.Intressen, metadata.Ln, "
                                       "metadata.Kommun, metadata.text "
                                       "FROM blogs LEFT OUTER JOIN metadata "
                                       "ON blogs.url=metadata.url "): 
                                        
            j += 1
            k += 1
            url = source[UNIQUENAME]
            #if not url in uniqueSources:
            #    uniqueSources.add(source[UNIQUENAME])
            
            rows.append(dict(url=source[UNIQUENAME], 
                             city=source['Ort'],
                             municipality=source['Kommun'],
                             county=source['Ln'], 
                             country=source['Land'],
                             intrests=source['Intressen'],
                             presentation=source['text'],
                             gender='',
                             source=SOURCE,
                             id=source['rowid'],
                             rank=2))

            if j > 1000: 
                j = 0                                                                         
                try:
                    documents['blogs'].insert_many(rows)
                    rows = [] 
                    print str(100*float(k)/float(sources))[0:4] + " %"  
                    sys.stdout.flush() 
                except:
                    traceback.print_exc(file=sys.stdout)
                    sys.stdout.flush() 
                    rows = [] 
                                           

        print "Inserting posts"
        rows = []
        k = 0
        # Posts
        for post in localfile.query("SELECT * from posts"):
            i += 1
            k += 1
            rows.append(dict(blog_id=post['blog_id'],
                             date=datetime.datetime.fromtimestamp(post['date']),
                             text=robertFix(only3bytes(post['summary'])))) 
            
            if i > 1000: 
                i = 0                                                                         
                try:
                    print str(100*float(k)/float(42000000))[0:4] + " %"  
                    sys.stdout.flush()
                    documents['posts'].insert_many(rows)
                    rows = [] 
                       
                except:
                    traceback.print_exc(file=sys.stdout)
                    sys.stdout.flush()
                    rows = [] # means that we trow away whole batch
    
        print "And now I'm döne. *tar en ostmacka*"
    
    except KeyboardInterrupt:
        print "Avbryter..."
                        