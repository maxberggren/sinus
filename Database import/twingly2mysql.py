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

def encutf8(s):
    if s is None:
        return ""
    else:
        if isinstance(s, (int, long)):
            return s 
        else:
            return s.encode('utf-8')

if __name__ == "__main__":
    localfile = dataset.connect('sqlite:///'+SOURCEFILE)
    documents = dataset.connect(c.LOCATIONDB)
    documents.query("set names 'utf8';")
    i, j, k = 0, 0, 0
    try:
        
        result = localfile.query("SELECT count(*) as c "
                                 "from " + BLOGSSOURCES)
        for row in result:
            print "Importerar " + str(row['c']) + " st källor." 
            sources = row['c']
        
        print "Inserting blogs"
        rows = []
        
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
            
            blog = dict(id=source['rowid'],
                        url=source[UNIQUENAME], 
                        city=source['Ort'],
                        municipality=source['Kommun'],
                        county=source['Ln'], 
                        country=source['Land'],
                        intrests=source['Intressen'],
                        presentation=source['text'],
                        gender='',
                        source=SOURCE,
                        rank=2)
                        
            blog = dict((k, encutf8(v)) for (k, v) in blog.items())

            rows.append(blog)

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
           
                                       
        # Posts
        print "Inserting posts"
        rows = []
        k = 0
        for post in localfile.query("SELECT * from posts"):
            i += 1
            k += 1
            t = robertFix(post['summary']).encode('utf-8')
            rows.append(dict(blog_id=post['blog_id'],
                             date=datetime.datetime.fromtimestamp(post['date']),
                             text=t)) 
            
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
                    rows = []
    
        print "And now I'm döne. *tar en ostmacka*"
    
    except KeyboardInterrupt:
        print "Avbryter..."
                        