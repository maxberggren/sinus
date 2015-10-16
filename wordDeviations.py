#!/usr/bin/python
# -*- coding: utf-8 -*- 
from __future__ import division
#import nltk
import dataset
import re
import numpy as np
from collections import Counter
import time
import string 
import sqlalchemy
import warnings
import config as c
import pandas as pd
from sqlalchemy import create_engine
import MySQLdb

db = dataset.connect(c.LOCATIONDB)

def deviations(region=None):
    
    result = db.query('DELETE FROM worddeviations where region = {}'.format(region))
    print "Tog bort gamla ord i databasen för {}".format(region)

    threshold = 0.5
    data = {}

    common_word_occurance = db['wordcounts'].find_one(token='och', region=region)['frequency']
    print "Ordet 'och' har frekvensen {} i regionen {}".format(common_word_occurance, region)
    
    start = time.time()

    lower_limit = common_word_occurance*0.00009902951079*threshold
    upper_limit = common_word_occurance*0.8
    print "Undre limit", lower_limit
    print "Ovre limit", upper_limit

    result = db.query('SELECT count(*) as c FROM wordcounts '
                      'WHERE (region = "country" '
                      'or region = "{}") ' 
                      'and frequency > {} '
                      'and frequency < {}'.format(region, lower_limit, upper_limit))
    for row in result:
        print row['c'], "ord hittade"
        n_words = row['c']

    # Using another databasecon that's 
    mysql = MySQLdb.connect(host="locationdb.gavagai.se",
                            user="sinus",
                            passwd="5NU4KbP8",
                            db="sinus2") 
    cur = mysql.cursor() 
    cur.execute('SELECT region, frequency, token FROM wordcounts '
                'WHERE (region = "country" '
                'or region = "{}") '
                'and frequency > {} '
                'and frequency < {}'.format(region, lower_limit, upper_limit))

    regions, frequencys, tokens = [], [], []

    i = 0
    for result in cur.fetchall(): #data:
        i += 1
        if i % 10000 == 0:
            print "{} % klart".format(float(i)/float(n_words))

        tokens.append(result[2].decode('latin-1'))
        regions.append(region)
        frequencys.append(result[1])

    df = pd.DataFrame({'token': tokens,
                       'region': regions,
                       'frequency': frequencys})

    print time.time() - start, "att ladda in i pandas"


    def rel_frq(values):
        if len(values) == 2:
            return (values.values[1] - values.values[0])/values.values[0]
        else: 
            return 0.0

    start = time.time()
    grouped = df.groupby("token")
    n_groups = len(grouped)

    words, dev = [], []
    rows = []
    i = 0
    for token, df in grouped:
        i += 1        
        if i % 1000 == 0:
            print "{} % klart".format(float(i)/float(n_groups))

        vals = df.frequency.values

        if len(vals) > 1:
            dev = (vals[1] - vals[0])/vals[0]

            if dev > 0.3:
                rows.append({'token': token,
                             'deviation': dev,
                             'region': region})


    print time.time() - start, "att gruppera per ord"

    #print rows
    db['worddeviations'].insert_many(rows)
        
    
if __name__ == "__main__":

    # Sweden total    
    #count_words_in_region("country", (26, 69.5, 8, 54.5), percent=100)
    # Skåne
    #count_words_in_region("skaune", (14.653015, 56.256273, 12.551880, 55.349353), percent=100)
    # Norrland
    #count_words_in_region("norrland", (25.975690, 69.173527, 12.372609, 62.213702), percent=100)
    # Småland 
    #count_words_in_region("smauland", (16.880994, 58.143755, 13.349390, 56.624219), percent=100)
    # Göteborg
    #count_words_in_region("gotlaborg", (13.867365, 59.393105, 11.401765, 56.482094), percent=100)
    # Mälardalen
    #count_words_in_region("malardalen", (18.532594, 59.933278, 14.962038, 58.497572), percent=100)
    # Mälardalen
    #count_words_in_region("finland", (26.971690, 65.189505, 20.643567, 59.497556), percent=100)
    # Dalarna
    #count_words_in_region("dalarna", (16.539451, 61.911557, 12.672264, 60.002842), percent=100)
    # Dalarna
    df = deviations("finland")

    