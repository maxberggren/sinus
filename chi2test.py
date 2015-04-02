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

def genGrid(koordinater, xBins=4, xyRatio=1.8):

    if len(koordinater) == 0:
        return np.zeros(shape=(int(xBins*xyRatio), xBins))
        
    lon_bins = np.linspace(8, 26, xBins)
    lat_bins = np.linspace(54.5, 69.5, xBins*xyRatio)

    lons, lats = zip(*koordinater)             
    lons = np.array(lons)
    lats = np.array(lats)

    density, _, _ = np.histogram2d(lats, 
                                   lons, 
                                   [lat_bins, 
                                    lon_bins])
    return density

def sum1(input):
    return sum(map(sum, input))
    
def normalize(matrix):
    return matrix / sum1(matrix)

if __name__ == "__main__":
    documents = dataset.connect(c.LOCATIONDB)
    documents.query("set names 'utf8';")
    
    new_matrix = genGrid([])
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
                                      "latitude is not NULL LIMIT 10000"):   
            j += 1
            k += 1
            url = source['url']  
            blogid = source['id']   
            percent = 100.0*float(j)/float(sources)

            coordinates.append([source['longitude'], source['latitude']])
            
            if j % 100:
                print normalize(genGrid(coordinates)) - new_matrix
                new_matrix = normalize(genGrid(coordinates))
                #print "{} procent klart".format(percent)
    
        #print np.amax(genGrid(coordinates))
        #print genGrid(coordinates)
        #print normalize(genGrid(coordinates))
                    
    except KeyboardInterrupt:
        print "Avbryter..."
                        