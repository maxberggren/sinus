#!/usr/bin/python
# -*- coding: utf-8 -*- 

from textLoc26 import *
import sys
import dataset
import re
import numpy as np
import urllib2
import json
import datetime
import config as c

BLOGSSOURCES = "blogs"
BLOGSOURCE = "blog"
USERURL = "url"
SOURCE = 'nattstad'
SOURCEFILE = "nattstad.db"

if __name__ == "__main__":
    localfile = dataset.connect('sqlite:///'+SOURCEFILE)
    documents = dataset.connect(c.DOCDB_URI_LOCAL)
    
    result = localfile.query("SELECT count(*) as c from " + BLOGSSOURCES)
    for row in result:
        print "Importerar " + str(row['c']) + " st källor. Letse go *supermarioröst*!" 
    print "D = duplicate, skipping"
    print "S#nr = Source nr # beeing inserted"
    print "P = post being inserted"
    
    # The sqlite3 DB
    localSources = localfile.query("SELECT * from " + BLOGSSOURCES)
    
    i = 0
    for source in localSources:
        i += 1
        url = source[USERURL]
        idInSource = source['id']
        
        foundInDocumentsDB = documents['blogs'].find_one(url=url)
        
        if foundInDocumentsDB:
            documentID = foundInDocumentsDB['id']
            sys.stdout.write('D')
            
        # The source needs to be created in documents
        else:
            documents['blogs'].insert(dict(url=url, 
                                           city=source['manuellStad'], 
                                           presentation=source['presentation'],
                                           source=SOURCE,
                                           rank=1))
            sys.stdout.write('S#'+str(i))
            
            foundInDocumentsDB = documents['blogs'].find_one(url=url)
            documentID = foundInDocumentsDB['id']
            
            # Now add the sources posts to the documents DB
            # with the newly inserted blog id.
            
            for post in localfile.query("SELECT * from posts "
                                        "WHERE "+BLOGSOURCE+"_id = " + str(idInSource)):
                
                try:
                    documents['posts'].insert(dict(blog_id=documentID,
                                                   date=post['date'],
                                                   text=post['text']))
                    sys.stdout.write('P')
                except:
                    sys.stdout.write('X')

    print "And now I'm döne."
