#!/usr/bin/python
# -*- coding: utf-8 -*-

from oracleGUIapp import app
from flask import Flask, jsonify, make_response, request, render_template, redirect, url_for
from werkzeug import secure_filename

import binascii
import config as c
import dataset
import geocode    
from geocode import latlon
import hashlib
import math
import numpy as np
from numpy import inf
import os
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
from PIL import Image
  
llcrnrlon = 9.5
llcrnrlat = 54.5
urcrnrlon = 28.5
urcrnrlat = 69.5

xBins = 9
xyRatio = 1.8

questions = [{'question': u'Sov eller sovde?',
              'explanation': u'Säger du **sovde** eller **sov**?',
              'answers': [u'Sovde', u'Sov'], 
              'query': [u'sovde', u'NOT sovde'], 
              'target': 'DB', 
              'id': 1},
              
             {'question': u'Fara eller åka?',
              'explanation': u'Fyll i följande mening: **vi skulle...**',
              'answers': [u'...fara till farmor', u'...åka till farmor'], 
              'query': [u'fara', u'NOT fara'], 
              'target': 'DB', 
              'id': 2},
              
             {'question': u'Skottkärra',
              'explanation': u'Har du under din omgivning ibland pratat om en **rullebör**?',
              'answers': [u'O-Ja', u'Nej'], 
              'query': [u'rullebör', u'NOT rullebör'], 
              'target': 'DB', 
              'id': 4},
              
             {'question': u'Släktskap',
              'explanation': u'Vad kallar du dina föräldras kusiners barn?',
              'answers': [u'Nästkusin', u'Tremänning', u'Småkusin', u'Syssling'], 
              'query': [u'nästkusin', u'tremänning', u'småkusin', u'syssling'], 
              'target': 'DB', 
              'id': 5},
              
             {'question': u'Sötsaker',
              'explanation': u'Kallar du det **gräddbullar** eller **mums-mums**?',
              'answers': [u'Gräddbullar', u'Mums-mums'], 
              'query': [u'gräddbullar', u'NOT gräddbullar'], 
              'target': 'DB', 
              'id': 6},
              
             {'question': u'Frukt',
              'explanation': u'Säger du äpp**el** eller äpp**le**?',
              'answers': [u'Äpple', u'Äppel'], 
              'query': [u'NOT äppel', u'äppel'], 
              'target': 'DB', 
              'id': 7},
              
             {'question': u'Förstörelse',
              'explanation': u'Är något **trasigt** eller **söndrigt**?',
              'answers': [u'Trasigt', u'Söndrigt'], 
              'query': [u'NOT söndrig', u'söndrig'], 
              'target': 'DB', 
              'id': 8},
              
             {'question': u'Potatis',
              'explanation': u'Kallar du den nypotatis eller färskpotatis?',
              'answers': [u'Färskpotatis', u'Nypotatis'], 
              'query': [u'färskpotatis', u'nypotatis'], 
              'target': 'DB', 
              'id': 9},
              
             {'question': u'Frågesport',
              'explanation': u'Vad kallar du en promenad där du svarar 1, X eller 2 på frågor?',
              'answers': [u'Tipsrunda', u'Tipspromenad', u'Poängpromenad'], 
              'query': [u'tipsrunda', u'tipspromenad', u'poängpromenad'], 
              'target': 'DB', 
              'id': 11},
              
             {'question': u'Slang för bjuda',
              'explanation': u'Vilket av följande slang för **att bjuda** föredrar du?',
              'answers': [u'Bjussa', u'Bjucka', u'Bjuppa/Bjubba'], 
              'query': [u'bjussa', u'bjucka', u'bjuppa OR bjubba'], 
              'target': 'DB', 
              'id': 12},
              
             {'question': u'Äppelpaj eller äpplepaj?',
              'explanation': u'Säger du äpp**el**paj eller äpp**le**paj?',
              'answers': [u'Äppelpaj', u'Äpplepaj'], 
              'query': [u'äppelpaj', u'äpplepaj'], 
              'target': 'DB', 
              'id': 13}]

 
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
    
    arr = np.copy(matrix)
    # 1st maximum
    i, j = np.unravel_index(arr.argmax(), arr.shape)
        
    lon_bins = np.linspace(llcrnrlon, urcrnrlon+2, xBins)
    lat_bins = np.linspace(llcrnrlat, urcrnrlat+1, xBins*xyRatio)

    lon_corr = lon_bins[1]-lon_bins[0]
    lat_corr = lat_bins[1]-lat_bins[0]

    maximum = lat_bins[i]+lat_corr*0.5, lon_bins[j]+lon_corr*0.5

    # 2nd maximum
    arr[i, j] = 0
    i, j = np.unravel_index(arr.argmax(), arr.shape)
    second_maximum = lat_bins[i]+lat_corr*0.5, lon_bins[j]+lon_corr*0.5

    # 3rd maximum
    arr[i, j] = 0
    i, j = np.unravel_index(arr.argmax(), arr.shape)
    third_maximum = lat_bins[i]+lat_corr*0.5, lon_bins[j]+lon_corr*0.5

    return maximum, second_maximum, third_maximum

