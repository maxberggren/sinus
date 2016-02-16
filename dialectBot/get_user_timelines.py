# -*- coding: utf-8 -*-

import sys

import json
import re
import urlparse
import os
import cPickle as pickle
import config as c
import datetime
import time

from twython import TwythonStreamer
OAUTH_TOKEN = '18907132-YidrXI5huIhij4HrSjCA2rlm4cc5C7dkqgZiYvaKQ'
OAUTH_SECRET = 'eY9Ucsm3P9zc2LlFVhTqhvX5exQ5cItlRbpG4NTWlROYl'
CONSUMER_KEY = 'O5CSlnWPU6aMlSk5nUxO70LRB'
CONSUMER_SECRET = 'jteN6HOjCnHQYyz1sVPXIuB8E3rVDhWmW82b8aCbbA36vp5t3B'

import tweepy
auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(OAUTH_TOKEN, OAUTH_SECRET)
api = tweepy.API(auth)

import dataset
mysqldb = dataset.connect(c.LOCATIONDB) 
mysqldb.query("set names 'utf8'") # Might help

def add_datapoints(username, lat, lon, text):

    #random_handler = binascii.b2a_hex(os.urandom(15))[:10]
    #random_handler = secure_filename(random_handler)
    uniqe_handler = "twitter://" + username
    
    blog = dict(url=uniqe_handler, 
                source="twitter",
                rank=2,
                longitude=lon,
                latitude=lat)

    mysqldb['blogs'].upsert(blog, ['url'])
    inserted_id = mysqldb['blogs'].find_one(url=uniqe_handler)['id']

    post = dict(blog_id=inserted_id, 
                date=datetime.datetime.now(),
                text=text.encode('utf-8'))
    #print post
    mysqldb['posts'].insert(post)

def strip_tweet(tweet):
    new_string = ''
    for i in tweet.split():
        s, n, p, pa, q, f = urlparse.urlparse(i)
        if s and n:
            pass
        elif i[:1] == '@':
            pass
        elif i[:1] == '#':
            new_string = new_string.strip() + ' ' + i[1:]
        else:
            new_string = new_string.strip() + ' ' + i

    return new_string

# Set up list of last tweet for users
global user_last_id
filename = 'last_tweet.pkl'

if os.path.isfile(filename):
    with open(filename, 'r') as f:
        user_last_id = pickle.load(f) 
else:
    user_last_id = {}

class MyStreamer(TwythonStreamer):

    def on_success(self, data):
        #print data
        if data['place']['country'] in ['Sverige', 'Finland'] and data['user']['lang'] == "sv":
            username = data['user']['screen_name']
            #print data['text']
            try:
                timeline = api.user_timeline(data['user']['screen_name'], count=3200, since_id=user_last_id[username])
                print "This user is aldready saved. Taking only whats new."
                # Remeber last tweet collected
                last_id = timeline[0].id
                user_last_id[username] = last_id
            except (KeyError, IndexError):
                timeline = api.user_timeline(data['user']['screen_name'], count=3200)

            coordinates = data['place']['bounding_box']['coordinates']
            middle_of_box = coordinates[0][1]
            lat = middle_of_box[1]
            lon = middle_of_box[0]

            text_blob = ""
            for tweet in timeline:
                if tweet.text[0:3] != "RT ":
                    text_blob += "\n\n" + strip_tweet(tweet.text)

            print "@{}: {} tecken hämtades {}".format(username, len(text_blob), datetime.datetime.now())  
            add_datapoints(username, lat, lon, text_blob)
                    
    def on_error(self, status_code, data):
        print status_code, data


stream = MyStreamer(CONSUMER_KEY, CONSUMER_SECRET, OAUTH_TOKEN, OAUTH_SECRET)

while True:
    try: 
        print "Collecting"
        stream.statuses.filter(locations='10, 54.329444, 25.068611, 69.329444')
    except KeyboardInterrupt:

        with open(filename, 'wb') as f:
            pickle.dump(user_last_id, f, -1) 

        del stream
        break
    except TypeError:
        pass
    except:
        print sys.exc_info()[0]
        print "Väntar 2 timmar"
        time.sleep(60*60*2)

