#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import division
from mpl_toolkits.basemap import Basemap, cm, maskoceans
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
from flask import Flask, jsonify, make_response, request, render_template, redirect
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
    
    
def colorCycle(i, scatter=False):
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
    
    if " or " in word.lower():
        words = word.lower().split(" or ")
        word = words[0] # Quickfix: choose the first in the or-clause
    if type(text) is str:
        try:
            text = text.decode("utf-8")
        except:
            return ""
        
    text = text.lower()
    left, sep, right = text.partition(word.lower().replace('"', ""))
    if sep:
        return "[" + source + "] " + left[-26:] + sep + right[:46]


def genShapefileImg(data, words, zoom, binThreshold, emptyBinFallback):
    """ Generate an image with shapefiles as bins 

    Parameters
    ----------
    coordinatesByWord : tuple
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


    lds, coord_count = [], {}

    for d, word in zip(data, words):
        coord_count[word] = len(d)
        ld = pd.DataFrame(d, columns=['longitude', 'latitude'])
        ld['word'] = word
        lds.append(ld)
    
    lds = pd.concat(lds)
    
    if zoom:
        llcrnrlon = lds['longitude'].quantile(0.16)
        llcrnrlat = lds['latitude'].quantile(0.17)
        urcrnrlon = lds['longitude'].quantile(0.86)
        urcrnrlat = lds['latitude'].quantile(0.85)
    else:
        llcrnrlon = 8
        llcrnrlat = 54.5
        urcrnrlon = 26
        urcrnrlat = 69.5
    
    m = Basemap(projection='merc',
                resolution = 'i', 
                area_thresh=500,
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
    
    # Municipality DF (SE + NO + FI)
    polygons = [Polygon(p) for p in m.muni] + \
               [Polygon(p) for p in m.muni_no] + \
               [Polygon(p) for p in m.muni_fi]
    names = [r['KNNAMN'] for r in m.muni_info] + \
            [r['NAVN'] for r in m.muni_no_info] + \
            [r['Kunta'] for r in m.muni_fi_info]
    areas = [r['LANDAREAKM'] for r in m.muni_info] + \
            [r['Shape_Area'] for r in m.muni_no_info] + \
            [0 for r in m.muni_fi_info]
    
    df_map_muni = pd.DataFrame({'poly': polygons, 'name': names, 'area': areas})
    
    # County DF
    df_map_county = pd.DataFrame({
        'poly': [Polygon(countys_points) for countys_points in m.countys],
        'name': [r['LAN_NAMN'] for r in m.countys_info]})
    
    mapped_points, all_points, hood_polygons_county = {}, {}, {}
    mapped_points_county, mapped_points_muni, hood_polygons_muni = {}, {}, {}
    
    for word, ld in lds.groupby(['word']):
        
        # Convert our latitude and longitude into Basemap cartesian map coordinates
        mapped_points[word] = [Point(m(mapped_x, mapped_y)) 
                               for mapped_x, mapped_y 
                               in zip(ld['longitude'], ld['latitude'])]
                               
        all_points[word] = MultiPoint(mapped_points[word])
    
        # Use prep to optimize polygons for faster computation
        hood_polygons_county[word] = prep(MultiPolygon(list(df_map_county['poly'].values)))
        hood_polygons_muni[word] = prep(MultiPolygon(list(df_map_muni['poly'].values)))
    
        # Filter out the points that do not fall within the map we're making
        mapped_points_county[word] = filter(hood_polygons_county[word].contains, all_points[word])
        mapped_points_muni[word] = filter(hood_polygons_muni[word].contains, all_points[word])
    
    
    def num_of_contained_points(apolygon, mapped_points):
        """ Counts number of points that fall into a polygon """
        return int(len(filter(prep(apolygon).contains, mapped_points)))
    
    for word in words:
        df_map_county[word] = df_map_county['poly'].apply(num_of_contained_points, 
                                                          args=(mapped_points_county[word],))
        df_map_muni[word] = df_map_muni['poly'].apply(num_of_contained_points, 
                                                      args=(mapped_points_muni[word],))
    
    # Get total occurencies in every county/municipality
    df_map_county["sum"] = df_map_county[words].sum(axis=1)
    df_map_muni["sum"] = df_map_muni[words].sum(axis=1)
    
    # Convert to percentages and skip where there is none
    def df_percent(df_map):
        df_map = df_map[df_map['sum'] > binThreshold]
        df_map[words] = df_map[words].astype('float').div(df_map["sum"].astype('float'), axis='index')
        return df_map
    
    df_map_county = df_percent(df_map_county)
    df_map_muni = df_percent(df_map_muni)
    
    # We'll only use a handful of distinct colors for our choropleth. 
    # These will be overwritten if only one word is being plotted.
    breaks = [0., 0.25, 0.5, 0.75, 1.0]
    
    def self_categorize(entry, breaks):
        for i in range(len(breaks)-1):
            if entry > breaks[i] and entry <= breaks[i+1]:
                return i
        return -1
    
    labels = ['0 %', '25 %', '50 %', '75 %', '100 %']
    
    fig = plt.figure(figsize=(3.25*len(words),6))
    
    for i, word in enumerate(words):
        df_map_county['jenks_bins_'+word] = df_map_county[word].apply(self_categorize, args=(breaks,))
        df_map_muni['jenks_bins_'+word] = df_map_muni[word].apply(self_categorize, args=(breaks,))
    
        ax = fig.add_subplot(1, len(words), int(i+1), axisbg='w', frame_on=False)
        ax.set_title(u"{word} - hits: {hits}".format(word=word, hits=coord_count[word]), 
                     y=1.01, fontsize=9)
    
        cmap = plt.get_cmap(colorCycle(i))
        cmap = opacify(cmap)
        
        print "emptybinfallack:", emptyBinFallback
        if emptyBinFallback == 'county':
            # Optional fallback for empty bins
            shapesToPutOnMap = [df_map_county, df_map_muni]
        else: 
            shapesToPutOnMap = [df_map_muni]
        
        for df_map in shapesToPutOnMap:
        
            if len(words) == 1: # When only one word, use Jenkins natural breaks
                breaks = Natural_Breaks(df_map['sum'], initial=300, k=3)
                df_map['jenks_bins_'+word] = breaks.yb
                
                labels = ['0', "> 0"] + ["> %d"%(perc) for perc in breaks.bins[:-1]]
    
            # Draw neighborhoods with grey outlines
            df_map['patches'] = df_map['poly'].map(lambda x: PolygonPatch(x, 
                                                                          ec='#111111', 
                                                                          lw=0, 
                                                                          alpha=0, 
                                                                          zorder=4))
            pc = PatchCollection(df_map['patches'], match_original=True)
            # Apply our custom color values onto the patch collection
            cmap_list = [cmap(val) for val in (df_map['jenks_bins_'+word].values - 
                                               df_map['jenks_bins_'+word].values.min())/(
                                                      df_map['jenks_bins_'+word].values.max()-
                                                      float(df_map['jenks_bins_'+word].values.min()))]
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
        
        
            
    fig.tight_layout(pad=2.5, w_pad=0.1, h_pad=0.0) 
    plt.plot()

    # Generate randomized filename
    filename = "_".join(words) + "_"
    filename += binascii.b2a_hex(os.urandom(15))[:10]
    filename = secure_filename(filename)
    
    emptyFolder('sinusGUIapp/static/maps/')
    plt.savefig("sinusGUIapp/static/maps/" + filename +".png", 
                dpi=100)
    plt.savefig("sinusGUIapp/static/maps/" + filename +".pdf", 
                dpi=100, 
                bbox_inches='tight')

    #return fewResults, filenameSF, gifFileName 
    return False, filename, None 


def genGridImg(coordinatesByWord, xBins, words, zoom,
              xyRatio, blurFactor, minCoordinates, 
              scatter, hits, chunks=1, dates=None, binThreshold=5):

    """ Generate the images i.e. the main image, the 
        time series gif and the histogram.

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
                          s=80,
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
            emptyFolder('sinusGUIapp/static/maps/')
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
    
    return fewResults, filename, gifFileName


