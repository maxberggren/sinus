#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import division
import matplotlib.cm as cm
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.colors import LogNorm
from matplotlib.ticker import LogFormatter
from mpl_toolkits.axes_grid1 import make_axes_locatable
from scipy import ndimage
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sinusGUIapp import app
from flask import Flask, jsonify, make_response, request, render_template, redirect, url_for
from werkzeug import secure_filename
from textLoc26 import *
import math
from werkzeug import secure_filename
import numpy.ma as ma
import binascii
from matplotlib.patches import Polygon
import dataset
import codecs
from sets import Set
import requests
from images2gif import writeGif
from PIL import Image
import os
import config as c
from sqlite_cache import SqliteCache
import sqlalchemy
from itertools import groupby
from shapely.geometry import Point, Polygon, MultiPoint, MultiPolygon
from shapely.prepared import prep
from matplotlib.collections import PatchCollection
from descartes import PolygonPatch
import json
import datetime
from pysal.esda.mapclassify import Natural_Breaks
from geocode import latlon
import geocode    
from scipy.stats import mode
 
def timing(f):
    def wrap(*args):
        time1 = time.time()
        ret = f(*args)
        time2 = time.time()
        print '%s function took %0.3f ms' % (f.func_name, (time2-time1)*1000.0)
        return ret
    return wrap
       
def colorCycle(i, scatter=False, hotcold=False):
    colors = ['Reds', 'Blues', 'BuGn', 'Purples', 'PuRd']
    if scatter:
        colors = ['blue', 'red', 'green', 'magenta', 'cyan']
    return colors[i % len(colors)]
                         
def dateHistogram(dates, filename):
    """ Create histogram of given dates

    Parameters
    ----------
    dates : list
        dates to make histogram over
    filename : str
        the filename it should be saved to
    """

    startYear = 2000
    endYear = datetime.datetime.now().year
    years = [date.year for date in dates]
    fig = plt.figure(figsize=(8,6))
    plt.hist(years, bins=range(startYear, endYear+1))
    plt.xlabel(u'År')
    plt.ylabel('Frekvens')
    plt.xlim(startYear, endYear)
    filename = "sinusGUIapp/static/maps/" + filename +"_hist.png"
    plt.savefig(filename, dpi=100)


def emptyFolder(folder):
    """ Empty folder so we won't run out of hdd space

    Parameters
    ----------
    folder : str
        path to folder
    """
    
    for the_file in os.listdir(folder):
        file_path = os.path.join(folder, the_file)
        try:
            # if older than a day
            if os.stat(os.path.join(file_path,the_file)).st_mtime < now - 86400:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
        except Exception as e:
            print e


def getSynonyms(query):
    """ Connect to Gavagai API to get synonyms

    Parameters
    ----------
    query : str
        term to be looked up with gavagai

    Returns
    -------
    synonyms : list
        list with synonyms
    """

    try:
        r = requests.get('https://ethersource.gavagai.se/ethersource/'
                         'rest/v2/suggestTerms?'
                         'apiKey='+c.ES_APIKEY+'&'
                         'terms='+query+'&'
                         'language=SV', 
                         auth=(c.ES_USER, c.ES_PASSW))
        
        synonyms = [row['word'] for row in r.json()['paradigmaticNeighbours']]
    except:
        synonyms = [""]
    
    return synonyms
    
    
def kwic(text, word, source):
    """ Make KeyWord In Context from a text and a keyword

    Parameters
    ----------
    text : str
        full text to be trunicated to a kwic
    word : str
        word to be highlighted
    source : str
        source of the text to be prepended the kwic e.g. [twingly]

    Returns
    -------
    kwic : str
        e.g. [twingly] this is a text with WORD to be highlighted
    """
    
    text = text.lower()
    #text = text.replace("å", "a").replace("ä", "a").replace("ö", "o")
    
    if " or " in word.lower():
        words = word.lower().split(" or ")
    else:
        words = [word]
        
    if type(text) is str:
        try:
            text = text.decode("utf-8")
        except:
            return ""
          
    kwics = []  
    for word in words:    
        left, sep, right = text.partition(word.lower().replace('"', ""))
        if sep:
            kwics.append("[" + source + "] " + left[-26:] + sep + right[:46])
            
    return "<br />".join(kwics)

