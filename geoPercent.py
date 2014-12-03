# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat> 

import sys
import dataset    
import codecs   
import datetime
import sys
import config as c
import traceback

OAUTH_TOKEN = c.OAUTH_TOKEN
OAUTH_SECRET = c.OAUTH_SECRET
CONSUMER_KEY = c.CONSUMER_KEY
CONSUMER_SECRET = c.CONSUMER_SECRET

from twython import TwythonStreamer
import json

tweetsdb = dataset.connect(c.LOCATIONDB)
tweetsdb.begin()
twittertable = tweetsdb['tweets']

class MyStreamer(TwythonStreamer):

    def __init__(self):
        self.tweets = 0
        self.geotweets = 0
        
    def on_success(self, data):
        self.tweets =+ 1
        
        if 'text' in data:
            if data['geo']:  
                print data  
                print "%.2f% %" % (100.0 * self.geotweets/self.tweets) 
                try: 
                    lon = data['coordinates']['coordinates'][0]
                    lat = data['coordinates']['coordinates'][1] 
                    self.tweets =+ 1
                except Exception:
                    pass
                    
    def on_error(self, status_code, data):
        print status_code, data

stream = MyStreamer(CONSUMER_KEY, CONSUMER_SECRET, OAUTH_TOKEN, OAUTH_SECRET)

while True:
    try: 
        #stream.statuses.filter(track='twitter')
        print "Hämtar tweets"
        stream.statuses.filter(language="sv")
    except KeyboardInterrupt:
        print "\nExiting..."
        break
    except:
        #print sys.exc_info()[0]
        traceback.print_exc(file=sys.stdout)