def gen_grid(lats, lons, no_zeros=True):
    """ Generate grid from coordinates """
    
    if len(lats) == 0:
        return np.zeros(shape=(int(xBins*xyRatio-1), xBins-1))
        
    lon_bins = np.linspace(llcrnrlon, urcrnrlon+2, xBins)
    lat_bins = np.linspace(llcrnrlat, urcrnrlat+1, xBins*xyRatio)
    
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
    #ensity[density == -inf] = 0
    print "griddade precis {} st coordianter".format(len(lons))

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

def get_enough_data():
    """ Get alot of data until a suitable null hypothesis has converged """
    
    try:        
        lons, lats = [], []

        for source in mysqldb.query("SELECT longitude, latitude from blogs "
                                    "WHERE longitude is not NULL and "
                                    "latitude is not NULL "
                                    "ORDER BY RAND() "
                                    "LIMIT 1000000"):   

            lons.append(source['longitude'])
            lats.append(source['latitude'])
            
        print "Plockade just {} coordinater fr DB".format(len(lons))
        return lons, lats

    except KeyboardInterrupt:
        print "Avbryter..."    

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
            print "söker i db efter: {}".format(str(query) + str(xBins))
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

def dev_from_null_hyp(grid, use_relative_deviation=False):
    """ Calc deviation from null hypothesis """

    hashkey = "hypothesis grid5" + str(xBins)
    null_hyp_grid = cache.get(hashkey)

    if isinstance(null_hyp_grid, np.ndarray): # Found in cache
        print "null hypothesis grid loaded from cache"
        
    else: # Not found in cache
        print "null hypothesis not found in cache"
        lons, lats = get_enough_data()
        null_hyp_grid = gen_grid(lats, lons)
        cache.set(hashkey, null_hyp_grid, timeout=60*60*24*31*99999) 

    if use_relative_deviation:
        quotent = np.divide(grid - null_hyp_grid, null_hyp_grid)
        NaNs = np.isnan(quotent)
        quotent[NaNs] = 0
        Infs = np.isinf(quotent)
        quotent[Infs] = 0
        maxerr = quotent.max()
        quotent = quotent + maxerr
    else: 
        # Use absolute deviation plus max element 
        # to remove entries < 0 (best try so far)
        quotent = grid - null_hyp_grid + null_hyp_grid.max()

    return quotent, null_hyp_grid
      
 