def genShapefileImg(data, ranks, words, zoom, binThreshold, binModel):
    """ Generate an image with shapefiles as bins 

    Parameters
    ----------
    data : tuple
        tuple with lists of the coordinates
    words : list
        list of words corresponding to the lists in 
        the tuple coordinatesByWord.
    zoom : int
        1 if the user wants the map to be zoomed in 
        around the avalible data. if 0 it defaults
        to around sweden.
    binThreshold : int
        threshold required for a bin to count and be plotted

    Returns
    -------
    fewResults : bool
        true if the template needs to generate an error
    filename : str
        name of the file generated
    gifFileName : always None for compability   
    """
    
    
    def custom_colorbar(cmap, ncolors, labels, **kwargs):    
        """ Create a custom, discretized colorbar with correctly 
            formatted/aligned labels.
        
            cmap: the matplotlib colormap object you plan on using 
            for your graph
            ncolors: (int) the number of discrete colors available
            labels: the list of labels for the colorbar. Should be 
            the same length as ncolors.
        """
        from matplotlib.colors import BoundaryNorm
        from matplotlib.cm import ScalarMappable
            
        norm = BoundaryNorm(range(0, ncolors), cmap.N)
        mappable = ScalarMappable(cmap=cmap, norm=norm)
        mappable.set_array([])
        mappable.set_clim(-0.5, ncolors+0.5)
        colorbar = plt.colorbar(mappable, **kwargs)
        colorbar.set_ticks(np.linspace(0, ncolors, ncolors+1)+0.5)
        colorbar.set_ticklabels(range(0, ncolors))
        colorbar.set_ticklabels(labels)
        
        return colorbar
    
    def opacify(cmap):
        """ Add opacity to a colormap going from full opacity to no opacity """
        
        cmap._init()
        alphas = np.abs(np.linspace(0, 1.0, cmap.N))
        cmap._lut[:-3,-1] = alphas
        return cmap
    
    def genGrid(koordinater, xBins=10, xyRatio=1.8):
        """ Generate grid from coordinates """
        
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
    
    @timing
    def sum1(input):
        """ Sum all elements in matrix """
        
        try:
            return sum(map(sum, input))
        except Exception:
            return sum(input)
    
    @timing    
    def normalize(matrix):
        """ Divide all elements by sum of all elements """
        return matrix / sum1(matrix)        
    
    @timing    
    def getEnoughData():
        """ Get alot of data until a suitable null hypothesis has converged """
        
        convergenceCrit = 1e-9 
        old_matrix = genGrid([])
        i, j, k = 0, 0, 0
        try:        
            coordinates = []

            for source in mysqldb.query("SELECT * from blogs "
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
                        print k
                        
                    # change between every 1000 new datapoints 
                    # should be less than 1e-9 = 0.0000001 %
                    if total_error < convergenceCrit and total_error != 0.0:
                       print "converged!"
                       return coordinates
                       break
                    
                    old_matrix = normalize(genGrid(coordinates))
                    
        except KeyboardInterrupt:
            print "Avbryter..."        


    
    lds, coord_count, breaks = [], {}, {}

    # If ranks not sent in, assume rank 2
    if not ranks:
        ranks = ()
        for batch in data:
            ranks = ranks + ([2]*len(batch),)

    # Put coordinates into DFs 
    for d, word, rank in zip(data, words, ranks):
        lon, lat = zip(*d)
        coord_count[word] = len(d)
        ld = pd.DataFrame({'longitude': lon, 
                           'latitude': lat,
                           'rank': rank})
        ld['word'] = word
        lds.append(ld)
        
    lds = pd.concat(lds) # One DF with all coordinates
    
    if zoom: # User choose to zoom map to iteresting points
        padding = 0.5
        llcrnrlon = lds['longitude'].quantile(0.05) - padding
        llcrnrlat = lds['latitude'].quantile(0.20) - padding
        urcrnrlon = lds['longitude'].quantile(0.88) + padding
        urcrnrlat = lds['latitude'].quantile(0.83) + padding
        resolution = "h"
        area_thresh = 50
    else: #
        llcrnrlon = 8
        llcrnrlat = 54.5
        urcrnrlon = 26
        urcrnrlat = 69.5
        resolution = 'i'
        area_thresh = 250
    
    m = Basemap(projection='merc',
                resolution=resolution, 
                area_thresh=area_thresh,
                llcrnrlon=llcrnrlon, 
                llcrnrlat=llcrnrlat,
                urcrnrlon=urcrnrlon, 
                urcrnrlat=urcrnrlat) 
    
    # County data
    _out = m.readshapefile('shapedata/alla_lan/alla_lan_Std', 
                           name='countys', drawbounds=False, 
                           color='none', zorder=2)
    
    # Municipality data
    _out = m.readshapefile('shapedata/Kommuner_SCB/Kommuner_SCB_Std', 
                           name='muni', drawbounds=False, 
                           color='none', zorder=3)
    _out = m.readshapefile('shapedata/N2000-Kartdata-master/NO_Kommuner_pol_latlng', 
                           name='muni_no', drawbounds=False, 
                           color='none', zorder=3)
    _out = m.readshapefile('shapedata/finland/finland-11000000-administrative-regions', 
                           name='muni_fi', drawbounds=False, 
                           color='none', zorder=3)
    
    finnishMunis = []
    # If a municipality has a Swedish name, 
    # take that, if not take Finnish name.
    for r in m.muni_fi_info:
        if r['Kunta_ni2'] != "N_A":
            finnishMunis.append(r['Kunta_ni2'])
        else:
            finnishMunis.append(r['Kunta_ni1'])
            
    # Municipality DF (SE + NO + FI)
    polygons = [Polygon(p) for p in m.muni] + \ 
               [Polygon(p) for p in m.muni_no] + \ 
               [Polygon(p) for p in m.muni_fi] 
               
    names = [r['KNNAMN'] for r in m.muni_info] + \ 
            [r['NAVN'] for r in m.muni_no_info] + \ 
            finnishMunis # FI
            
    areas = [r['LANDAREAKM'] for r in m.muni_info] + \ 
            [r['Shape_Area'] for r in m.muni_no_info] + \ 
            [0 for r in m.muni_fi_info] # FI
    
    df_map_muni = pd.DataFrame({'poly': polygons, 'name': names, 'area': areas})
    
    # County DF
    df_map_county = pd.DataFrame({
        'poly': [Polygon(countys_points) for countys_points in m.countys],
        'name': [r['LAN_NAMN'] for r in m.countys_info]})

    # Fix encoding
    df_map_muni['name'] = df_map_muni.apply(lambda row: row['name'].decode('latin-1'), axis=1)
    df_map_county['name'] = df_map_county.apply(lambda row: row['name'].decode('latin-1'), axis=1)
    
    @timing
    def mapPointsToPoly(coordinates_df, poly_df):
        """ Take coordiates DF and put into polygon DF """
        
        mapped_points, hood_polygons = {}, {}
        ranks = {}
        
        uniqeWords = coordinates_df['word'].unique()
        
        for word, ld in coordinates_df.groupby(['word']):             
            # Convert our latitude and longitude into Basemap cartesian map coordinates
            points = [Point(m(mapped_x, mapped_y)) 
                      for mapped_x, mapped_y 
                      in zip(ld['longitude'], ld['latitude'])]
            
            # If we did not get ranked data, assume rank 2          
            try:
                mapped_points[word] = pd.DataFrame({'points': points,
                                                    'rank': ld['rank']})
            except KeyError:
                mapped_points[word] = pd.DataFrame({'points': points})
                mapped_points[word]['rank'] = 2
                                                   
            # Use prep to optimize polygons for faster computation
            hood_polygons[word] = prep(MultiPolygon(list(poly_df['poly'].values)))
            
            # Filter out the points that do not fall within the map we're making
            #mapped_points[word] = [p for p in all_points[word] if hood_polygons[word].contains(p)]
            #ranks[word] = [r for p, r in zip(all_points[word], ranks[word]) 
            #               if hood_polygons[word].contains(p)]


        def num_of_contained_points(apolygon, mapped_points):
            """ Counts number of points that fall into a polygon
                Points with rank >= 4 gets just half weight """

            num = 0            
            for rank, ld in mapped_points.groupby(['rank']):  
                if rank >= 4: # Downweight bad ranked points
                    num += int(0.5*len(filter(prep(apolygon).contains, ld['points'])))
                else:
                    num += int(len(filter(prep(apolygon).contains, ld['points'])))
                    
            return num
        
        for word in uniqeWords:
            poly_df[word] = poly_df['poly'].apply(num_of_contained_points, 
                                                  args=(mapped_points[word],))
            poly_df[word][poly_df[word] < binThreshold] = 0
            
        return poly_df
        
        
    df_map_muni = mapPointsToPoly(lds, df_map_muni)
    df_map_county = mapPointsToPoly(lds, df_map_county)

    print words
        
    ### Only one word: compare to country average
    if len(words) == 1: 
        
        fname_muni = "null_hypothesis_muni_df.pkl" 
        fname_county = "null_hypothesis_county_df.pkl" 
        
        if not os.path.isfile(fname_muni):
            temp_latlon_df = pd.DataFrame(getEnoughData(), 
                                          columns=['longitude', 'latitude'])
            temp_latlon_df['word'] = "expected"
            
            # Make dataframe and pickle 
            null_h_muni_df = mapPointsToPoly(temp_latlon_df, df_map_muni)
            null_h_county_df = mapPointsToPoly(temp_latlon_df, df_map_county)
            null_h_county_df.to_pickle(fname_county)
            null_h_muni_df.to_pickle(fname_muni)
        else:
            # Read from pickle
            null_h_muni_df = pd.io.pickle.read_pickle(fname_muni)
            null_h_county_df = pd.io.pickle.read_pickle(fname_county)
            
        def deviationFromAverage(df_map, avg):
            # Expected is to see a word according to country average
            df_map['expected'] = avg['expected']        
            df_map = df_map[df_map['expected'] > 0] # remove zeros
            # Calculate percentages
            df_map['expected'] = df_map['expected'].astype('float')\
                                                   .div(df_map['expected'].sum(axis=0))
            # Words will here just be the one word
            df_map[words] = df_map[words].astype('float')\
                                         .div(df_map[words].sum(axis=0))
            df_map[words] = df_map[words].div(df_map['expected'], axis='index')
            del df_map['expected']
            return df_map
         
        # Since only one word, calculate deviation from country average   
        df_map_muni = deviationFromAverage(df_map_muni, null_h_muni_df)
        df_map_county = deviationFromAverage(df_map_county, null_h_county_df)
        
        breaks['muni'], breaks['county'] = {}, {}
               
        for word in words:    
            countyMax = float(df_map_county[word].max(axis=0))
            muniMax = float(df_map_muni[word].max(axis=0))
            
            breaks['muni'][word] = [0., 0.5, 1., muniMax/2.0, muniMax]
            breaks['county'][word] = [0., 0.5, 1., countyMax/2.0, countyMax]
        
        labels = ['Below avg.', '', 'Avg.', '', 'Above avg.']    
        
    else:     
        ### More than one word: compare words against each other 
           
        # Get total occurencies in every county/municipality
        df_map_county["sum"] = df_map_county[words].sum(axis=1)
        df_map_muni["sum"] = df_map_muni[words].sum(axis=1)
            
        def df_percent(df_map):
            # Handle divide by zero as zeros
            df_map[words] = df_map[words].astype('float').div(df_map["sum"].replace({ 0 : np.nan })
                                                              .astype('float'), axis='index')
            df_map[words] = df_map[words].fillna(0)
            df_map.loc[df_map['sum'] < binThreshold, words] = 0
                        
            return df_map
        
        # Convert to percentages and skip where there is none
        df_map_county = df_percent(df_map_county)
        df_map_muni = df_percent(df_map_muni)

        breaks['muni'], breaks['county'] = {}, {}
               
        for word in words:    
            breaks['muni'][word] = [0., 0.25, 0.5, 0.75, 1.0]
            breaks['county'][word] = [0., 0.25, 0.5, 0.75, 1.0]
            
        labels = ['None', 'Low', 'Medium', 'High', 'Very high']
        
    def self_categorize(entry, breaks):
        """ Put percent into a category (breaks) """
        
        for i in range(len(breaks)-1):
            if entry > breaks[i] and entry <= breaks[i+1]:
                return i
        return -1 # under or over break interval
    
    def genFallbackMap(df, word):
        """ Generate fallback map from municipalitys """
        hierarchy = pd.io.excel.read_excel("hierarchy.xlsx")

        def getMuni(df, level, key):
            return df.groupby(level).get_group(key)['Kommun'].unique()

        def getParentMean(df, municipality, level, word):
            try:
                parent = hierarchy.loc[hierarchy[u'Kommun'] == municipality][level].values[0]
                if not parent == "-":
                    munis = getMuni(hierarchy, level, parent)
                    parentData = df.loc[df['name'].isin(munis), word]
                    mean = np.mean(parentData)  
                    return mean
                else:
                    return None
            except IndexError:
                return None

        def updateDF(df, word):
            """ Find municipalitys with no hits and update according to rule """
            new_df = df.copy(deep=True)

            for parentLevels in [[u"Stadsomland", u"Gymnasieort"], 
                                 [u"LA-region", u"FA-region"], 
                                 [u"NDR", u"A", u"Tidningsdistrikt", u"Postnummer", u"P"], 
                                 [u"Län", u"Landskap"]]:
                                                  
                for muni in df[df[word] == 0.0]['name'].unique(): 
                
                    # Merge the mean of every parent level
                    mean = [getParentMean(df, muni, parentLevel, word) 
                            for parentLevel in parentLevels]
                    mean = np.array(mean)
                    mean = mean[mean != np.array(None)] # Remove Nones 
                    #mean = mean[mean != 0.0] # Remove zeroes
                    mean = np.mean(mean)
    
                    # Update municipality with fallback according to rule
                    if mean and mean != 0.0 and mean != True:
                        new_df.loc[new_df['name'] == muni, word] = mean
                        
            return new_df 

        df = updateDF(df, word)

        return df
    
    fig = plt.figure(figsize=(3.25*len(words),6))
    
    for i, word in enumerate(words):

        # Create columns stating which break precentages belongs to
        df_map_county['bins_'+word] = df_map_county[word].apply(self_categorize, 
                                                                args=(breaks['county'][word],))
        df_map_muni['bins_'+word] = df_map_muni[word].apply(self_categorize, 
                                                             args=(breaks['muni'][word],))      
        # Also create a fallback DF if needed
        if binModel == 'lab':
            df_map_fallback = genFallbackMap(df_map_muni, word)            
            df_map_fallback['bins_'+word] = df_map_fallback[word].apply(self_categorize, 
                                                                        args=(breaks['muni'][word],)) 
                                                                                                              
        # Subplot for every word
        ax = fig.add_subplot(1, len(words), int(i+1), axisbg='w', frame_on=False)
        ax.set_title(u"{word} - hits: {hits}".format(word=word.replace(" OR ", "/"), 
                                                     hits=coord_count[word]), 
                     y=1.01, fontsize=9)
    
        colormap = colorCycle(i)
        if len(words) == 1:
            colormap = "coolwarm"
            
        cmap = plt.get_cmap(colormap)
        #cmap = opacify(cmap) # Add opacity to colormap
                
        if binModel == 'municipality+county':
            # County fallback for empty bins
            shapesToPutOnMap = [df_map_county, df_map_muni]
        elif binModel == 'county':
            # Just use countys
            shapesToPutOnMap = [df_map_county]
        elif binModel == 'lab':
            # Lab
            shapesToPutOnMap = [df_map_fallback]
        else: 
            shapesToPutOnMap = [df_map_muni]
        
        # Put all shapes on map
        for df_map in shapesToPutOnMap:
            
            # Create patches
            df_map['patches'] = df_map['poly'].map(lambda x: PolygonPatch(x, 
                                                                          ec='#111111', 
                                                                          lw=0, 
                                                                          alpha=0, 
                                                                          zorder=4))
            pc = PatchCollection(df_map['patches'], match_original=True)
            # Apply our custom color values onto the patch collection
            cmaps = (df_map['bins_'+word].values - 
                       df_map['bins_'+word].values.min())/(
                           df_map['bins_'+word].values.max()-
                               float(df_map['bins_'+word].values.min()))
                                           
            cmap_list = []
            for val in cmaps:
                if val == 0:
                    cmap_list.append('none')
                else:
                    cmap_list.append(cmap(val))
            
            #cmap_list = [cmap(val) for val in cmaps]                    
            pc.set_facecolor(cmap_list)
            ax.add_collection(pc)
            
        m.drawcoastlines(linewidth=0.5)
        m.drawcountries()
        m.drawstates()
        m.drawmapboundary()
        m.fillcontinents(color='white', lake_color='black', zorder=0)
        m.drawmapboundary(fill_color='black')
    
        divider = make_axes_locatable(plt.gca())
        cax = divider.append_axes("bottom", 
                                  "2%", 
                                  pad="2.5%")
                        
        cbar = custom_colorbar(cmap, ncolors=len(labels)+1, 
                               labels=labels, 
                               orientation='horizontal', 
                               cax=cax)
        cbar.ax.tick_params(labelsize=6)
        
            
    try:
        fig.tight_layout(pad=2.5, w_pad=0.1, h_pad=0.0) 
    except:
        pass
    
    plt.plot()

    # Generate randomized filename
    filename = "_".join(words) + "_"
    filename += binascii.b2a_hex(os.urandom(15))[:10]
    filename = secure_filename(filename)
    
    #emptyFolder('sinusGUIapp/static/maps/')
    plt.savefig("sinusGUIapp/static/maps/" + filename +".png", 
                dpi=100)
    plt.savefig("sinusGUIapp/static/maps/" + filename +".pdf", 
                dpi=100, 
                bbox_inches='tight')
    plt.close('all')

    #return fewResults, filenameSF, gifFileName 
    return False, filename, None 


def genGridImg(coordinatesByWord, xBins, words, zoom,
              xyRatio, blurFactor, minCoordinates, 
              scatter, hits, chunks=1, dates=None, binThreshold=5):

    """ Generate the images i.e. the main image, the 
        time series gif and the histogram.
        
        NOTE: going to be depreciated alltogether!

    Parameters
    ----------
    coordinatesByWord : tuple
        tuple with lists of the coordinates
    xBins : int
        how many bins there should be on the x-axis
    words : list
        list of words corresponding to the lists in 
        the tuple coordinatesByWord.
    zoom : int
        1 if the user wants the map to be zoomed in 
        around the avalible data. if 0 it defaults
        to around sweden.
    xyRatio : int
        correction to make the bins square in
        mercurator projection map
    blurFactor : float
        if blurring the 2d bin data should be applied
        do it by this amount
    minCoordinates : int
        threshold under where the map falls back to
        making an scatterplot since the binplot 
        would be kinda useless
    scatter : int
        1 if manual override so scatterplot 
        should be used
    hits : dict
        storing how many hits a keyword has
    chunks : int
        how many chunks that the dates should be split
        into when generating a gif
    dates : list
        the dates for the histogram
    binThreshold : int
        threshold required for a bin to count and be plotted

    Returns
    -------
    fewResults : bool
        true if a keyword had to few hits in the
        documents database
    filename : str
        name of the file that should be saved (main image)
    gifFileName : str
        filename of the gif
    """

    # Time series is only generated when just one word is searched for
    if chunks > 1 and len(coordinatesByWord) != 1:
        return False, None, None
        
    fewResults = False
    gifFileName = None 
          
    lon_bins = np.linspace(8, 26, xBins)
    lat_bins = np.linspace(54.5, 69.5, xBins*xyRatio)
    gifFilenames = []
    nBins = len(lon_bins)*len(lat_bins)

    if dates:
        # Chunking only supported when just one word is sent in
        ts = [{'date':str(date),'value':value} for date, value in zip(dates, coordinatesByWord[0])]
        
        months = []
        monthCoordinates = []
        for k, v in groupby(ts, key=lambda x:x['date'][:7]):
            months.append(k)
            monthCoordinates.append([c['value'] for c in list(v)])
            
        #dates = np.array_split(dates, chunks)
        dates = monthCoordinates
        
        if chunks == 1:
            dates = [dates]
        else:
            chunks = len(dates)

    for chunk in range(chunks):
            
        totCoordinates = 0
        totDensity = np.ones((len(lat_bins)-1, 
                              len(lon_bins)-1))*0.00000000000000001
        
        # For every word
        for kordinater in coordinatesByWord:
            # Coordinates to be put into chunks 
            if chunks == 1:
                kordinater = [kordinater]  
            else:
                kordinater = dates  
            
            totCoordinates += len(kordinater[chunk])
            
            lons, lats = zip(*kordinater[chunk])
            subdensity, _, _ = np.histogram2d(lats, lons, 
                                              [lat_bins, lon_bins])
            totDensity += subdensity

        # Filter out bins with to few hits
        totDensity[totDensity < binThreshold] = 9999999999999 
                
        #totDensity = ndimage.gaussian_filter(totDensity, blurFactor)
            
        fig = plt.figure(figsize=(3.25*len(coordinatesByWord),6))
        
        for i, kordinater in enumerate(coordinatesByWord):
            word = words[i]

            if chunks == 1:
                kordinater = [kordinater]
            else:
                kordinater = dates
                            
            if dates:
                try:
                    fig.suptitle(months[chunk],fontsize=9)              
                except: # Some dates might be wierd in the DB
                    pass
            
            lons, lats = zip(*kordinater[chunk])             
            lons = np.array(lons)
            lats = np.array(lats)
        
            ax = fig.add_subplot(1, len(coordinatesByWord), int(i+1))
            ax.set_title(u"{word} - hits: {hits}".format(word=word, hits=len(kordinater[chunk])), 
                         y=1.01, 
                         fontsize=9)
            if zoom:
                llcrnrlon = np.amin(lons)
                llcrnrlat = np.amin(lats)
                urcrnrlon = np.amax(lons)
                urcrnrlat = np.amax(lats)
            else:
                llcrnrlon = 8
                llcrnrlat = 54.5
                urcrnrlon = 26
                urcrnrlat = 69.5
            
            m = Basemap(projection='merc',
                        resolution='i', 
                        area_thresh=250,
                        llcrnrlon=llcrnrlon, 
                        llcrnrlat=llcrnrlat,
                        urcrnrlon=urcrnrlon, 
                        urcrnrlat=urcrnrlat,)   
            
            m.drawcoastlines(linewidth=0.5)
            m.drawcountries()
            m.drawmapboundary()
            m.fillcontinents(color='white',
                             lake_color='black',
                             zorder=0)
            m.drawmapboundary(fill_color='black')
            
            density, _, _ = np.histogram2d(lats, 
                                           lons, 
                                           [lat_bins, 
                                            lon_bins])
    
            #density = ndimage.gaussian_filter(density, blurFactor)
    
            lon_bins_2d, lat_bins_2d = np.meshgrid(lon_bins, 
                                                   lat_bins)
            xs, ys = m(lon_bins_2d, lat_bins_2d)
            xs = xs[0:density.shape[0], 0:density.shape[1]]
            ys = ys[0:density.shape[0], 0:density.shape[1]]
                    
            # Colormap transparency
            theCM = cm.get_cmap(colorCycle(i))
            theCM._init()
            alphas = np.abs(np.linspace(0, 1.0, theCM.N))
            theCM._lut[:-3,-1] = alphas
            
            # SCATTERPLOT if to few coordinates or manual override
            if (minCoordinates < 50 and scatter is None) or scatter == 1:
                x1, y1 = m(lons, lats) 
                m.scatter(x1[0:1000], 
                          y1[0:1000], 
                          alpha=1, 
                          c=colorCycle(i, scatter=True), 
                          s=10,
                          edgecolors='none')
                fewResults = True
                
            else: # 2DHISTPLOT if enough coordinates
                if len(coordinatesByWord) == 1:
                    # One term means logplot
                    if chunks != 1: 
                        # For animation, we need to fix 
                        # z-axis if this is part of a chunking
                        p = plt.pcolor(xs, ys, density, 
                                       cmap=theCM, 
                                       norm=LogNorm(), 
                                       vmin=1, 
                                       vmax=hits[words[i]],
                                       antialiased=True)
                    else: 
                        p = plt.pcolor(xs, ys, density, 
                                       cmap=theCM, 
                                       norm=LogNorm(), 
                                       vmin=1, 
                                       antialiased=True)                    
                else:
                    # Relative frequency when more terms
                    pctFrq = density/totDensity
                    p = plt.pcolor(xs, ys, pctFrq,
                                   antialiased=True,
                                   cmap=theCM)
    
                # Add colorbar
                divider = make_axes_locatable(plt.gca())
                cax = divider.append_axes("bottom", 
                                          "2%", 
                                          pad="2.5%")
                colorbar = plt.colorbar(p, 
                                        cax=cax, 
                                        orientation='horizontal')
                
                # And fixed ticks
                if len(coordinatesByWord) != 1:
                    colorbar.set_ticks([0, 0.25, 0.5, 0.75, 1])            
                    colorbar.set_ticklabels(["0 %",
                                             "25 %",
                                             "50 %", 
                                             "75 %",
                                             "100 %"])
                
                colorbar.ax.tick_params(labelsize=6) 
            
        fig.tight_layout(pad=2.5, w_pad=0.1, h_pad=0.0) 

        # Generate randomized filename
        filename = "_".join(words) + "_"
        filename += binascii.b2a_hex(os.urandom(15))[:10]
        filename = secure_filename(filename)
    
        # Create images
        if chunks > 1: # We are saving a timeseries
        
            gifFilename = "sinusGUIapp/static/maps/" 
            gifFilename += filename +"_"+str(chunk)+".png"
                          
            gifFilenames.append(gifFilename) # Save for giffing
            plt.savefig(gifFilename, dpi=150)
            
        else: # Just saving one image
            #emptyFolder('sinusGUIapp/static/maps/')
            plt.savefig("sinusGUIapp/static/maps/" + filename +".png", 
                        dpi=100)
            plt.savefig("sinusGUIapp/static/maps/" + filename +".pdf", 
                        dpi=100, 
                        bbox_inches='tight')

    # If timeseries created - GIFfify it!
    if chunks > 1: 
        #gifFilenames = gifFilenames + gifFilenames[::-1]
        gifFilenames = gifFilenames
        images = [Image.open(fn) for fn in gifFilenames]
        gif2file = "sinusGUIapp/static/maps/" + filename +".gif"
        writeGif(gif2file, images, duration=0.5)
        gifFileName = filename
        
    plt.close('all')
    
    return fewResults, filename, gifFileName

def getOperators(queryWords):
    operators = [o.strip() for o in queryWords 
                           if "age:" in o 
                               or "gender:" in o
                               or "xbins:" in o
                               or "scatter:" in o
                               or "zoom:" in o
                               or "rankthreshold:" in o
                               or "datespan:" in o
                               or "binthreshold:" in o
                               or "bintype:" in o
                               or "binmodel:" in o
                               or "hitsthreshold:" in o]
                               
    queryWords = [w.strip() for w in queryWords 
                            if "age:" not in w 
                               and "gender:" not in w
                               and "xbins:" not in w
                               and "scatter:" not in w
                               and "zoom:" not in w
                               and "rankthreshold:" not in w
                               and "datespan:" not in w
                               and "binthreshold:" not in w
                               and "bintype:" not in w
                               and "binmodel:" not in w
                               and "hitsthreshold:" not in w]
    
    try:
        xbins = int([o.split(":")[1].strip()
                    for o in operators if "xbins:" in o][0])
    except:
        xbins = 20

    try:
        scatter = int([o.split(":")[1].strip()
                      for o in operators if "scatter:" in o][0])
    except:
        scatter = None
    try:
        zoom = int([o.split(":")[1].strip()
               for o in operators if "zoom:" in o][0])
    except:
        zoom = None
    try:
        rankthreshold = int([o.split(":")[1].strip()
               for o in operators if "rankthreshold:" in o][0])
    except:
        rankthreshold = 3
    try:
        datespan = [o.split(":")[1].strip()
                   for o in operators if "datespan:" in o][0]
    except:
        datespan = None

    try:
        binThreshold = int([o.split(":")[1].strip()
               for o in operators if "binthreshold:" in o][0])
    except:
        binThreshold = 5
        
    try:
        binType = [o.split(":")[1].strip()
               for o in operators if "bintype:" in o][0]
    except:
        binType = "shape"
        
    try:
        binModel = [o.split(":")[1].strip()
               for o in operators if "binmodel:" in o][0]
    except:
        binModel = None
        
    try:
        hitsThreshold = int([o.split(":")[1].strip()
               for o in operators if "hitsthreshold:" in o][0])
    except:
        hitsThreshold = 50
        
    return operators, queryWords, xbins, scatter, zoom, rankthreshold, datespan, binThreshold, binType, binModel, hitsThreshold

def getStats():
    cacheTimeout = 24*60*60 # 1 day
    stats = {}
    
    # Get sourcecount for sources that have lon lat
    key = "sourceswithlatlon"
    if not cache.get(key):
        stats[key] = []
        while True:
            try:
                result = mysqldb.query("SELECT source, rank, COUNT(*) "
                                       "as count FROM blogs "
                                       "WHERE longitude is not NULL "
                                       "AND rank <> 9999 "
                                       "GROUP BY source, rank ORDER BY count DESC")
                break
            except sqlalchemy.exc.OperationalError:
                pass
                  
        for row in result:
            stats[key].append(row)
        
        cache.set(key, stats[key], timeout=cacheTimeout) # cache for 1 hours    
    else:
        stats[key] = cache.get(key)
    
    # Get sourcecount for sources that yet have no lat lon
    key = "sourceswithoutlatlon"
    if not cache.get(key):
        stats[key] = []
        result = mysqldb.query("SELECT source, rank, COUNT(*) as count FROM blogs "
                               "WHERE "
                               "    (longitude is NULL AND rank <> 9999 "
                               "     AND noCoordinate is NULL) "
                               "AND "
                               "    (city is not NULL OR "
                               "     municipality is not NULL "
                               "     OR county is not NULL) "
                               "GROUP BY source, rank ORDER BY count DESC") 
        for row in result:
            stats[key].append(row)
        
        cache.set(key, stats[key], timeout=cacheTimeout) # cache for 1 hours    
    else:
        stats[key] = cache.get(key)

    # Get sourcecount for sources that yet have no lat lon
    key = "sourceswithoutanymetadata"
    if not cache.get(key):
        stats[key] = []
        result = mysqldb.query("SELECT source, rank, COUNT(*) as count FROM blogs "
                               "WHERE "
                               "( (country = '' and municipality = '' "
                               "   and county = '' and city = '') "
                               "  OR (country is NULL and municipality is NULL "
                               "      and county is NULL and city is NULL)"
                               ") "
                               "AND longitude is NULL AND latitude is NULL AND "
                               "rank <> 9999 "
                               "GROUP BY source, rank ORDER BY count DESC") 
        for row in result:
            stats[key].append(row)
        
        cache.set(key, stats[key], timeout=cacheTimeout) # cache for 1 hours    
    else:
        stats[key] = cache.get(key)

    return stats

def getData(words, xBins=None, scatter=None, zoom=None,
            xyRatio=1.8, blurFactor=0.6, rankthreshold=3, 
            binThreshold=5, datespan=None, binType="shape",
            binModel=None, hitsThreshold=50):

    """ Retrive data from the document database

    Parameters
    ----------
    words : list
        list of n-grams that should be queried
    xBins : int
        how many bins there should be on the x-axis
    scatter : int
        1 if scatterplot should be forced
    zoom : int
        1 if the user wants the map to be zoomed in 
        around the avalible data. if 0 it defaults
        to around sweden.
    xyRatio : int
        correction to make the bins square in
        mercurator projection map
    blurFactor : float
        if blurring the 2d bin data should be applied
        do it by this amount
    rankthreshold : int
        which rank to be the highest included
    datespan : str
        span of what dates to be used in the query. eg. 2011-01-01:2011-12-31
    binThreshold : int
        number of hits required in a bin for it to count
    binType : int
        number of hits required in a bin for it to count

    Returns
    -------
    filename : str
        filename of main image
    hits : dict
        dict of the querywords number of hits in 
        the document database
    KWIC : dict
        dict with the querywords kwics
    fewResults : bool
        if a word has to few hits in document database
    gifFileName : str
        filename of the gif
    """
    
    coordinatesByWord, ranksByWord = (), ()
    minCoordinates = 99999999999999 # Shame!
    hits = {}
    KWIC = {}
    resultsOmitted = False
    wordsOverThreshold = []
    
    for word in words:
        coordinates, dates, ranks = [], [], []
        fewResults = False
        if datespan:
            print "datespan", datespan
            try:
                dateFrom = datespan.split("->")[0].encode('utf-8')
                dateTo = datespan.split("->")[1].encode('utf-8')
                print dateFrom, dateTo  
                spanQuery = "AND posts.date BETWEEN CAST('"+dateFrom+"' AS DATE) "
                spanQuery += "AND CAST('"+dateTo+"' AS DATE) "   
            except:
                spanQuery = ""
        else:
            spanQuery = ""
            
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
                               "AGAINST ('" + word.encode('utf-8') + "' "
                               "IN BOOLEAN MODE) "
                               "AND blogs.latitude is not NULL "
                               "AND blogs.longitude is not NULL "
                               "AND blogs.rank <= " + str(rankthreshold) + " "
                               " " + spanQuery + " "
                               "ORDER BY posts.date ")
                               #ORDER BY RAND() limit 1000? 
        print word.encode('utf-8')
        
        # Get all lon and lats, and dates
        # and keywords in contexts (kwic)
        wordkwic = []
        i = 0
        oldkwic = ""
        for row in result:
            coordinates.append([row['longitude'], 
                                row['latitude']])
            dates.append(row['date'])
            ranks.append(row['rank'])
            
            newkwic = kwic(row['text'], word, row['source'])
            if oldkwic != newkwic and i < 50:
                i += 1
                wordkwic.append(newkwic)
                oldkwic = newkwic
        
        if len(coordinates) > hitsThreshold: # only draw coordinates over limit
        
            wordsOverThreshold.append(word)
            
            KWIC[word.replace('"',"")] = wordkwic
            
            coordinatesByWord = coordinatesByWord + (coordinates,)
            ranksByWord = ranksByWord + (ranks,)
            
            if len(coordinates) < minCoordinates: # log the one with fewest coordinates
                minCoordinates = len(coordinates)
                
        else:
            resultsOmitted = True # So we can show the user that a word has been removed
            
        hits[word] = len(coordinates)
    
    words = wordsOverThreshold # So words under threshold is omitted     

    if not xBins: # xBins not set: "guestimate" that 2 hits per bin is good
        xBins = math.sqrt(float(minCoordinates)/(float(xyRatio)*float(2)))
        xBins = int(xBins)            

    if not any([(val > hitsThreshold) for val in hits.itervalues()]):
        # I.e. no word had enough hits
        fewResults, filename, gifFileName = True, None, None
        
    elif binType == "shape":
        # Get main image with shapefiles
        fewResults, filename, gifFileName = genShapefileImg(coordinatesByWord, ranks,
                                                            words, zoom,
                                                            binThreshold=binThreshold,
                                                            binModel=binModel)
    elif binType == "square":
        # Get main image
        fewResults, filename, gifFileName = genGridImg(coordinatesByWord=coordinatesByWord,
                                                       xBins=xBins,
                                                       words=words,
                                                       zoom=zoom,
                                                       xyRatio=xyRatio, 
                                                       blurFactor=blurFactor, 
                                                       minCoordinates=minCoordinates,
                                                       scatter=scatter,
                                                       hits=hits,
                                                       chunks=1)
        # Get time series gif
        """
        fewResults, giffile, gifFileName = genGridImg(coordinatesByWord=coordinatesByWord,
                                                      xBins=xBins,
                                                      words=words,
                                                      zoom=zoom,
                                                      xyRatio=xyRatio, 
                                                      blurFactor=blurFactor, 
                                                      minCoordinates=minCoordinates,
                                                      scatter=scatter,
                                                      hits=hits,
                                                      chunks=7,
                                                      dates=dates,
                                                      binThreshold=binThreshold)
        
        if gifFileName: # no gif = no histogram                                     
            dateHistogram(dates, gifFileName)
        """
        
    return filename, hits, KWIC, fewResults, gifFileName, resultsOmitted
        
    #else: # if a term has to few hits
    #    return None, hits, KWIC, fewResults, None
    

