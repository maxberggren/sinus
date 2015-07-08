#!/usr/bin/python
# -*- coding: utf-8 -*-
import config as c
import dataset
import geocode    
from geocode import latlon
import math
import numpy as np
from numpy import inf
import pandas as pd
from sqlite_cache import SqliteCache

from mpl_toolkits.basemap import Basemap, cm, maskoceans
import matplotlib.cm as cm
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.colors import LogNorm
from matplotlib.ticker import LogFormatter
from mpl_toolkits.axes_grid1 import make_axes_locatable
from scipy import ndimage
import matplotlib.pyplot as plt

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

def gen_grid(lats, lons, xyRatio=1.8, no_zeros=False):
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
    
    grids = []
    
    for query in queries:
        word, source = query
        print "letar efter {} i {}".format(word, source)
        word = word.replace("NOT ", "")
        
        grid = cache.get(str(query) + str(xBins))

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
                cache.set(str(query) + str(xBins), grid, timeout=60*60*24*31)   
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
                cache.set(str(query) + str(xBins), grid, timeout=60*60*24*31) 
                grids.append(grid)
            
    return grids        

def colorCycle(i, scatter=False):
    colors = ['Reds', 'Blues', 'BuGn', 'Purples', 'PuRd']
    if scatter:
        colors = ['blue', 'red', 'green', 'magenta', 'cyan']
    return colors[i % len(colors)]
    
 
def make_map(matrix, name):
    
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
    m.fillcontinents(color='white',
                     lake_color='black',
                     zorder=0)
    m.drawmapboundary(fill_color='black')
    
    lon_bins_2d, lat_bins_2d = np.meshgrid(lon_bins, 
                                           lat_bins)
    xs, ys = m(lon_bins_2d, lat_bins_2d)
    xs = xs[0:density.shape[0], 0:density.shape[1]]
    ys = ys[0:density.shape[0], 0:density.shape[1]]
            
    # Colormap transparency
    theCM = cm.get_cmap(colorCycle(0)) 
    theCM._init()
    alphas = np.abs(np.linspace(0, 1.0, theCM.N))
    theCM._lut[:-3,-1] = alphas
    
    p = plt.pcolor(xs, ys, density, 
                   cmap=theCM, 
                   #norm=LogNorm(), 
                   antialiased=True)                    
    
    fig.tight_layout(pad=2.5, w_pad=0.1, h_pad=0.0) 
    
    plt.savefig("sinusGUIapp/static/maps/" + name + ".pdf", 
                dpi=100, 
                bbox_inches='tight')
                



cache = SqliteCache("oracle_cache") 
mysqldb = dataset.connect(c.LOCATIONDB) 
mysqldb.query("set names 'utf8'") # Might help
np.set_printoptions(formatter={'float': lambda x: "{0:0.5f}".format(x)}, linewidth=155)

xBins = 20
queries = [#('NOT sovde', 'Moderna dialektskillnader - SOVDE.xlsx'),
           ('nästkusin', 'DB'),
           ('NOT tyken', 'DB'),
           #('äppelpaj', 'DB'),
           ('gräddbullar', 'DB'),
           #('fara', 'DB'),
           #('NOT böla', 'DB'),
           ('söndrig', 'Moderna dialektskillnader - SONDRIG.xlsx'),
           ('nyckelen', 'DB'),	
           ('chokladet', 'DB'),
           ('NOT svalen', 'DB'),
           #('NOT böla', 'DB'),
           ('NOT poängpromenad', 'DB')
           ]
           
#[3.0261368612279473, 9.0789762435053003, 3.4817350502751632, 5.2375385048799039, 3.9100301581369665, 2.5767977201749948, 9.0325154827791145, 9.2289144202172508]

          
grids = get_grids(queries)
print [entropy(m) for m in grids] # Show entropy for the matrixes
product = np.ones(grids[0].shape)      
 
def negative(query):
    return query[0][0:4] == "NOT "

# Multiply all distributions into a final one      
for grid, query in zip(grids, queries): 
    if negative(query):
        #print not_in(grid)
        #make_map(not_in(grid), query[0]) 
        product = np.multiply(product, not_in(grid)) 
    else:
        #print grid
        #make_map(grid, query[0]) 
        product = np.multiply(product, grid) 
    
print normalize(product)
density = normalize(product)
make_map(density, "product")




