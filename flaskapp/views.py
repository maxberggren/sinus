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
import matplotlib.pyplot as plt
from flaskapp import app
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

def dateHistogram(dates, filename):
    """Create histogram of given dates

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
    filename = "flaskapp/static/maps/" + filename +"_hist.png"
    plt.savefig(filename, dpi=100)

def emptyFolder(folder):
    """Empty folder so we won't run out of hdd space

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
    """Connect to Gavagai API to get synonyms

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
    """Make KeyWord In Context

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

def genImages(coordinatesByWord, xBins, words, zoom,
              xyRatio, blurFactor, minCoordinates, 
              scatter, hits, chunks=1, dates=None):

    """Generate the images i.e. the main image, the 
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

    # Making of time series gif only possible when
    # looking at only one word.
    if chunks > 1 and len(coordinatesByWord) != 1:
        return False, None, None
        
    fewResults = False
    gifFileName = None
    
    colorCycle = ['Reds', 'Blues', 'Oranges', 'BuGn', 'PuRd', 'Purples',
                  'Reds', 'Blues', 'Oranges', 'BuGn', 'PuRd', 'Purples',
                  'Reds', 'Blues', 'Oranges', 'BuGn', 'PuRd', 'Purples',
                  'Reds', 'Blues', 'Oranges', 'BuGn', 'PuRd', 'Purples']
    colorCycleScatter = ['blue', 'red', 'green', 'magenta', 'cyan',
                         'blue', 'red', 'green', 'magenta', 'cyan',
                         'blue', 'red', 'green', 'magenta', 'cyan',
                         'blue', 'red', 'green', 'magenta', 'cyan']
          
    lon_bins = np.linspace(8, 26, xBins)
    lat_bins = np.linspace(54.5, 69.5, xBins*xyRatio)
    gifFilenames = []
    nBins = len(lon_bins)*len(lat_bins)
    
    if dates:
        dates = np.array_split(dates, chunks)
        
    for chunk in range(chunks):
            
        totCoordinates = 0
        totDensity = np.ones((len(lat_bins)-1, 
                              len(lon_bins)-1))*0.00000000000000001
        
        for kordinater in coordinatesByWord:
            # Coordinates to be put into chunks
            kordinater = np.array_split(kordinater, chunks)
            
            totCoordinates += len(kordinater[chunk])
            
            lons, lats = zip(*kordinater[chunk])
            subdensity, _, _ = np.histogram2d(lats, lons, 
                                              [lat_bins, lon_bins])
            totDensity += subdensity
                
        #totDensity = ndimage.gaussian_filter(totDensity, blurFactor)
            
        fig = plt.figure(figsize=(3.25*len(coordinatesByWord),6))
        
        for i, kordinater in enumerate(coordinatesByWord):
            word = words[i]
            kordinater = np.array_split(kordinater, chunks)
            
            if dates:
                maxdateInChunk = max(dates[chunk])
                mindateInChunk = min(dates[chunk])
                fig.suptitle('{:%Y-%m-%d} - {:%Y-%m-%d}'.format(mindateInChunk, 
                                                                maxdateInChunk),
                             fontsize=9)             
            
            lons, lats = zip(*kordinater[chunk])             
            lons = np.array(lons)
            lats = np.array(lats)
        
            ax = fig.add_subplot(1, len(coordinatesByWord), int(i+1))
            ax.set_title(word + " (" + str(len(kordinater[chunk])) 
                         + u" träffar)", 
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
                                            
            # Filter out bins with to few hits
            density[density < 5] = 0 
    
            #density = ndimage.gaussian_filter(density, blurFactor)
    
            lon_bins_2d, lat_bins_2d = np.meshgrid(lon_bins, 
                                                   lat_bins)
            xs, ys = m(lon_bins_2d, lat_bins_2d)
            xs = xs[0:density.shape[0], 0:density.shape[1]]
            ys = ys[0:density.shape[0], 0:density.shape[1]]
                    
            # Colormap transparency
            theCM = cm.get_cmap(colorCycle[i])
            theCM._init()
            alphas = np.abs(np.linspace(0, 1.0, theCM.N))
            theCM._lut[:-3,-1] = alphas
            
            # SCATTERPLOT if to few coordinates or manual override
            if minCoordinates < 50 or scatter == 1:
                x1, y1 = m(lons, lats) 
                m.scatter(x1[0:1000], 
                          y1[0:1000], 
                          alpha=1, 
                          c=colorCycleScatter[i], 
                          s=80,
                          edgecolors='none')
                fewResults = True
                
            else: # 2DHISTPLOT if enough coordinates
                if len(coordinatesByWord) == 1:
                    # One term means logplot
                    if chunks != 1: 
                        # For animation, 
                        # we need to fix z-axis
                        # if this is part of a chunking
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
                
                # And fix ticks
                if len(coordinatesByWord) != 1:
                    colorbar.set_ticks([0, 0.25, 0.5, 0.75, 1])            
                    colorbar.set_ticklabels(["0 %",
                                             "25 %",
                                             "50 %", 
                                             "75 %",
                                             "100 %"])
                
                colorbar.ax.tick_params(labelsize=6) 
            
        fig.tight_layout(pad=2.5, w_pad=0.1, h_pad=0.0) 
    
        # Generate filename
        filename = "_".join(words) + "_"
        filename += binascii.b2a_hex(os.urandom(15))[:10]
        filename = secure_filename(filename)
    
        # Create images
        if chunks > 1: # We are saving a timeseries
        
            gifFilename = "flaskapp/static/maps/" 
            gifFilename += filename +"_"+str(chunk)+".png"
                          
            gifFilenames.append(gifFilename) # Save for giffing
            plt.savefig(gifFilename, dpi=100)
            
        else: # Just saving one image
            emptyFolder('flaskapp/static/maps/')
            plt.savefig("flaskapp/static/maps/" + filename +".png", dpi=100)
            plt.savefig("flaskapp/static/maps/" + filename +".pdf", dpi=100)        

    # If timeseries created - GIFfify it!
    if chunks > 1: 
        gifFilenames = gifFilenames + gifFilenames[::-1]
        images = [Image.open(fn) for fn in gifFilenames]
        gif2file = "flaskapp/static/maps/" + filename +".gif"
        writeGif(gif2file, images, duration=0.5)
        gifFileName = filename
    
    return fewResults, filename, gifFileName

def getData(words, xBins=None, scatter=None, zoom=None,
            xyRatio=1.8, blurFactor=0.6, uselowqualdata=0):

    """Retrive data from the document database

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
    uselowqualdata : int
        1 if blogs that only have inferred coordinate
        should be used. that means the geotagging done
        by tagData.py

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
        if uselowqualdata == 0:
            queryuselowqualdata = "AND rank <> 4"
        else:
            queryuselowqualdata = ""

        result = mysqldb.query("SELECT blogs.longitude, "
                               "blogs.latitude, "
                               "blogs.source, "
                               "posts.text, "
                               "posts.date, "
                               "blogs.id "
                               "FROM posts INNER JOIN blogs ON "
                               "blogs.id=posts.blog_id "
                               "WHERE MATCH(posts.text) "
                               "AGAINST ('" + word + "' "
                               "IN BOOLEAN MODE) "
                               "AND blogs.latitude is not NULL "
                               " " + queryuselowqualdata + " "
                               "ORDER BY posts.date ") 
                               #ORDER BY RAND() limit 15000?
        
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

        if not xBins: # xBins not set? "guestimate" that 2 hits per bin is good
            xBins = math.sqrt(float(minCoordinates)/
                                         (float(xyRatio)*float(2)))
            xBins = int(xBins)            

        # Get main image
        fewResults, filename, gifFileName = genImages(coordinatesByWord, 
                                                      xBins,
                                                      words,
                                                      zoom,
                                                      xyRatio, 
                                                      blurFactor, 
                                                      minCoordinates,
                                                      scatter,
                                                      hits,
                                                      chunks=1)
        # Get time series gif
        fewResults, giffile, gifFileName = genImages(coordinatesByWord, 
                                                     xBins,
                                                     words,
                                                     zoom,
                                                     xyRatio, 
                                                     blurFactor, 
                                                     minCoordinates,
                                                     scatter,
                                                     hits,
                                                     chunks=7,
                                                     dates=dates)
        
        if gifFileName: # no gif = no histogram                                     
            dateHistogram(dates, gifFileName)

        return filename, hits, KWIC, fewResults, gifFileName
        
    else: # if a term has to few hits
        return None, hits, KWIC, fewResults, None
    