@app.route('/sinus', methods = ['GET', 'POST'])
@app.route('/sinus/', methods = ['GET', 'POST'])
@app.route('/sinus/search/<urlSearch>', methods = ['GET'])
def site(urlSearch=None):
    """ Run if index/search view if choosen

    Parameters
    ----------
    urlSearch : str
        if a document database search is queryed
        by querystring instead of POST

    Returns
    -------
    index.html : html
        the index view rendered with render_template("index.html")

    """  
    #stats = getStats()
    stats = None
    
    ### Classify text
    try:
        textInput = request.form['textInput']
    except:
        textInput = ""
    
    if request.method == 'POST' and len(textInput) > 0:
        touple = model.predict(request.form['textInput'])
        coordinate, placeness, mostUsefulWords, OOV, mentions = touple
        
        if not placeness == 0.0:
            placeness = int(math.log(placeness))
        else:
            placeness = 0.0
        lon = coordinate[0]
        lat = coordinate[1]
        localizeText = { 'text': request.form['textInput'],
                         'lon': lon, 'lat': lat,
                         'placeness': placeness,
                         'mostUsefulWords': mostUsefulWords } 
    else:
        localizeText = None
        
    ### Search in document database
    if request.method == 'POST' and len(textInput) == 0:
        query = request.form['queryInput']
        queryWords = query.split(",")
    elif urlSearch:
        queryWords = urlSearch.split(",")
        query = None
    else:
        queryWords = []
        query = None

    operators, queryWords, xbins, scatter, zoom, rankthreshold, datespan, binThreshold, binType, binModel, hitsThreshold = getOperators(queryWords)
            
    if len(queryWords) > 0:
        touple = getData(queryWords,        
                         xBins=xbins,
                         scatter=scatter,
                         zoom=zoom,
                         rankthreshold=rankthreshold,
                         binThreshold=binThreshold,
                         datespan=datespan,
                         binType=binType,
                         binModel=binModel,
                         hitsThreshold=hitsThreshold)
                         
        filename, hits, KWICs, fewResults, gifFileName, resultsOmitted = touple
                              
        documentQuery = { 'query': query,
                          'filename': filename,
                          'hits': hits,
                          'KWICs': KWICs,
                          'fewResults': fewResults,
                          'gifFileName': gifFileName,
                          'resultsOmitted': resultsOmitted }
    else:
        documentQuery = None
        
    return render_template("index.html", localizeText=localizeText,
                                         documentQuery=documentQuery,
                                         stats=stats)