def make_map(matrix, log=False, filename=False):
    """ Create image with map and grid overlaid """

    print "skapar karta"

    coordinate, second_maximum, third_maximum = grid_maximum(matrix)
    density = matrix
    fig = plt.figure(figsize=(3.25*1,6))
    
    lon_bins = np.linspace(llcrnrlon, urcrnrlon+2, xBins)
    lat_bins = np.linspace(llcrnrlat, urcrnrlat+1, xBins*xyRatio)
    

    m = Basemap(projection='merc',
                resolution = 'l', 
                #area_thresh=500,
                llcrnrlon=llcrnrlon, 
                llcrnrlat=llcrnrlat,
                urcrnrlon=urcrnrlon, 
                urcrnrlat=urcrnrlat,)   
    
    m.drawcoastlines(linewidth=0.3, color='k')
    m.drawcountries(linewidth=0.3)
    #m.drawstates()
    m.drawmapboundary(linewidth=0, color='none', fill_color=(0.8, 0.8, 0.8, 0.5))
    m.fillcontinents(color='white', lake_color=(0.8, 0.8, 0.8, 0.5), zorder=0)
    
    lon_bins_2d, lat_bins_2d = np.meshgrid(lon_bins, lat_bins)
    xs, ys = m(lon_bins_2d, lat_bins_2d)
    xs = xs[0:density.shape[0], 0:density.shape[1]]
    ys = ys[0:density.shape[0], 0:density.shape[1]]
            
    # Colormap transparency
    theCM = cm.get_cmap('spring') 
    theCM._init()
    half_n = int(theCM.N / 2.0)
    forth_n = int(half_n / 2.0) 
    alphas = np.append(np.linspace(1, 0, forth_n), 
                       np.linspace(0, 0, half_n))
    alphas = np.append(alphas, 
                       np.linspace(0, 1, forth_n))

    theCM._lut[:-3,-1] = alphas
    
    if log:
        norm = LogNorm()
    else:
        norm = None

    p = plt.pcolor(xs, ys, density, 
                   cmap=theCM, 
                   norm=norm, 
                   antialiased=True)

    #plt.colorbar()                    
 
    # Put maximum on map
    lat, lon = coordinate
    x1, y1 = m(lon, lat)
    m.scatter(x1, y1, s=40, c='k', lw=0)

    fig.tight_layout(pad=2.5, w_pad=0.1, h_pad=0.0) 
    
    if not filename:
        filename = binascii.b2a_hex(os.urandom(15))[:10]
        filename = secure_filename(filename)

    filename = filename + ".png"
    path = "oracleGUIapp/static/maps/" + filename
    plt.savefig(path, 
                dpi=100, 
                bbox_inches='tight')

    # Crop
    img = Image.open(path)
    width = img.size[0]
    height = img.size[1]
    img = img.crop((20, 20, width-20, height-20))
    img.save(path)

    return filename
                
@app.route('/oracle/', methods = ['GET', 'POST'])
@app.route('/oracle', methods = ['GET', 'POST'])
def oracle():
    return render_template("index.html", questions=questions, n_questions=len(questions))


@app.route('/oracle/predict', methods=['POST'])
def predict(get_map=False, and_confirm=None): 
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

    def min_max_scaling(arr):
        return np.divide(arr - arr.min(), arr.max() - arr.min())

    def matrix_product(grids, queries):
        """ Multiply all distributions into a final one """ 

        product = np.ones(grids[0].shape) # Set up uniform distribution

        for grid, query in zip(grids, queries): 
            if negative(query):
                deviation_grid, _ = dev_from_null_hyp(grid)
                #deviation_grid = min_max_scaling(deviation_grid)
                deviation_grid = normalize(deviation_grid)

                product = np.multiply(product, not_in(deviation_grid)) 
                #make_map(not_in(deviation_grid), filename=str(query))
            else:
                deviation_grid, _ = dev_from_null_hyp(grid)
                #deviation_grid = min_max_scaling(deviation_grid)
                deviation_grid = normalize(deviation_grid)

                product = np.multiply(product, deviation_grid) 
                #make_map(deviation_grid, filename=str(query))

        return product

    product = matrix_product(grids, queries)    
    product = normalize(product)
    coordinate, second_maximum, third_maximum = grid_maximum(product) 
    region = rg.get(coordinate)['admin1']
    region2 = rg.get(second_maximum)['admin1']
    region3 = rg.get(third_maximum)['admin1']

    if get_map:
        product = min_max_scaling(product)
        filename_product = make_map(product)
    else:
        filename_product = None

    #_, null_hyp_grid = dev_from_null_hyp(product)
    #filename_hypo = make_map(null_hyp_grid, log=True)

    predictions = [region, region2, region3]

    if and_confirm:
        # TODO: Write datapoint to mysql
        return make_response(jsonify( { 'confirmed': predictions[and_confirm-1] } ))
    else:
        return make_response(jsonify( { 'region': region, 'region2': region2, 'region3': region3, 
                                        'filename_product': filename_product } ))
    

@app.route('/oracle/map', methods=['POST'])
def map(): 
    return predict(get_map=True)
    
@app.route('/oracle/confirm/<prediction_nr>', methods=['POST'])
def mapconfirm(prediction_nr=None): 
    return predict(and_confirm=int(prediction_nr))


cache = SqliteCache("oracle_cache") 
try:
    mysqldb = dataset.connect(c.LOCATIONDB) 
    mysqldb.query("set names 'utf8'") # Might help
except sqlalchemy.exc.OperationalError:
    print "No connection to mysql. Cache better work or it will fail."

np.set_printoptions(formatter={'float': lambda x: "{0:0.4f}".format(x)}, linewidth=155)
    