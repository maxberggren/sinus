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
from geotagapp import app
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
import collections

def convert(data):
    if isinstance(data, basestring):
        return data.encode('utf-8')
    elif isinstance(data, collections.Mapping):
        return dict(map(convert, data.iteritems()))
    elif isinstance(data, collections.Iterable):
        return type(data)(map(convert, data))
    else:
        return data

@app.route('/geotag/api/v1.0/tag', methods=['POST'])
@app.route('/geotag/api/v1.0/tag/placenessThreshold/<threshold>', methods=['POST'])
@app.route('/geotag/api/v1.0/tag/threshold/<threshold>', methods=['POST'])
def tag(threshold=None): 
    if not request.json or not 'text' in request.json:
        abort(400)

    if isinstance(threshold, (unicode)):
        try:
            threshold = float(threshold)
        except:
            return jsonify( { 'error': "Threshold should be of the form 1e40." } )
        
    touple = model.predict(request.json['text'], threshold=threshold)   
    coordinate, placeness, mostUsefulWords, OOV, mentions = touple
    lon = coordinate[0]
    lat = coordinate[1]
    return jsonify( { 'latitude': lat, 
                      'longitude': lon, 
                      'placeness': placeness, 
                      'mostUsefulWords': mostUsefulWords,
                      'outOfVocabulary': OOV, 
                      'mentions': mentions } )


@app.route('/geotag/api/v1.0/tagnogmmmerging', methods=['POST'])
@app.route('/geotag/api/v1.0/tagnogmmmerging/threshold/<threshold>', methods=['POST'])
def tagnomerge(threshold=None): 
    if not request.json or not 'text' in request.json:
        abort(400)

    if isinstance(threshold, (unicode)):
        try:
            threshold = float(threshold)
        except:
            return jsonify( { 'error': "Threshold should be of the form 1e40." } )
        
    touple = model.predict(request.json['text'], threshold=threshold, mergeSubGMMs=False)   
    coordinate, placeness, mostUsefulWords, OOV, mentions = touple
    lon = coordinate[0]
    lat = coordinate[1]
    return jsonify( { 'latitude': lat, 
                      'longitude': lon, 
                      'placeness': placeness, 
                      'mostUsefulWords': mostUsefulWords,
                      'outOfVocabulary': OOV, 
                      'mentions': mentions } )
                      

@app.route('/geotag/api/v1.0/tagbyvote1', methods=['POST'])
@app.route('/geotag/api/v1.0/tagbyvote1/threshold/<threshold>', methods=['POST'])
def tagbyvote1(threshold=None): 
    touple = model.predictByVote1(request.json['text'], 
                                  threshold=threshold, 
                                  correctCoord=request.json['coord'])   
    coordinate, placeness, mostUsefulWords, OOV, mentions = touple
    lon = coordinate[0]
    lat = coordinate[1]
    return jsonify( { 'latitude': lat, 
                      'longitude': lon, 
                      'placeness': placeness, 
                      'mostUsefulWords': mostUsefulWords,
                      'outOfVocabulary': OOV, 
                      'mentions': mentions } )


@app.route('/geotag/api/v1.0/tagbyvote2', methods=['POST'])
@app.route('/geotag/api/v1.0/tagbyvote2/threshold/<threshold>', methods=['POST'])
def tagbyvote2(threshold=None): 

    touple = model.predictByVote1(model.predictByGrammar(request.json['text'], 
                                  threshold=threshold), 
                                  threshold=threshold, 
                                  correctCoord=request.json['coord'])   
    coordinate, placeness, mostUsefulWords, OOV, mentions = touple
    lon = coordinate[0]
    lat = coordinate[1]
    return jsonify( { 'latitude': lat, 
                      'longitude': lon, 
                      'placeness': placeness, 
                      'mostUsefulWords': mostUsefulWords,
                      'outOfVocabulary': OOV, 
                      'mentions': mentions } )


@app.route('/geotag/api/v1.0/tagbygrammar', methods=['POST'])
@app.route('/geotag/api/v1.0/tagbygrammar/threshold/<threshold>', methods=['POST'])
@app.route('/geotag/api/v1.0/tagbygrammar/mvp/<mvpThreshold>', methods=['POST'])
def tagbygrammar(threshold=None, mvpThreshold=None): 
    touple = model.predict(model.predictByGrammar(request.json['text'], threshold), 
                           threshold, mvpThreshold=mvpThreshold)   
                           
    coordinate, placeness, mostUsefulWords, OOV, mentions = touple
    lon = coordinate[0]
    lat = coordinate[1]
    return jsonify( { 'latitude': lat, 
                      'longitude': lon, 
                      'placeness': placeness, 
                      'mostUsefulWords': mostUsefulWords,
                      'outOfVocabulary': OOV, 
                      'mentions': mentions } )