@app.route('/sinus/explore', methods = ['GET', 'POST'])
@app.route('/sinus/explore/<word>', methods = ['GET'])
def explore(word=None):
    """Run if explore in the menu is choosen

    Parameters
    ----------
    word : str
        the word to explore
        
    Returns
    -------
    explore.html : html
        the explore view rendered with render_template("explore.html")

    """    
    result = mysqldb.query("select * from ngrams "
                           "where entropy < 3 "
                           "and entropy > 0 "
                           "order by entropy ")
    totEntWords, totEnt = [], []

    for row in result:
        if row['token'].decode('utf-8') not in s:
            totEntWords.append(row['token'].decode('utf-8'))
            totEnt.append(row['entropy'])

    totEntWords = zip(totEntWords, totEnt)
        
    if word:
        synonyms = getSynonyms(word)
        synonyms.insert(0, word)
        synonyms = ", ".join(synonyms)
    else:
        synonyms = None


    ### Calculate alot of different delta entropys

    # Get delta entropy 10 % (difference between first and last 10%)
    result = mysqldb.query("select * from ngrams "
                           "where deltaEnt10 is not NULL "
                           "and deltaEnt10 > 1 "
                           "order by deltaEnt10 desc")
    deltaEnt10Words, ent10 = [], []

    for row in result:
        if row['token'].decode('utf-8') not in s:
            deltaEnt10Words.append(row['token'].decode('utf-8'))
            ent10.append(row['deltaEnt10'])

    deltaEnt10Words = zip(deltaEnt10Words, ent10)

    # Get delta entropy 20 %
    result = mysqldb.query("select * from ngrams "
                           "where deltaEnt20 is not NULL "
                           "and deltaEnt20 > 1 "
                           "order by deltaEnt20 desc")
    deltaEnt20Words, ent20 = [], []

    for row in result:
        if row['token'].decode('utf-8') not in s:
            deltaEnt20Words.append(row['token'].decode('utf-8'))
            ent20.append(row['deltaEnt20'])

    deltaEnt20Words = zip(deltaEnt20Words, ent20)

    # Get delta entropy 30 %
    result = mysqldb.query("select * from ngrams "
                           "where deltaEnt30 is not NULL "
                           "and deltaEnt30 > 1 "
                           "order by deltaEnt30 desc")
    deltaEnt30Words, ent30 = [], []

    for row in result:
        if row['token'].decode('utf-8') not in s:
            deltaEnt30Words.append(row['token'].decode('utf-8'))
            ent30.append(row['deltaEnt30'])

    deltaEnt30Words = zip(deltaEnt30Words, ent30)

    # Get delta entropy 40 %
    result = mysqldb.query("select * from ngrams "
                           "where deltaEnt40 is not NULL "
                           "and deltaEnt40 > 1 "
                           "order by deltaEnt40 desc")
    deltaEnt40Words, ent40 = [], []

    for row in result:
        if row['token'].decode('utf-8') not in s:
            deltaEnt40Words.append(row['token'].decode('utf-8'))
            ent40.append(row['deltaEnt40'])

    deltaEnt40Words = zip(deltaEnt40Words, ent40)

    # Get delta entropy 50 %
    result = mysqldb.query("select * from ngrams "
                           "where deltaEnt50 is not NULL "
                           "and deltaEnt50 > 1 "
                           "order by deltaEnt50 desc")
    deltaEnt50Words, ent50 = [], []

    for row in result:
        if row['token'].decode('utf-8') not in s:
            deltaEnt50Words.append(row['token'].decode('utf-8'))
            ent50.append(row['deltaEnt50'])     

    deltaEnt50Words = zip(deltaEnt50Words, ent50)


    
    data = { 'totEntWords': totEntWords,
             'deltaEnt10Words': deltaEnt10Words, 
             'deltaEnt20Words': deltaEnt20Words, 
             'deltaEnt30Words': deltaEnt30Words, 
             'deltaEnt40Words': deltaEnt40Words, 
             'deltaEnt50Words': deltaEnt50Words, 
             'synonyms': synonyms }    
             
    return render_template("explore.html", data=data)


