#!/usr/bin/python
# -*- coding: utf-8 -*-
import config as c
import dataset
import geocode    
from geocode import latlon
import numpy as np
import pandas as pd

def sum1(input):
    """ Sum all elements in matrix """
    
    try:
        return sum(map(sum, input))
    except Exception:
        return sum(input)

def normalize(matrix):
    """ Divide all elements by sum of all elements """
    
    return matrix / sum1(matrix) 

def gen_grid(lats, lons, xBins=15, xyRatio=1.8, fix_zeros=False):
    """ Generate grid from coordinates """
    
    if len(lats) == 0:
        return np.zeros(shape=(int(xBins*xyRatio-1), xBins-1))
        
    lon_bins = np.linspace(8, 26, xBins)
    lat_bins = np.linspace(54.5, 69.5, xBins*xyRatio)
    
    lons = np.array(lons)
    lats = np.array(lats)

    density, _, _ = np.histogram2d(lats, 
                                   lons, 
                                   [lat_bins, 
                                    lon_bins])      
    if fix_zeros:
        # Set zeros to the smallest value in the matrix  
        zeros = np.in1d(density.ravel(), [0.]).reshape(density.shape)
        smallest = np.amin(np.nonzero(density))
        density[zeros] = smallest
        
    return density

def get_coordinate(place):
    """ Get coordinate from Google API. Also, this is posisbly
    the worst code ever written """
    
    city, muni, county, region = place
    try:
        city = city.encode('utf-8')  
    except:
        city = ""  
    try:
        muni = muni.encode('utf-8')    
    except:
        muni = ""
    try:
        county = county.encode('utf-8')  
    except:
        county = ""
    try:  
        region = region.encode('utf-8')  
    except:
        region = ""
    
    # Here a every possible field is stripped untill Google accepts it  
    try:
        coordinate = latlon(city + ", " + 
                            muni + ", " + 
                            county + ", " + 
                            region)
    except geocode.NoResultError as error:
        try:
            coordinate = latlon(muni + ", " + 
                                county + ", " + 
                                region)
        except geocode.NoResultError as error:
            try:
                coordinate = latlon(county + ", " + 
                                   region)
            except geocode.NoResultError as error:
                try:
                    coordinate = latlon(region)
                except geocode.NoResultError as error:
                    print error
                    coordinate = (None, None)
    
    return coordinate

mysqldb = dataset.connect(c.LOCATIONDB) 
mysqldb.query("set names 'utf8'") # For safety
np.set_printoptions(precision=4, linewidth=130)

for dist in [('täckbyxor', 'DB'),
             ('täck', 'Moderna dialektskillnader - TERMOBYXOR.xlsx')]:
    
    word, source = dist
    
    print "letar efter {} i {}".decode('utf-8').format(word.decode('utf-8'), source)
    
    if source == "DB":
        lats, lons = [], []
        result = mysqldb.query("SELECT blogs.longitude, "
                               "blogs.latitude, "
                               "blogs.source, "
                               "posts.text, "
                               "posts.date, "
                               "blogs.rank, "
                               "blogs.id "
                               "FROM posts INNER JOIN blogs ON "
                               "blogs.id=posts.blog_id "
                               "WHERE MATCH(posts.text) "
                               "AGAINST ('" + word + "' "
                               "IN BOOLEAN MODE) "
                               "AND blogs.latitude is not NULL "
                               "AND blogs.longitude is not NULL "
                               "AND blogs.rank <= 4 "
                               "ORDER BY posts.date ")        
        for row in result:
            lats.append(row['latitude'])
            lons.append(row['longitude'])
            
        print normalize(gen_grid(lats, lons))
        
    else: # Get from excel file
        df = pd.io.excel.read_excel("excelData/" + source)
        df = df.loc[df['form'] == word] # Filter for word of intrest
        lats, lons = [], [] 
        
        for place in zip(df['ort'], df['kommun'], df[u'län'], df['landskap']):
            try:
                lat, lon = get_coordinate(place) # from Google's API
            except geocode.QueryLimitError:
                lat, lon = None, None
                queryLimit = True
                
            lats.append(lat)
            lons.append(lon) 
            
        print normalize(gen_grid(lats, lons))