@app.route('/geotag/api/v1.0/tagbygrammarnoclip', methods=['POST'])
@app.route('/geotag/api/v1.0/tagbygrammarnoclip/threshold/<threshold>', methods=['POST'])
def tagbygrammarnoclip(threshold=None): 
    touple = model.predict(model.predictByGrammar(request.json['text'], threshold, clipping=False), threshold)   
    coordinate, placeness, mostUsefulWords, OOV, mentions = touple
    lon = coordinate[0] 
    lat = coordinate[1]
    return jsonify( { 'latitude': lat, 
                      'longitude': lon, 
                      'placeness': placeness, 
                      'mostUsefulWords': mostUsefulWords,
                      'outOfVocabulary': OOV, 
                      'mentions': mentions } )
                      

@app.route('/geotag/api/v1.0/tagbyunique', methods=['POST'])
@app.route('/geotag/api/v1.0/tagbyunique/threshold/<threshold>', methods=['POST'])
def tagbyunique(threshold=None): 
    touple = model.predictByUnique(request.json['text'], threshold)   
    coordinate, placeness, mostUsefulWords, OOV, mentions = touple
    lon = coordinate[0]  
    lat = coordinate[1]
    return jsonify( { 'latitude': lat, 
                      'longitude': lon, 
                      'placeness': placeness, 
                      'mostUsefulWords': mostUsefulWords,
                      'outOfVocabulary': OOV, 
                      'mentions': mentions } )

@app.route('/geotag/api/v1.0/tagbytown', methods=['POST'])
@app.route('/geotag/api/v1.0/tagbytown/threshold/<threshold>', methods=['POST'])
def tagbytown(threshold=None): 
    touple = model.predictByTown(request.json['text'], threshold=threshold)   
    coordinate, placeness, mostUsefulWords, OOV, mentions = touple
    lon = coordinate[0]
    lat = coordinate[1]
    return jsonify( { 'latitude': lat, 
                      'longitude': lon, 
                      'placeness': placeness, 
                      'mostUsefulWords': mostUsefulWords,
                      'outOfVocabulary': OOV, 
                      'mentions': mentions } )


@app.route('/geotag/api/v1.0/trainingData/<ammountData>/pickRandom', methods=['GET'])
def pickRandomData(ammountData=None): 
    return getData(ammountData=ammountData, random=1)    
    
@app.route('/geotag/api/v1.0/trainingData/<ammountData>', methods=['GET'])
def getData(ammountData=None, random=0): 

    if not ammountData:
        ammountData = 10
    if random == 1:
        randomQ = " ORDER BY RAND()"
    else:
        randomQ = " ORDER by id DESC"     
    
    blogs = {}    
    mysqldb.query("set names 'utf8'")           
    for blogrow in mysqldb.query("SELECT b.* from blogs b "
                                 "WHERE (select count(*) from posts p where " 
                                 "       p.blog_id=b.id) > 0 "
                                 "AND rank = 2 AND "
                                 "longitude is not NULL "
                                 "latitude is not NULL "
                                 " " + randomQ + " "
                                 "order by b.id DESC"
                                 "limit " + str(ammountData)):
        
        blogtext = ""                  
        for postrow in mysqldb.query("SELECT * from posts "
                                     "WHERE blog_id = " + str(blogrow['id'])):

            blogtext += "\n\n" + postrow['text'].decode('latin-1')
            
        blogdata = { 'id': blogrow['id'],
                     'latitude': blogrow['latitude'], 
                     'longitude': blogrow['longitude'],
                     'city': blogrow['city'].decode('latin-1'),
                     'county': blogrow['county'].decode('latin-1'),
                     "municipality": blogrow['municipality'].decode('latin-1'),
                     "country": blogrow['country'].decode('latin-1'),
                     'text': blogtext  }
                     
        blogs[blogrow['url'].decode('latin-1')] = blogdata
            
    return jsonify( blogs )
                      


@app.route('/geotag/api/v1.0/evaluate', methods=['POST'])
def evaluate(): 
    
    errors = {}
    for key, val in request.json.iteritems():
        try:
            prediction = val
            blog = mysqldb['blogs'].find_one(id=int(key))
            error = haversine([blog['longitude'], blog['latitude']], 
                              [prediction['longitude'], prediction['latitude']])
            errors[int(key)] = error
        except TypeError:
            pass
    print errors
    
    print list(errors.values())
        
    return jsonify( { 'errors': errors,
                      'meanError': np.mean(list(errors.values())),
                      'medianError': np.median(list(errors.values())) } )


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify( { 'error': 'Not found' } ), 404)

# Set up the geotagging model
model = tweetLoc(c.LOCATIONDB)
# Connect to DB
mysqldb = dataset.connect(c.LOCATIONDB) 
mysqldb.query("set names 'utf8'") # For safety
cache = SqliteCache("cache")