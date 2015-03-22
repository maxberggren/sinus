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


if __name__ == "__main__":
    documents = dataset.connect(c.LOCATIONDB)
    documents.query("set names 'utf8';")
    i, j, k = 0, 0, 0
    try:
        
        result = documents.query("SELECT count(*) as c "
                                 "from blogs")
        for row in result:
            print "Hittade " + str(row['c']) + " st källor." 
            sources = row['c']
        
        print "Inserting blogs"
        rows = []
        
        # Blogs
        for source in documents.query("SELECT * from blogs"):                         
            j += 1
            k += 1
            url = source['url']   
            print url
            """
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
            """
                        
            #rows.append(blog)
           
    
    except KeyboardInterrupt:
        print "Avbryter..."
                        