#!/usr/bin/python
# -*- coding: utf-8 -*-

from dialectBot import app
from flask import Flask, jsonify, make_response, request, render_template, redirect, url_for
from werkzeug import secure_filename
import json
import cPickle as pickle

import binascii
import dataset
import datetime
import geocode    
import hashlib
import math
import ast
import numpy as np
from numpy import inf
import os
import pandas as pd
import sqlalchemy
import requests

from dialectBot.config import questions
import dialectBot.config as c

bots = []

def add_datapoints(username, lat, lon, found_words):
    """ Add datapoints to database from user """

    randomHandler = binascii.b2a_hex(os.urandom(15))[:10]
    randomHandler = secure_filename(randomHandler)
    uniqeHandler = "dialectbot://" + username
    
    blog = dict(url=uniqeHandler, 
                source="dialectbot",
                rank=5,
                longitude=lon,
                latitude=lat)

    mysqldb['blogs'].insert(blog)
    insertedId = mysqldb['blogs'].find_one(url=uniqeHandler)['id']

    for word in found_words:
        post = dict(blog_id=insertedId, 
                    date=datetime.datetime.now(),
                    text=word.encode('utf-8'))
        #print post
        mysqldb['posts'].insert(post)

    
@app.route('/<word>/-------------------------/<username>/<question_id>/<lat>/<lon>/', methods=['GET'])
def add_data(word, username, question_id, lat, lon): 

    if request.remote_addr in bots:
        print "Blockar bot."
        make_response("Silly bot")

    r = requests.get('http://freegeoip.net/json/{}'.format(request.remote_addr))
    user_loc = r.json()
    if not user_loc['country_name'] in ['Sweden', 'Finland']:
        print "Stoppar förmodligen en bot."
        bots.append(user_loc['country_name'])
        return make_response("You need an Swedish ip. So I don't think you're an bot.")

    print questions[int(question_id)]['answers']
    print word
    if word in questions[int(question_id)]['answers']:
        add_datapoints(username=username,
                       lat=lat,
                       lon=lon,
                       found_words=[word])
         
        print "Nog en människa allt"
        return make_response("Tack! Nu vet jag lite mer!")
    else:
        return make_response("Det var inte ett svar jag förväntade mig.")

try:
    mysqldb = dataset.connect(c.LOCATIONDB) 
    mysqldb.query("set names 'utf8'") # Might help
except sqlalchemy.exc.OperationalError:
    print "No connection to mysql. Cache better work or it will fail."

np.set_printoptions(formatter={'float': lambda x: "{0:0.4f}".format(x)}, linewidth=155)
    