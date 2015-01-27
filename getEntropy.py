#!/usr/bin/python
# -*- coding: utf-8 -*- 
from __future__ import division
import matplotlib  
matplotlib.use('Agg')
#import nltk 
import dataset
import re
from collections import Counter
import time
import string 
from PIL import Image
import numpy as np
from matplotlib import pyplot as plt
import math
import sqlalchemy
import traceback
import config as c
import sys

def entropy(lats, lons, bins=10, xyRatio=1.8):
    # control how many bins
    binNrScaleFactor = bins 
    lon_bins = np.linspace(8, 26, binNrScaleFactor)
    # xyRatio to control the squarness of bins 
    lat_bins = np.linspace(54.5, 69.5, binNrScaleFactor*xyRatio) 
    
    frqMatrix, _, _ = np.histogram2d(lats, 
                                     lons, 
                                     [lat_bins, lon_bins])
    pctMatrix = frqMatrix / np.sum(frqMatrix)

    ent = 0.0
    for pct in pctMatrix.flatten():
        if pct > 0:
            ent -= + pct * math.log(pct, 2)
    
    return ent
    
def deltaEntropy(lats, lons, chunk=0.2):
    nCoordinates = len(lats)
    step = int(nCoordinates*chunk)
    entStart = entropy(lats[0:step], lons[0:step])
    entEnd = entropy(lats[-step:], lons[-step:])
    deltaEnt = abs(entStart-entEnd)
    return deltaEnt

if __name__ == "__main__":

    mysqldb = dataset.connect(c.LOCATIONDB)
    mysqldb.query("set names 'utf8'")
    
    try:
        token = sys.argv[1]
        print type(token)
        tokenQ = "token = '{token}' ".format(token=token)
        frq = ""
    except:
        tokenQ = "AND entropy is NULL "
        frq = "frequency > 50 AND frequency < 30000"
        
    q = """SELECT * from ngrams WHERE {frq} {tokenQ} 
           ORDER BY RAND() """.format(tokenQ=tokenQ, frq=frq)

    for row in mysqldb.query(q):
        start = time.time()
        searchWord = row['token']
        
        print "Ordet: {ord} med frekvens: {frq}".format(ord=searchWord,
                                                        frq=row['frequency'])
        
        try:
            lats, lons = [], []
            print type(searchWord)
            result = mysqldb.query("SELECT blogs.longitude "
                                   "FROM posts INNER JOIN blogs ON "
                                   "blogs.id=posts.blog_id "
                                   "WHERE MATCH(posts.text) "
                                   "AGAINST ('" + token + "' "
                                   "IN BOOLEAN MODE) "
                                   "AND blogs.latitude is not NULL "
                                   "AND blogs.longitude is not NULL "
                                   "AND blogs.rank <= 3 "
                                   "ORDER BY posts.date ")

            for row in result:
                if row['latitude'] and row['longitude']:
                    lats.append(row['latitude'])
                    lons.append(row['longitude'])

            if len(lats) > 15:
                deltaEnt10 = deltaEntropy(lats, lons, chunk=0.1)            
                print "Deltaent10:", deltaEnt10            
                deltaEnt20 = deltaEntropy(lats, lons, chunk=0.2)            
                print "Deltaent20:", deltaEnt20
                deltaEnt30 = deltaEntropy(lats, lons, chunk=0.3)            
                print "Deltaent30:", deltaEnt30
                deltaEnt40 = deltaEntropy(lats, lons, chunk=0.4)            
                print "Deltaent40:", deltaEnt40
                deltaEnt50 = deltaEntropy(lats, lons, chunk=0.5)            
                print "Deltaent50:", deltaEnt50                
                ent = entropy(lats, lons)
                print "Overall entropy:", ent
        
                data = dict(token=searchWord, 
                            entropy=ent,
                            deltaEnt10=deltaEnt10,
                            deltaEnt20=deltaEnt20,
                            deltaEnt30=deltaEnt30,
                            deltaEnt40=deltaEnt40,
                            deltaEnt50=deltaEnt50)
                mysqldb['ngrams'].update(data, ['token'])
            else:
                print "Ordet misslyckades pga för få koordinater."
                print "Hittade endast: " + str(len(lats))

        except KeyboardInterrupt:
            print "Skippar ordet"
            choise = raw_input('Vill du avsluta? (j/n): ')
            if choise == "j":
                break
        except sqlalchemy.exc.InternalError:
            print "FTS query exceeds result cache limit"
        #except:
        #    traceback.print_exc(file=sys.stdout)
    
