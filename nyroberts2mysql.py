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
    documents = dataset.connect(c.LOCATIONDB)
    documents.query("set names 'utf8';")
    #documents.query("SET AUTOCOMMIT = 0; "
    #                "SET FOREIGN_KEY_CHECKS = 0; "
    #                "SET UNIQUE_CHECKS = 0;")
     
    try:
        result = localfile.query("SELECT count(*) as c "
                                 "from " + BLOGSSOURCES)
        for row in result:
            print "Importerar " + str(row['c']) + " st källor." 
            sources = row['c']
        
        # The sqlite3 DB
        localSources = localfile.query("SELECT blogs.url, blogs.rowid, "
                                       "metadata.Ort, metadata.Land, "
                                       "metadata.Intressen, metadata.Ln, "
                                       "metadata.Kommun, metadata.text "
                                       "FROM blogs LEFT OUTER JOIN metadata "
                                       "ON blogs.url=metadata.url ")
        i, j = 0, 0
        
        for j, source in enumerate(localSources):  
            if j % 1000 == 1:
                print str(100*float(j)/float(sources))[0:4] + " %"    

            url = source[UNIQUENAME]
            idInSource = source['rowid']
            
            foundInDocumentsDB = documents['blogs'].find_one(url=url)
            
            if foundInDocumentsDB:
                documentID = foundInDocumentsDB['id']
                
            # The source needs to be created in documents
            else:
                documents['blogs'].insert(dict(url=url, 
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
                                               
                foundInDocumentsDB = documents['blogs'].find_one(url=url)
                documentID = foundInDocumentsDB['id']
                
                # Add the sources posts to the documents DB
                # with the newly inserted blog id.
                rows = []
                for post in localfile.query("SELECT * from posts "
                                            "WHERE "+BLOGSOURCE+"_id =" 
                                            " " + str(idInSource)):
                    i += 1
                    rows.append(dict(blog_id=documentID,
                                     date=datetime.datetime.fromtimestamp(post['date']),
                                     text=robertFix(only3bytes(post['summary'])))) 
                    
                    if i > 1000: 
                        i = 0                                                                         
                        try:
                            documents['posts'].insert_many(rows)
                            rows = [] 
                        except:
                            traceback.print_exc(file=sys.stdout)
                            rows = [] 
        
        print "And now I'm döne."
    
    except KeyboardInterrupt:
        #documents.query("SET AUTOCOMMIT = 1; "
        #                "SET FOREIGN_KEY_CHECKS = 1; "
        #                "SET UNIQUE_CHECKS = 1;")
        print "Avbryter..."
                        
    #documents.query("SET AUTOCOMMIT = 1; "
    #                "SET FOREIGN_KEY_CHECKS = 1; "
    #                "SET UNIQUE_CHECKS = 1;")