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
import time
import codecs
from sets import Set
import requests
from images2gif import writeGif
from PIL import Image
import os
import config as c
from sqlite_cache import SqliteCache
from sqlalchemy import create_engine
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
import cPickle as pickle

def timing(f):
    def wrap(*args):
        time1 = time.time()
        ret = f(*args)
        time2 = time.time()
        if 60 > time2-time1 > 0:
            print '%s function took %0.3f s' % (f.func_name, (time2-time1))
        elif time2-time1 > 60:
            print '%s function took %0.3f min' % (f.func_name, (time2-time1)/60.0)
        elif time2-time1 < 0:
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
    
    if "-" in word or "+" in word or "(" in word:
        words = word.replace("+","").replace("-","").replace("(","").replace(")","").replace("OR","").split()
    elif " or " in word.lower():
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
            
    return kwics

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
            
        lon_bins = np.linspace(9.5, 28.5, xBins)
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
        """ Sum all elements in matrix """
        
        try:
            return sum(map(sum, input))
        except Exception:
            return sum(input)
    
    def normalize(matrix):
        """ Divide all elements by sum of all elements """
        return matrix / sum1(matrix)        
    
    @timing    
    def getEnoughData():
        """ Get alot of data until a suitable null hypothesis has converged """
        
        try:        
            coordinates = []

            for source in mysqldb.query("SELECT longitude, latitude from blogs "
                                        "WHERE longitude is not NULL and "
                                        "latitude is not NULL "
                                        "ORDER BY RAND() "
                                        "LIMIT 500000"):   
    
                coordinates.append([source['longitude'], source['latitude']])
                
            return coordinates
   
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
        llcrnrlon = 9.5
        llcrnrlat = 54.5
        urcrnrlon = 28.5
        urcrnrlat = 69.5
        resolution = 'i'
        area_thresh = 250

    cachedMapWithShapes = "mapwithshapefiles.pkl"

    if not os.path.isfile(cachedMapWithShapes) or zoom:
        # If no cache is awalible, set up object
        start_time = time.time()

        m = Basemap(projection='merc',
                    resolution=resolution, 
                    area_thresh=area_thresh,
                    llcrnrlon=llcrnrlon, 
                    llcrnrlat=llcrnrlat,
                    urcrnrlon=urcrnrlon, 
                    urcrnrlat=urcrnrlat) 

        ### Read shapefiles
 
        # Finnish regions (sv: landskap)
        _out = m.readshapefile('shapedata/finland/fin-adm2', 
                               name='regions_fi', drawbounds=False, 
                               color='none', zorder=2)
        
        # Åland
        _out = m.readshapefile('shapedata/finland/ala-adm0', 
                               name='region_al', drawbounds=False, 
                               color='none', zorder=2)
        
        # Municipality data (SV)
        _out = m.readshapefile('shapedata/Kommuner_SCB/Kommuner_SCB_Std', 
                               name='muni', drawbounds=False, 
                               color='none', zorder=3)

        # Make cached map
        if not zoom:
            with open(cachedMapWithShapes,'wb') as f:
                pickle.dump(m, f)
                               
        print("--- %s sekunder att läsa alla shapefiles ---" % (time.time() - start_time))
    else:
        # Read from cache to save precious time
        start_time = time.time()
        with open(cachedMapWithShapes, 'rb') as f:
            m = pickle.load(f)
        print("--- %s sekunder att läsa alla shapefiles från cache ---" % (time.time() - start_time))

    start_time = time.time()
            
    # Municipality DF (SE + FI)
    # (FID is for removing Finnish Lapland and North Osterbothnia)   
    df_map_muni = pd.DataFrame({
        'poly': [Polygon(p) for p in m.muni] + \
                [Polygon(p) for p, r in zip(m.regions_fi, m.regions_fi_info) \
                            if r['FID'] not in [1, 3]] + \
                [Polygon(p) for p in m.region_al], 
        'name': [r['KNNAMN'] for r in m.muni_info] + \
                ["n/a" for r in m.regions_fi_info \
                       if r['FID'] not in [1, 3]] + \
                ["åland" for r in m.region_al_info] })    
    
    # Fix encoding
    df_map_muni['name'] = df_map_muni.apply(lambda row: row['name'].decode('latin-1'), axis=1)
    
    #print("--- %s sekunder att sätta upp dataframes med polygoner ---" % (time.time() - start_time))

    def mapPointsToPoly(coordinates_df, poly_df):
        """ Take coordiates DF and put into polygon DF """
        
        mapped_points, hood_polygons = {}, {}
        ranks = {}
        
        uniqeWords = coordinates_df['word'].unique()
        
        for word, ld in coordinates_df.groupby(['word']):             
            # Convert our latitude and longitude into Basemap cartesian map coordinates
            start_time = time.time()
            points = [Point(m(mapped_x, mapped_y)) 
                      for mapped_x, mapped_y 
                      in zip(ld['longitude'], ld['latitude'])]
            
            #print("--- %s sekunder att konvertera till Point() ---" % (time.time() - start_time))
            # If we did not get ranked data, assume rank 2          
            try:
                mapped_points[word] = pd.DataFrame({'points': points,
                                                    'rank': ld['rank']})
            except KeyError:
                mapped_points[word] = pd.DataFrame({'points': points})
                mapped_points[word]['rank'] = 2


        def num_of_contained_points(apolygon, mapped_points):
            """ Counts number of points that fall into a polygon
                Points with rank >= 4 gets just half weight """

            num = 0            
            for rank, ld in mapped_points.groupby(['rank']):  
                if rank >= 4: # Downweight badly ranked points
                    num += int(0.5*len(filter(prep(apolygon).contains, ld['points'])))
                else:
                    num += int(len(filter(prep(apolygon).contains, ld['points'])))
                    
            return num
        

        for word in uniqeWords:
            start_time = time.time()   
            poly_df[word] = poly_df['poly'].apply(num_of_contained_points, 
                                                  args=(mapped_points[word],))
            poly_df[word][poly_df[word] < binThreshold] = 0
            print("--- %s sekunder att kolla hur många träffar som är i varje polygon) ---" % (time.time() - start_time))
            
        return poly_df
        
    df_map_muni = mapPointsToPoly(lds, df_map_muni)

    print words
        
    ### Only one word: compare to country average
    if len(words) == 1: 
        
        fname_muni = "null_hypothesis_muni_df.pkl" 
        
        start_time = time.time()   
        if not os.path.isfile(fname_muni):
            temp_latlon_df = pd.DataFrame(getEnoughData(), 
                                          columns=['longitude', 'latitude'])
            temp_latlon_df['word'] = "expected"
            
            # Make dataframe and pickle 
            null_h_muni_df = mapPointsToPoly(temp_latlon_df, df_map_muni)
            null_h_muni_df.to_pickle(fname_muni)
        else:
            # Read from pickle
            null_h_muni_df = pd.io.pickle.read_pickle(fname_muni)
        
        print("--- %s sekunder att ladda nollhypotes) ---" % (time.time() - start_time))


        def deviationFromAverage(df_map, avg):
            """ Make DFs into percentages and see the deviation from country average """

            df_map['expected'] = avg['expected']        
            df_map = df_map[df_map['expected'] > 0] # remove zeros

            # Calculate percentages
            df_map['expected'] = df_map['expected'].astype('float')\
                                                   .div(df_map['expected'].sum(axis=0))

            # Keep the frequencys
            df_map[words[0] + "_frq"] = df_map[words[0]] 

            # Words will here just be the one word
            df_map[words] = df_map[words].astype('float')\
                                         .div(df_map[words].sum(axis=0))

            # Divide distribution percentage by expected percentage   
            df_map[words] = df_map[words].div(df_map['expected'], axis='index')
            del df_map['expected']

            return df_map
         
        start_time = time.time()   
        # Since only one word, calculate deviation from country average   
        df_map_muni = deviationFromAverage(df_map_muni, null_h_muni_df)
        print("--- %s sekunder att kolla avvikelse fr nollhypotes) ---" % (time.time() - start_time))
        
        breaks['muni'] = {}
               
        for word in words:    
            muniMax = float(df_map_muni[word].max(axis=0))
            breaks['muni'][word] = [0., 0.5, 1., muniMax/2.0, muniMax]
        
        labels = ['Below avg.', '', 'Avg.', '', 'Above avg.']    
        
    else:     
        ### More than one word: compare words against each other 
           
        # Get total occurencies in every municipality
        df_map_muni["sum"] = df_map_muni[words].sum(axis=1)
            
        def df_percent(df_map):
            # Save for later use
            for word in words:
                df_map[word + "_frq"] = df_map[word]

            # Handle divide by zero as zeros
            df_map[words] = df_map[words].astype('float').div(df_map["sum"].replace({ 0 : np.nan })
                                                              .astype('float'), axis='index')
            df_map[words] = df_map[words].fillna(0)
            df_map.loc[df_map['sum'] < binThreshold, words] = 0
                        
            return df_map
        
        # Convert to percentages and skip where there is none
        start_time = time.time()   
        df_map_muni = df_percent(df_map_muni)
        #print("--- %s sekunder att konvertera till procent) ---" % (time.time() - start_time))

        breaks['muni'] = {}
               
        for word in words:    
            breaks['muni'][word] = [0., 0.25, 0.5, 0.75, 1.0]
            
        labels = ['None', 'Low', 'Medium', 'High', 'Very high']
        
    def self_categorize(entry, breaks):
        """ Put percent into a category (breaks) """
        
        for i in range(len(breaks)-1):
            if entry > breaks[i] and entry <= breaks[i+1]:
                return i
        return -1 # under or over break interval
    
    def genFallbackMap(df, word, smooth=False):
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

                if smooth:
                    municipalitys = df['name'].unique() # All
                else:
                    municipalitys = df[df[word] == 0.0]['name'].unique() # Just where zero hits

                for muni in municipalitys: 
                    # Merge the mean of every parent level
                    mean = np.array([getParentMean(df, muni, parentLevel, word) 
                                     for parentLevel in parentLevels])
                    mean = np.mean(mean[mean != np.array(None)]) # Remove Nones and then mean
    
                    # Update municipality with fallback according to rule
                    if mean and mean != 0.0 and mean != True:
                        #if smooth:
                            #new_df.loc[new_df['name'] == muni, word] = (3*mean+df.loc[df['name'] == muni, word])/4.0
                        #else:
                        new_df.loc[new_df['name'] == muni, word] = mean
                        
            return new_df 

        df = updateDF(df, word)

        return df
    
    fig = plt.figure(figsize=(3.45*len(words),6))
    
    for i, word in enumerate(words):

        start_time = time.time()  
        # Create columns stating which break precentages belongs to
        df_map_muni['bins_'+word] = df_map_muni[word].apply(self_categorize, 
                                                             args=(breaks['muni'][word],))      

        # Also create a fallback DF if needed
        if binModel == 'MP' or binModel == 'MP+smooth':
            start_time = time.time() 
            df_map_fallback = genFallbackMap(df_map_muni, word)   
            if binModel == 'MP+smooth':
                df_map_fallback = genFallbackMap(df_map_fallback, word, smooth=True)   
                
            print("--- %s sekunder att skapa mp-stepback) ---" % (time.time() - start_time))        
            df_map_fallback['bins_'+word] = df_map_fallback[word].apply(self_categorize, 
                                                                        args=(breaks['muni'][word],)) 

        start_time = time.time()                                                                                                       
        # Subplot for every word
        if len(word) > 25:
            title = word.replace(" OR ", "/")[0:25] + " [...]"
        else:
            title = word.replace(" OR ", "/")
            
        ax = fig.add_subplot(1, len(words), int(i+1), axisbg='w', frame_on=False)
        ax.set_title(u"{word} - hits: {hits}".format(word=title, 
                                                     hits=coord_count[word]), 
                     y=1.01, fontsize=9)
    
        colormap = colorCycle(i)
        if len(words) == 1:
            colormap = "coolwarm" 
            
        cmap = plt.get_cmap(colormap)
        #cmap = opacify(cmap) # Add opacity to colormap
        
        if binModel == 'MP' or binModel == 'MP+smooth':
            # Lab
            shapesToPutOnMap = [df_map_fallback]
        else: 
            shapesToPutOnMap = [df_map_muni]
        
        # Put all shapes on map
        for df_map in shapesToPutOnMap:
            
            # Create patches
            df_map['patches'] = df_map.apply(lambda row: PolygonPatch(row['poly'], lw=0, zorder=4), axis=1)

            pc = PatchCollection(df_map['patches'], match_original=True)

            # Apply our custom color values onto the patch collection
            #cmaps = (df_map['bins_'+word].values - 
            #           df_map['bins_'+word].values.min())/(
            #               df_map['bins_'+word].values.max()-
            #                   float(df_map['bins_'+word].values.min()))
            cmaps = (df_map['bins_'+word].values - -1)/(
                           len(breaks['muni'][word])-2-
                               float(-1)) # Let's fix the scaling for now
            cmap_list = []

            def cmapOpacity(val, opacity):
                """ Fix for setting opacity """
                r, g, b, a = cmap(val)
                a = opacity
                return r, g, b, a

            for val, frq in zip(cmaps, df_map[word + "_frq"]):
                if val == 0:
                    cmap_list.append('none')
                else:
                    if frq > 10:
                        opacity = 1
                    else:
                        opacity = 0.5

                    opacity = 1 # Let's wait with using opacity for significance
                    cmap_list.append(cmapOpacity(val, opacity))
            
            pc.set_facecolor(cmap_list)
            ax.add_collection(pc)
            
        m.drawcoastlines(linewidth=0.25, color="#3b3b3b") 
        m.drawcountries()
        m.drawstates()
        m.drawmapboundary()
        m.fillcontinents(color='white', lake_color='grey', zorder=0)
        m.drawmapboundary(fill_color='grey')
    
        divider = make_axes_locatable(plt.gca())
        cax = divider.append_axes("bottom", 
                                  "2%", 
                                  pad="2.5%")
                        
        cbar = custom_colorbar(cmap, ncolors=len(labels)+1, 
                               labels=labels, 
                               orientation='horizontal', 
                               cax=cax)
        cbar.ax.tick_params(labelsize=6)
        
        #print("--- %s sekunder att skapa karta) ---" % (time.time() - start_time))      
            
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







