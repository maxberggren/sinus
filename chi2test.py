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
        coordinates = []
        result = documents.query("SELECT count(*) as c "
                                 "from blogs "
                                 "WHERE longitude is not NULL and "
                                 "latitude is not NULL")
        for row in result:
            sources = row['c']
            print "Hittade {} st källor.".format(sources)
                    
        # Blogs
        for source in documents.query("SELECT * from blogs "
                                      "WHERE longitude is not NULL and "
                                      "latitude is not NULL LIMIT 10"):   
            j += 1
            k += 1
            url = source['url']  
            blogid = source['id']   
            percent = 100.0*float(j)/float(sources)
            print "{} procent klart".format(percent)

            coordinates.append([source['longitude'], source['latitude']])
    
        print coordiantes
    
    except KeyboardInterrupt:
        print "Avbryter..."
                        