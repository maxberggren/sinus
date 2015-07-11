#!/usr/bin/python
# -*- coding: utf-8 -*-

from oracleGUIapp import app
from flask import Flask, jsonify, make_response, request, render_template, redirect, url_for
from werkzeug import secure_filename

import config as c
import dataset
import geocode    
from geocode import latlon
import hashlib
import math
import numpy as np
from numpy import inf
import pandas as pd
import reverse_geocoder as rg
from sqlite_cache import SqliteCache
import sqlalchemy

from mpl_toolkits.basemap import Basemap, cm, maskoceans
import matplotlib.cm as cm
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.colors import LogNorm
from matplotlib.ticker import LogFormatter
from mpl_toolkits.axes_grid1 import make_axes_locatable
from scipy import ndimage
import matplotlib.pyplot as plt

questions = [{'question': u'Fara eller åka?',
              'explanation': u'Fyll i följande mening: **vi skulle...**',
              'answers': ['...fara till farmor', u'...åka till farmor'], 
              'query': ['fara', u'NOT fara'], 
              'target': 'DB', 
              'id': 2},
              
             {'question': u'Polisen?',
              'explanation': u'Vilket av följade använder du oftast för att tala om polisen?',
              'answers': [u'Bängen', 'Snuten', u'Farbror blå'], 
              'query': [u'bängen', 'snuten', u'farbror blå'], 
              'target': 'DB', 
              'id': 3}]

 
def negative(query):
    return query[0][0:4] == "NOT "

def sum1(input):
    """ Sum all elements in matrix """
    
    try:
        return sum(map(sum, input))
    except Exception:
        return sum(input)

def normalize(matrix):
    """ Divide all elements by sum of all elements """
    
    return matrix / sum1(matrix) 

def not_in(matrix):
    """ Prob of not being in each element """
    
    return normalize(1 - matrix)

def grid_maximum(matrix):
    """ Find where in grid highest probability lies """
    
    i, j = np.unravel_index(matrix.argmax(), matrix.shape)
        
    lon_bins = np.linspace(8, 26, xBins)
    lat_bins = np.linspace(54.5, 69.5, xBins*xyRatio)

    print matrix[i, j]
    print lon_bins[i]
    print lat_bins[j]

def gen_grid(lats, lons, no_zeros=False):
    """ Generate grid from coordinates """
    
    if len(lats) == 0:
        return np.zeros(shape=(int(xBins*xyRatio-1), xBins-1))
        
    lon_bins = np.linspace(8, 26, xBins)
    lat_bins = np.linspace(54.5, 69.5, xBins*xyRatio)
    
    lons = np.array(lons)
    lats = np.array(lats)

    density, _, _ = np.histogram2d(lats, lons, [lat_bins, lon_bins])   
       
    if no_zeros:
        # Set zeros to the smallest value in the matrix  
        zeros = np.in1d(density.ravel(), [0.]).reshape(density.shape)
        smallest = np.amin(np.nonzero(density))
        density[zeros] = smallest
    
    # Test with logaritmizing the data  
    #density = np.log(density)
    #density[density == -inf] = 0
    return normalize(density)

def entropy(pctMatrix):
    """ Calc entropy of a matrix """

    ent = 0.0
    for pct in pctMatrix.flatten():
        if pct > 0:
            ent -= + pct * math.log(pct, 2)
    return ent