def dataframe2tuple(df):
    coordinatesByWord = ()
    words = []
    
    for word, data in df.groupby(['form']):
        words.append(word)
        coordinates = zip(data['lon'], data['lat'])
        coordinates = [list(c) for c in coordinates]
        coordinatesByWord = coordinatesByWord + (coordinates,)
    
    return coordinatesByWord, words

def getCoordinate(place):
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

@app.route('/sinus/byod', methods = ['GET', 'POST'])
def byod():
    """Run if BYOD in the menu is choosen

    Parameters
    ----------
        
    Returns
    -------
    byod.html : html
        the explore view rendered with render_template("byod.html")

    """      
    UPLOAD_FOLDER = 'sinusGUIapp/static/maps'
    ALLOWED_EXTENSIONS = set(['xlsx'])
    
    def allowed_file(filename):
        return '.' in filename and \
               filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS
    
    app = Flask(__name__)
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    
    excelfile = None
    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            excelfile = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    if excelfile:
        df = pd.io.excel.read_excel(excelfile)

        lats, lons, queryLimit = [], [], False
        
        for place in zip(df['ort'], df['kommun'], df[u'län'], df['landskap']):
            try:
                lat, lon = getCoordinate(place) # from Google's API
            except geocode.QueryLimitError:
                lat, lon = None, None
                queryLimit = True
                
            lats.append(lat)
            lons.append(lon) 
                   
        df['lat'] = lats
        df['lon'] = lons
        
        if queryLimit: # if fail, set to percent sucess
            queryLimit = 100.0 * float(len(df[df['lat'] > 0])) / float(len(df['lat']))

        # Parse operators
        query = request.form['queryInput']
        queryWords = query.split(",")
        
        operators, queryWords, xbins, scatter, zoom, rankthreshold, datespan, binThreshold, binType, binModel, hitsThreshold = getOperators(queryWords)
              
        # If no column "form" is found, assume only one word
        if not 'form' in df.columns:
            # Use filename
            df['form'] = filename.split("_-_")[-1].replace(".xlsx", "").lower()

        # Note if words are omitted
        if sum(df.groupby('form').form.transform(len) > hitsThreshold) < len(df):
            resultsOmitted = True
        else:
            resultsOmitted = False
          
        # Save hits of different terms
        hits = df.form.value_counts().to_dict()
            
        # Remove words under threshold
        df = df[df.groupby('form').form.transform(len) > hitsThreshold]
        words = df['form'].unique()
                        
        # Convert DF into tuple format that genShapefileImg accepts
        coordinatesByWord, words = dataframe2tuple(df)
        
        # Generate statistics
        stats = getStats()
        
        if binType == "shape":
            # Get main image with shapefiles
            fewResults, filename, gifFileName = genShapefileImg(coordinatesByWord, None, # ranks=None
                                                                words, zoom,
                                                                binThreshold=binThreshold,
                                                                binModel=binModel)  
        if binType == "square":
            # Get main image
            fewResults, filename, gifFileName = genGridImg(coordinatesByWord=coordinatesByWord,
                                                           xBins=xbins,
                                                           words=words,
                                                           zoom=zoom,
                                                           xyRatio=1.8, 
                                                           blurFactor=0,
                                                           minCoordinates=999999999,
                                                           scatter=0,
                                                           hits=hits,
                                                           chunks=1)

        documentQuery = { 'query': query,
                          'filename': filename,
                          'hits': None,
                          'KWICs': None,
                          'fewResults': fewResults,
                          'gifFileName': None ,
                          'queryLimit': queryLimit,
                          'resultsOmitted': resultsOmitted }
                                      
        return render_template("index.html", localizeText=None,
                                             documentQuery=documentQuery,
                                             stats=stats)
    else: # no file submitted yet / error
        return render_template("byod.html", data=None)

    
@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify( { 'error': 'Not found' } ), 404)


# Set up the geotagging model
model = tweetLoc(c.LOCATIONDB)
# Connect to DB
mysqldb = dataset.connect(c.LOCATIONDB) 
mysqldb.query("set names 'utf8'") # For safety

# Create set with all Swedish towns to be used to exclude from 
# the results when hunting for words with low entropy in the data.
# Towns/cities are by nature with low entropy but of no intrest. 
s = Set()
f = codecs.open("orter.txt", encoding="utf-8")
for line in f:
    s.add(line.lower().strip())
    
cache = SqliteCache("cache")