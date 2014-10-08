#!/usr/bin/python
# -*- coding: utf-8 -*- 

from textLoc23 import *
import sys
import config as c

if __name__ == "__main__":
    model = tweetLoc()
    dbsqlite = dataset.connect('sqlite:///GMMs.db')
    GMMtable = dbsqlite['GMMs']
    dbmySQL = dataset.connect(c.GMMDB_URI)
    GMMtablemySQL = dbmySQL['GMMs']
    
    #result = dbmySQL.query("SET NAMES utf8;")
    #result = dbmySQL.query("DEFAULT CHARSET=utf8;")
    result = dbsqlite.query("SELECT * FROM GMMs")
        
    i = 0
    for row in result:
        i = i + 1
        print i
        #print row
        encodedDict = dict(word=row['word'].encode('utf-8'), lon=row['lon'], 
                           lat=row['lat'], scoring=row['scoring'],
                           date=row['date'], n_coordinates=row['n_coordinates'])
        #print encodedDict
        #try:
        #print row
        GMMtablemySQL.insert(encodedDict)
        #except:
        #    print sys.exc_info()[0]
        #    print row