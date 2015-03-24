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
from elasticsearch import Elasticsearch
from elasticsearch import helpers

if __name__ == "__main__":
    documents = dataset.connect(c.LOCALLOCATIONDB)

    documents.query("set names 'utf8';")

    es = Elasticsearch()

    i, j, k = 0, 0, 0
    try:
        
        result = documents.query("SELECT count(*) as c "
                                 "from blogs")
        for row in result:
            sources = row['c']
            print "Hittade {} st källor.".format(sources)
            
        print "Lägger in bloggars poster som dokument i ES."
        rows = []
        
        # Blogs
        for source in documents.query("SELECT * from blogs"):   
            actions = []                      
            j += 1
            k += 1
            url = source['url']  
            blogid = source['id']   
            percent = 100.0*float(j)/float(sources)
            print "{} procent klart".format(percent)

            for post in documents.query("SELECT * from posts "
                                        "WHERE blog_id = " + str(blogid)): 
                
                i += 1
                # date, text, blog_id, posttitle, posturl


                document = dict(url=url, 
                                blogid=blogid,

                                city=source['city'],
                                country=source['country'],
                                municipality=source['municipality'],
                                county=source['county'],
                                intrests=source['intrests'],
                                presentation=source['presentation'],

                                latitude=source['latitude'],
                                longitude=source['longitude'],

                                gender=source['gender'],
                                age=source['age'],
                                rank=source['rank'],
                                source=source['source'],

                                text=post['text'],
                                date=post['date'],
                                blog_id=post['blog_id'],
                                posttitle=post['posttitle'],
                                posturl=post['posturl']
                                )


                action = {
                    "_index": "sinus-index",
                    "_type": "sinus-data",
                    "_id": i,
                    "_source": document
                    }

                actions.append(action)

            helpers.bulk(es, actions)
    
    except KeyboardInterrupt:
        print "Avbryter..."
                        