@app.route('/localize/api/v1.0/localize', methods = ['POST'])
def api(): 
    if not request.json or not 'text' in request.json:
        abort(400)
     
    touple = model.predict(request.json['text'])   
    coordinate, placeness, mostUsefulWords, OOV, mentions = touple
    lon = coordinate[0]
    lat = coordinate[1]
    return jsonify( { 'latitude': lat, 
                      'longitude': lon, 
                      'placeness': placeness, 
                      'mostUsefulWords': mostUsefulWords,
                      'outOfVocabulary': OOV, 
                      'mentions': mentions } )


@app.route('/sinus', methods = ['GET', 'POST'])
@app.route('/sinus/', methods = ['GET', 'POST'])
@app.route('/sinus/search/<urlSearch>', methods = ['GET'])
def site(urlSearch=None):
    """Run if index/search view if choosen

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
    # Initialize for stats
    stats = {}
    
    # Get sourcecount for sources that have lon lat
    key = "sourceswithlatlon2"
    if not cache.get(key):
        stats[key] = []
        result = mysqldb.query("SELECT source, rank, COUNT(*) as count FROM blogs "
                               "WHERE longitude is not NULL "
                               "GROUP BY source, rank ORDER BY count DESC") 
        for row in result:
            stats[key].append(row)
        
        cache.set(key, stats[key], timeout=60*60*3) # cache for 3 hours    
    else:
        stats[key] = cache.get(key)
    
    # Get sourcecount for sources that yet have no lat lon
    key = "sourceswithoutlatlon2"
    if not cache.get(key):
        stats[key] = []
        result = mysqldb.query("SELECT source, rank, COUNT(*) as count FROM blogs "
                               "WHERE longitude is NULL AND rank <> 9999 "
                               "GROUP BY source, rank ORDER BY count DESC") 
        for row in result:
            stats[key].append(row)
        
        cache.set(key, stats[key], timeout=60*60*3) # cache for 3 hours    
    else:
        stats[key] = cache.get(key)


      
    # Classify text
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
        
    # Search in document database
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
                               or "uselowqualdata:" in o]
                               
    queryWords = [w.strip() for w in queryWords 
                            if "age:" not in w 
                               and "gender:" not in w
                               and "xbins:" not in w
                               and "scatter:" not in w
                               and "zoom:" not in w
                               and "uselowqualdata:" not in w]
    
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
        uselowqualdata = int([o.split(":")[1].strip()
               for o in operators if "uselowqualdata:" in o][0])
    except:
        uselowqualdata = 0
            
            
    if len(queryWords) > 0:
        touple = getData(queryWords,        
                         xBins=xbins,
                         scatter=scatter,
                         zoom=zoom,
                         uselowqualdata=uselowqualdata)
                         
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
f = codecs.open("flaskapp/orter.txt", encoding="utf-8")
for line in f:
    s.add(line.lower().strip())
    
cache = SqliteCache("cache")