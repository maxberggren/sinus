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

BLOGSSOURCES = "sources"
BLOGSOURCE = "source"
UNIQUENAME = "username"
SOURCE = 'zatzy'
SOURCEFILE = "zatzy.db"

unicodeBMPpattern = re.compile(u'[^\u0000-\uD7FF\uE000-\uFFFF]', re.UNICODE)

def only3bytes(unicode_string):
    return unicodeBMPpattern.sub(u'\uFFFD', unicode_string)

def encutf8(s):
    if s is None:
        return ""
    else:
        if isinstance(s, (int, long, str)):
            return s 
        else:
            return s.encode('utf-8')
            
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
        localSources = localfile.query("SELECT * FROM " + BLOGSSOURCES)
        i, j = 0, 0
        
        for j, source in enumerate(localSources):  
            if j % 1000 == 1:
                print str(100*float(j)/float(sources))[0:4] + " %"    

            url = encutf8(source[UNIQUENAME])
            idInSource = source['id']
            
            foundInDocumentsDB = documents['blogs'].find_one(url=url)
            
            if foundInDocumentsDB:
                documentID = foundInDocumentsDB['id']
                
            # The source needs to be created in documents
            else:
                blog = dict(url=url, 
                            city=source['city'],
                            municipality='',
                            county='', 
                            country='',
                            intrests='',
                            presentation='',
                            gender='',
                            source=SOURCE,
                            rank=2)
                            
                blog = dict((k, encutf8(v)) for (k, v) in blog.items())
                documents['blogs'].insert(blog)
                                               
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
                                     date=post['date'],
                                     text=only3bytes(encutf8(post['text'])))) 
                    
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