def get_coordinate(place):
    """ Get coordinate from Google API. Also, this is possisbly
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

def get_grids(queries):
    """ Take queries and get their grids from the database. Or,
        from excel file. But ideally, get cached version. """

    grids = []
    
    for query in queries:
        word, source = query
        word, source = word.encode('utf-8'), source.encode('utf-8')

        print "letar efter {} i {}".format(word, source)
        word = word.replace("NOT ", "")
        
        hashkey = hashlib.sha224(str(word) + str(source) + str(xBins)).hexdigest()
        grid = cache.get(hashkey)

        if isinstance(grid, np.ndarray): # Found in cache
            print "hämtade från cachen: {}".format(str(query) + str(xBins))
            grids.append(grid)
            
        else: # Not found in cache
            if source == "DB": # Database
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
                                       "AND blogs.rank <= 3 "
                                       "ORDER BY posts.date ")
                for row in result:
                    lats.append(row['latitude'])
                    lons.append(row['longitude'])
                    
                print "Hittade {} koordinater".format(len(lats))
                grid = gen_grid(lats, lons)

                hashkey = hashlib.sha224(str(word) + str(source) + str(xBins)).hexdigest()
                cache.set(hashkey, grid, timeout=60*60*24*31*99999)   
                grids.append(grid)
                
            else: # Get from excel file
                df = pd.io.excel.read_excel("excelData/" + source)
                if 'form' in df.columns:
                    df = df.loc[df['form'] == word.decode('utf-8')] # Filter for word of intrest
                lats, lons = [], [] 
                
                for place in zip(df['ort'], df['kommun'], df[u'län'], df['landskap']):
                    try:
                        lat, lon = get_coordinate(place) # from Google's API
                    except geocode.QueryLimitError:
                        lat, lon = None, None
                        queryLimit = True
                        
                    if lat and lon:
                        lats.append(lat)
                        lons.append(lon) 
                    
                grid = gen_grid(lats, lons)
                hashkey = hashlib.sha224(str(word) + str(source) + str(xBins)).hexdigest()
                cache.set(hashkey, grid, timeout=60*60*24*31) 
                grids.append(grid)
            
    return grids         
 
def make_map(matrix, name):
    """ Create image with map and grid overlaid """

    print "skapar karta"
    density = matrix
    fig = plt.figure(figsize=(3.25*1,6))
    
    llcrnrlon = 8
    llcrnrlat = 54.5
    urcrnrlon = 26
    urcrnrlat = 69.5
    
    lon_bins = np.linspace(llcrnrlon, urcrnrlon, xBins)
    lat_bins = np.linspace(llcrnrlat, urcrnrlat, xBins*1.8)
        
    m = Basemap(projection='merc',
                resolution = 'i', 
                area_thresh=500,
                llcrnrlon=llcrnrlon, 
                llcrnrlat=llcrnrlat,
                urcrnrlon=urcrnrlon, 
                urcrnrlat=urcrnrlat,)   
    
    m.drawcoastlines(linewidth=0.5)
    m.drawcountries()
    m.drawstates()
    m.drawmapboundary()
    m.fillcontinents(color='white', lake_color='black', zorder=0)
    m.drawmapboundary(fill_color='black')
    
    lon_bins_2d, lat_bins_2d = np.meshgrid(lon_bins, lat_bins)
    xs, ys = m(lon_bins_2d, lat_bins_2d)
    xs = xs[0:density.shape[0], 0:density.shape[1]]
    ys = ys[0:density.shape[0], 0:density.shape[1]]
            
    # Colormap transparency
    theCM = cm.get_cmap('Purples') 
    theCM._init()
    alphas = np.abs(np.linspace(0, 1.0, theCM.N))
    theCM._lut[:-3,-1] = alphas
    
    p = plt.pcolor(xs, ys, density, 
                   cmap=theCM, 
                   norm=LogNorm(), 
                   antialiased=True)                    
    
    fig.tight_layout(pad=2.5, w_pad=0.1, h_pad=0.0) 
    
    plt.savefig("sinusGUIapp/static/maps/" + name + ".pdf", 
                dpi=100, 
                bbox_inches='tight')
                
@app.route('/oracle/', methods = ['GET', 'POST'])
@app.route('/oracle', methods = ['GET', 'POST'])
def oracle():
    return render_template("index.html", questions=questions, n_questions=len(questions))


@app.route('/oracle/predict', methods=['POST'])
def predict(): 
    """ Predict where user is from """

    def interp_answers(data):
        """ Put json data from GUI in the right form """
        queries = []

        for key, value in data.iteritems():
            query = [q for q in questions if q['id'] == int(key)][0]['query'][int(value)]
            source = [q for q in questions if q['id'] == int(key)][0]['target']
            queries.append((query, source))

        return queries

    queries = interp_answers(request.json)
    grids = get_grids(queries)
     
    def negative(query):
        return query[0][0:4] == "NOT "

    def matrix_product(grids, queries):
        """ Multiply all distributions into a final one """ 

        product = np.ones(grids[0].shape) # Set up uniform distribution

        for grid, query in zip(grids, queries): 
            if negative(query):
                product = np.multiply(product, not_in(grid)) 
            else:
                product = np.multiply(product, grid) 

        return product

    product = matrix_product(grids, queries)    
    density = normalize(product)
    grid_maximum(density)
    make_map(density, "product")

    return make_response(jsonify( { 'city1': 'YES', 'matrix': str(density) } ))






#print rg.get((37.78674,-122.39222))
xBins = 20
xyRatio = 1.8
cache = SqliteCache("oracle_cache") 
try:
    mysqldb = dataset.connect(c.LOCATIONDB) 
    mysqldb.query("set names 'utf8'") # Might help
except sqlalchemy.exc.OperationalError:
    print "No connection to mysql. Cache better work or it will fail."

np.set_printoptions(formatter={'float': lambda x: "{0:0.5f}".format(x)}, linewidth=155)
    