def genOneMapShapefileImg(data, ranks, words, zoom, binThreshold, binModel):
    """ Generate an image with shapefiles as bins but not multiple maps

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
            
        lon_bins = np.linspace(9.5, 28.5, xBins)
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
        """ Sum all elements in matrix """
        
        try:
            return sum(map(sum, input))
        except Exception:
            return sum(input)
    
    def normalize(matrix):
        """ Divide all elements by sum of all elements """
        return matrix / sum1(matrix)        
    
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
        llcrnrlon = 9.5
        llcrnrlat = 54.5
        urcrnrlon = 28.5
        urcrnrlat = 69.5
        resolution = 'i'
        area_thresh = 250

    cachedMapWithShapes = "mapwithshapefiles.pkl"

    if not os.path.isfile(cachedMapWithShapes) or zoom:
        # If no cache is awalible, set up object
        start_time = time.time()

        m = Basemap(projection='merc',
                    resolution=resolution, 
                    area_thresh=area_thresh,
                    llcrnrlon=llcrnrlon, 
                    llcrnrlat=llcrnrlat,
                    urcrnrlon=urcrnrlon, 
                    urcrnrlat=urcrnrlat) 

        ### Read shapefiles
 
        # Finnish regions (sv: landskap)
        _out = m.readshapefile('shapedata/finland/fin-adm2', 
                               name='regions_fi', drawbounds=False, 
                               color='none', zorder=2)
        
        # Åland
        _out = m.readshapefile('shapedata/finland/ala-adm0', 
                               name='region_al', drawbounds=False, 
                               color='none', zorder=2)
        
        # Municipality data (SV)
        _out = m.readshapefile('shapedata/Kommuner_SCB/Kommuner_SCB_Std', 
                               name='muni', drawbounds=False, 
                               color='none', zorder=3)

        # Make cached map
        if not zoom:
            with open(cachedMapWithShapes,'wb') as f:
                pickle.dump(m, f)
                               
        print("--- %s sekunder att läsa alla shapefiles ---" % (time.time() - start_time))
    else:
        # Read from cache to save precious time
        start_time = time.time()
        with open(cachedMapWithShapes, 'rb') as f:
            m = pickle.load(f)
        print("--- %s sekunder att läsa alla shapefiles från cache ---" % (time.time() - start_time))

    start_time = time.time()
            
    # Municipality DF (SE + FI)
    # (FID is for removing Finnish Lapland and North Osterbothnia)   
    df_map_muni = pd.DataFrame({
        'poly': [Polygon(p) for p in m.muni] + \
                [Polygon(p) for p, r in zip(m.regions_fi, m.regions_fi_info) \
                            if r['FID'] not in [1, 3]] + \
                [Polygon(p) for p in m.region_al], 
        'name': [r['KNNAMN'] for r in m.muni_info] + \
                ["n/a" for r in m.regions_fi_info \
                       if r['FID'] not in [1, 3]] + \
                ["åland" for r in m.region_al_info] })    
    
    # Fix encoding
    df_map_muni['name'] = df_map_muni.apply(lambda row: row['name'].decode('latin-1'), axis=1)
    
    #print("--- %s sekunder att sätta upp dataframes med polygoner ---" % (time.time() - start_time))

    def mapPointsToPoly(coordinates_df, poly_df):
        """ Take coordiates DF and put into polygon DF """
        
        mapped_points, hood_polygons = {}, {}
        ranks = {}
        
        uniqeWords = coordinates_df['word'].unique()
        
        for word, ld in coordinates_df.groupby(['word']):             
            # Convert our latitude and longitude into Basemap cartesian map coordinates
            start_time = time.time()
            points = [Point(m(mapped_x, mapped_y)) 
                      for mapped_x, mapped_y 
                      in zip(ld['longitude'], ld['latitude'])]
            
            #print("--- %s sekunder att konvertera till Point() ---" % (time.time() - start_time))
            # If we did not get ranked data, assume rank 2          
            try:
                mapped_points[word] = pd.DataFrame({'points': points,
                                                    'rank': ld['rank']})
            except KeyError:
                mapped_points[word] = pd.DataFrame({'points': points})
                mapped_points[word]['rank'] = 2


        def num_of_contained_points(apolygon, mapped_points):
            """ Counts number of points that fall into a polygon
                Points with rank >= 4 gets just half weight """

            num = 0            
            for rank, ld in mapped_points.groupby(['rank']):  
                if rank >= 4: # Downweight badly ranked points
                    num += int(0.5*len(filter(prep(apolygon).contains, ld['points'])))
                else:
                    num += int(len(filter(prep(apolygon).contains, ld['points'])))
                    
            return num
        

        for word in uniqeWords:
            start_time = time.time()   
            poly_df[word] = poly_df['poly'].apply(num_of_contained_points, 
                                                  args=(mapped_points[word],))
            poly_df[word][poly_df[word] < binThreshold] = 0
            print("--- %s sekunder att kolla hur många träffar som är i varje polygon) ---" % (time.time() - start_time))
            
        return poly_df
        
    df_map_muni = mapPointsToPoly(lds, df_map_muni)

    print words
    
    ### More than one word: compare words against each other 
       
    # Get total occurencies in every municipality
    df_map_muni["sum"] = df_map_muni[words].sum(axis=1)
        
    def df_percent(df_map):
        # Save for later use
        for word in words:
            df_map[word + "_frq"] = df_map[word]

        # Handle divide by zero as zeros
        df_map[words] = df_map[words].astype('float').div(df_map["sum"].replace({ 0 : np.nan })
                                                          .astype('float'), axis='index')
        df_map[words] = df_map[words].fillna(0)
        df_map.loc[df_map['sum'] < binThreshold, words] = 0
                    
        return df_map
    
    # Convert to percentages and skip where there is none
    start_time = time.time()   
    df_map_muni = df_percent(df_map_muni)

    breaks['muni'] = {}
           
    for word in words:    
        breaks['muni'][word] = [0., 0.25, 0.5, 0.75, 1.0]
        
    labels = ['None', 'Low', 'Medium', 'High', 'Very high']
        
    def self_categorize(entry, breaks):
        """ Put percent into a category (breaks) """
        
        for i in range(len(breaks)-1):
            if entry > breaks[i] and entry <= breaks[i+1]:
                return i
        return -1 # under or over break interval
    
    def genFallbackMap(df, word, smooth=False):
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

                if smooth:
                    municipalitys = df['name'].unique() # All
                else:
                    municipalitys = df[df[word] == 0.0]['name'].unique() # Just where zero hits

                for muni in municipalitys: 
                    # Merge the mean of every parent level
                    mean = np.array([getParentMean(df, muni, parentLevel, word) 
                                     for parentLevel in parentLevels])
                    mean = np.mean(mean[mean != np.array(None)]) # Remove Nones and then mean
    
                    # Update municipality with fallback according to rule
                    if mean and mean != 0.0 and mean != True:
                        #if smooth:
                            #new_df.loc[new_df['name'] == muni, word] = (3*mean+df.loc[df['name'] == muni, word])/4.0
                        #else:
                        new_df.loc[new_df['name'] == muni, word] = mean
                        
            return new_df 

        df = updateDF(df, word)

        return df
    
    fig = plt.figure(figsize=(3.45*len(words),6))
    
    for i, word in enumerate(words):

        start_time = time.time()  
        # Create columns stating which break precentages belongs to
        df_map_muni['bins_'+word] = df_map_muni[word].apply(self_categorize, 
                                                             args=(breaks['muni'][word],))      

        # Also create a fallback DF if needed
        if binModel == 'MP' or binModel == 'MP+smooth':
            start_time = time.time() 
            df_map_fallback = genFallbackMap(df_map_muni, word)   
            if binModel == 'MP+smooth':
                df_map_fallback = genFallbackMap(df_map_fallback, word, smooth=True)   
                
            print("--- %s sekunder att skapa mp-stepback) ---" % (time.time() - start_time))        
            df_map_fallback['bins_'+word] = df_map_fallback[word].apply(self_categorize, 
                                                                        args=(breaks['muni'][word],)) 

        start_time = time.time()                                                                                                       
        # Subplot for every word
        if len(word) > 25:
            title = word.replace(" OR ", "/")[0:25] + " [...]"
        else:
            title = word.replace(" OR ", "/")
            
        ax = fig.add_subplot(1, len(words), 1,#int(i+1), 
                             axisbg='w', frame_on=False)
        ax.set_title(u"{word} - hits: {hits}".format(word=title, 
                                                     hits=coord_count[word]), 
                     y=1.01, fontsize=9)
    
        colormap = colorCycle(i)
            
        cmap = plt.get_cmap(colormap)
        #cmap = opacify(cmap) # Add opacity to colormap
        
        if binModel == 'MP' or binModel == 'MP+smooth':
            # Lab
            shapesToPutOnMap = [df_map_fallback]
        else: 
            shapesToPutOnMap = [df_map_muni]
        
        # Put all shapes on map
        for df_map in shapesToPutOnMap:
            
            # Create patches
            df_map['patches'] = df_map.apply(lambda row: PolygonPatch(row['poly'], lw=0, zorder=4), axis=1)

            pc = PatchCollection(df_map['patches'], match_original=True)

            # Apply our custom color values onto the patch collection
            cmaps = (df_map['bins_'+word].values - -1)/(
                           len(breaks['muni'][word])-2-
                               float(-1)) # Let's fix the scaling for now
            cmap_list = []

            def cmapOpacity(val, opacity):
                """ Fix for setting opacity """
                r, g, b, a = cmap(val)
                a = opacity
                return r, g, b, a

            for val, frq in zip(cmaps, df_map[word + "_frq"]):
                if val == 0:
                    cmap_list.append('none')
                else:
                    if frq > 10:
                        opacity = 1
                    else:
                        opacity = 0.5

                    opacity = 1 # Let's wait with using opacity for significance
                    cmap_list.append(cmapOpacity(val, opacity))
            
            pc.set_facecolor(cmap_list)
            ax.add_collection(pc)
            
        m.drawcoastlines(linewidth=0.25, color="#3b3b3b") 
        m.drawcountries()
        m.drawstates()
        m.drawmapboundary()
        m.fillcontinents(color='white', lake_color='grey', zorder=0)
        m.drawmapboundary(fill_color='grey')
    
        divider = make_axes_locatable(plt.gca())
        cax = divider.append_axes("bottom", 
                                  "2%", 
                                  pad="2.5%")
                        
        cbar = custom_colorbar(cmap, ncolors=len(labels)+1, 
                               labels=labels, 
                               orientation='horizontal', 
                               cax=cax)
        cbar.ax.tick_params(labelsize=6)
        
        #print("--- %s sekunder att skapa karta) ---" % (time.time() - start_time))      
            
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
        
        NOTE: going to be depreciated someday!

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
          
    lon_bins = np.linspace(9.5, 28.5, xBins)
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
            
        fig = plt.figure(figsize=(3.45*len(coordinatesByWord),6))
        
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
                llcrnrlon = 9.5
                llcrnrlat = 54.5
                urcrnrlon = 28.5
                urcrnrlat = 69.5
            
            m = Basemap(projection='merc',
                        resolution=resolution, 
                        area_thresh=area_thresh,
                        llcrnrlon=llcrnrlon, 
                        llcrnrlat=llcrnrlat,
                        urcrnrlon=urcrnrlon, 
                        urcrnrlat=urcrnrlat,)   
            
            m.drawcoastlines(linewidth=0.25, color="#3b3b3b")
            m.drawcountries()
            m.drawmapboundary()
            m.fillcontinents(color='white',
                             lake_color='grey',
                             zorder=0)
            m.drawmapboundary(fill_color='grey')
            
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
                               or "hitsthreshold:" in o
                               or "onemap:" in o]
                               
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
                               and "hitsthreshold:" not in w
                               and "onemap:" not in w]
    
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
        
    try:
        oneMap = int([o.split(":")[1].strip()
               for o in operators if "onemap:" in o][0])
        if oneMap == 1:
            oneMap = True
    except:
        oneMap = False
        
    return operators, queryWords, xbins, scatter, zoom, rankthreshold, datespan, binThreshold, binType, binModel, hitsThreshold, oneMap

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
        start_time = time.time()
        coordinates, dates, ranks = [], [], []
        fewResults = False
        if datespan:
            try:
                dateFrom = datespan.split("->")[0].encode('utf-8')
                dateTo = datespan.split("->")[1].encode('utf-8')
                spanQuery = "AND posts.date BETWEEN CAST('"+dateFrom+"' AS DATE) "
                spanQuery += "AND CAST('"+dateTo+"' AS DATE) "   
            except:
                spanQuery = ""
        else:
            spanQuery = ""

        if " EXCLUDE " in word:
            exclude = word.split(" EXCLUDE ")[1].replace('"',"")
            word = word.split(" EXCLUDE ")[0]
        else:
            exclude = None

        if exclude:
            print "Exkluderar:", exclude
        
        attempts = 0

        while attempts < 3:
            try:
                mysqldb.query("set names 'utf8'")
                result = mysqldb.query("select count(*) as c from posts "
                                       "WHERE MATCH(text) "
                                       "AGAINST('{}' IN BOOLEAN MODE)".format(word.encode('utf-8')))
                for row in result:
                    print "--- Ordet {} har {} träffar, kör dem nu ---".format(word.encode('utf-8'), row['c'])

                break
            except sqlalchemy.exc.OperationalError:
                print "--- MySQL ej tillgänglig, testar igen ---"
                attempts += 1    

        mysqldb.query("set names 'utf8'")
        result = mysqldb.query("SELECT blogs.longitude, "
                               "blogs.latitude, "
                               "blogs.source, "
                               "posts.text, "
                               "posts.date, "
                               "blogs.rank, "
                               "blogs.id as blogid "
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
        
        # Get all lon and lats, and dates
        # and keywords in contexts (kwic)
        wordkwic = []
        i = 0
        oldkwic = ""
        for row in result:
            if exclude:
                if exclude.encode('utf-8') in row['text'] or word.encode('utf-8') not in row['text']:   
                    continue         

            coordinates.append([row['longitude'], 
                                row['latitude']])
            dates.append(row['date'])
            ranks.append(row['rank'])
            
            newkwic = kwic(row['text'], word, row['source']+":"+str(row['blogid']))
            if oldkwic != newkwic and i < 50:
                i += 1

                if type(newkwic) is list:
                    wordkwic += newkwic
                    oldkwic = newkwic
                else:
                    wordkwic.append(newkwic)
                    oldkwic = newkwic
        
        def addNoise(coordinates):
            np.random.seed(seed=666)
            start_time = time.time()
            coordinates = [tuple(c) for c in coordinates]
            lon, lat = zip(*coordinates)
            lon = np.array(lon) + np.random.normal(0, 0.5, len(lon))
            lat = np.array(lat) + np.random.normal(0, 0.5, len(lat))
            coordinates = zip(lon, lat)
            coordinates = [list(c) for c in coordinates]
            print("--- %s lägga på brus ---" % (time.time() - start_time))

            return coordinates

        if binModel == "noise" or binModel == "noise+mp":
            coordinates = addNoise(coordinates)

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

        print("--- %s sekunder att hämta data för ett ord ---" % (time.time() - start_time))
    
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
    

@app.route('/', methods = ['GET', 'POST'])
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

    operators, queryWords, xbins, scatter, zoom, rankthreshold, datespan, binThreshold, binType, binModel, hitsThreshold, oneMap = getOperators(queryWords)
            
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
                                         stats=None)


@app.route('/sinus/explore', methods = ['GET', 'POST'])
@app.route('/sinus/explore/<region>', methods = ['GET'])
def explore(region=None):
    """ Run if explore in the menu is choosen """    
    
    data = {}
    db = dataset.connect(c.LOCATIONDB)

    if not region:
        regions = []
        for result in db['worddeviations'].distinct('region'):
            regions.append(result['region'])
    else:
        regions = [region]

    for region in regions:
        tokens = []
        deviations = []
        for result in db['worddeviations'].find(region=region):
            tokens.append(result['token'].decode('latin-1'))
            deviations.append(result['deviation'])

        skewedWords = zip(tokens, deviations)
        skewedWords = sorted(skewedWords, key=lambda tup: tup[1], reverse=True)
        data[region] = skewedWords  
             
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
        
        operators, queryWords, xbins, scatter, zoom, rankthreshold, datespan, binThreshold, binType, binModel, hitsThreshold, oneMap = getOperators(queryWords)
              
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

        if oneMap:
            # Get main image with shapefiles
            fewResults, filename, gifFileName = genOneMapShapefileImg(coordinatesByWord, None, # ranks=None
                                                                words, zoom,
                                                                binThreshold=binThreshold,
                                                                binModel=binModel)          
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
                          'hits': hits,
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