def getData(words, xBins=None, scatter=None, zoom=None,
            xyRatio=1.8, blurFactor=0.6, rankthreshold=3, 
            binThreshold=5, datespan=None, binType="shape",
            emptyBinFallback=None):

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
    
    coordinatesByWord = ()
    minCoordinates = 99999999999999 # Shame!
    hits = {}
    KWIC = {}
    
    for word in words:
        coordinates, dates = [], []
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
                               "ORDER BY posts.date " )
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
            
            newkwic = kwic(row['text'], word, row['source'])
            if oldkwic != newkwic and i < 50:
                i += 1
                wordkwic.append(newkwic)
                oldkwic = newkwic
        
        KWIC[word.replace('"',"")] = wordkwic
        
        coordinatesByWord = coordinatesByWord + (coordinates,)
        hits[word] = len(coordinates)
        
        if len(coordinates) < minCoordinates:
            minCoordinates = len(coordinates)
                
    if minCoordinates > 4:

        if not xBins: # xBins not set: "guestimate" that 2 hits per bin is good
            xBins = math.sqrt(float(minCoordinates)/
                                         (float(xyRatio)*float(2)))
            xBins = int(xBins)            

        if binType == "shape":
            # Get main image with shapefiles
            fewResults, filename, gifFileName = genShapefileImg(coordinatesByWord, words, zoom,
                                                                binThreshold=binThreshold,
                                                                emptyBinFallback=emptyBinFallback)
        if binType == "square":
            # Get main image
            fewResults, filename, gifFileName = genGridImg(coordinatesByWord, 
                                                          xBins,
                                                          words,
                                                          zoom,
                                                          xyRatio, 
                                                          blurFactor, 
                                                          minCoordinates,
                                                          scatter,
                                                          hits,
                                                          chunks=1,
                                                          binThreshold=binThreshold)
            # Get time series gif
            fewResults, giffile, gifFileName = genGridImg(coordinatesByWord, 
                                                         xBins,
                                                         words,
                                                         zoom,
                                                         xyRatio, 
                                                         blurFactor, 
                                                         minCoordinates,
                                                         scatter,
                                                         hits,
                                                         chunks=7,
                                                         dates=dates,
                                                         binThreshold=binThreshold)
            
            if gifFileName: # no gif = no histogram                                     
                dateHistogram(dates, gifFileName)
            
        return filename, hits, KWIC, fewResults, gifFileName
        
    else: # if a term has to few hits
        return None, hits, KWIC, fewResults, None
    

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
    
    ### Statistics
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
                               or "emptybinfallback:" in o]
                               
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
                               and "emptybinfallback:" not in w]
    
    try:
        xbins = int([o.split(":")[1].strip()
                    for o in operators if "xbins:" in o][0])
    except:
        xbins = None

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
        emptyBinFallback = [o.split(":")[1].strip()
               for o in operators if "emptybinfallback:" in o][0]
    except:
        emptyBinFallback = None
            
            
    if len(queryWords) > 0:
        touple = getData(queryWords,        
                         xBins=xbins,
                         scatter=scatter,
                         zoom=zoom,
                         rankthreshold=rankthreshold,
                         binThreshold=binThreshold,
                         datespan=datespan,
                         binType=binType,
                         emptyBinFallback=emptyBinFallback)
                         
        filename, hits, KWICs, fewResults, gifFileName = touple
                              
        documentQuery = { 'query': query,
                          'filename': filename,
                          'hits': hits,
                          'KWICs': KWICs,
                          'fewResults': fewResults,
                          'gifFileName': gifFileName }
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