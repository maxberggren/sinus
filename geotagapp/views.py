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


@app.route('/geotag/api/v1.0/tag', methods=['POST'])
@app.route('/geotag/api/v1.0/tag/placenessThreshold/<threshold>', methods=['POST'])
def api(threshold=None): 
    if not request.json or not 'text' in request.json:
        abort(400)
    print float(threshold)
    touple = model.predict(request.json['text'], threshold=float(threshold))   
    coordinate, placeness, mostUsefulWords, OOV, mentions = touple
    lon = coordinate[0]
    lat = coordinate[1]
    return jsonify( { 'latitude': lat, 
                      'longitude': lon, 
                      'placeness': placeness, 
                      'mostUsefulWords': mostUsefulWords,
                      'outOfVocabulary': OOV, 
                      'mentions': mentions } )




@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify( { 'error': 'Not found' } ), 404)

# Set up the geotagging model
model = tweetLoc(c.LOCATIONDB)
# Connect to DB
mysqldb = dataset.connect(c.LOCATIONDB) 
mysqldb.query("set names 'utf8'") # For safety
cache = SqliteCache("cache")