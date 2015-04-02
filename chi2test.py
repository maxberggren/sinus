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
import scipy

def genGrid(koordinater, xBins=4, xyRatio=1.8):

    if len(koordinater) == 0:
        return np.zeros(shape=(int(xBins*xyRatio-1), xBins-1))
        
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
    dump_filename = "all_blog_matrix.dump"

    if len(sys.argv) > 1:
        # kör bara på det sökordet
        searchword = sys.argv[1]
        coordinates = []
        
        for source in documents.query("SELECT blogs.longitude, "
                                   "blogs.latitude, "
                                   "blogs.id "
                                   "FROM posts INNER JOIN blogs ON "
                                   "blogs.id=posts.blog_id "
                                   "WHERE MATCH(posts.text) "
                                   "AGAINST ('" + searchword.encode('utf-8') + "' "
                                   "IN BOOLEAN MODE) "
                                   "AND blogs.latitude is not NULL "
                                   "AND blogs.longitude is not NULL "
                                   "AND blogs.rank <= 3 "):
                                   
            coordinates.append([source['longitude'], source['latitude']])

        matrix = normalize(genGrid(coordinates)) 
        null_hypothesis = np.load(dump_filename)
        
        print matrix
        print null_hypothesis
        
        print scipy.stats.chisquare(matrix, null_hypothesis, axis=None)
        
    else: # skapa matris att köra chi2 mot
        
        old_matrix = genGrid([])
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
                                          "latitude is not NULL "
                                          "ORDER BY RAND() "):   
                j += 1
                k += 1
                url = source['url']  
                blogid = source['id']    
    
                coordinates.append([source['longitude'], source['latitude']])
                
                if j % 1000:
                    diff = old_matrix - normalize(genGrid(coordinates)) 
                    diff = np.square(diff)
                    total_error = sum1(diff)
                    
                    if total_error != 0.0:
                        print total_error
                        
                    if total_error < 1e-8 and total_error != 0.0:
                       old_matrix.dump(dump_filename)
                       break
                    
                    old_matrix = normalize(genGrid(coordinates))
                    
        except KeyboardInterrupt:
            print "Avbryter..."
                        