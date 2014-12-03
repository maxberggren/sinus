# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat> 

import sys
import dataset    
import codecs   
import datetime
import sys
import config as c
import traceback
import json

OAUTH_TOKEN = c.OAUTH_TOKEN
OAUTH_SECRET = c.OAUTH_SECRET
CONSUMER_KEY = c.CONSUMER_KEY
CONSUMER_SECRET = c.CONSUMER_SECRET

from twython import TwythonStreamer
import json



class MyStreamer(TwythonStreamer):
        
    def on_success(self, data):
        try:
            self.tweets += 1
        except:
            self.tweets = 0
        
        if 'text' in data and data['lang'] == "sv":
#       if 'text' in data:

            if data['geo']:  
                try: 
                    lon = data['coordinates']['coordinates'][0] 
                    lat = data['coordinates']['coordinates'][1] 
                    try:
                        self.geotweets += 1
                    except:
                        self.geotweets = 0
                        
                except Exception:
                    pass

                print json.dumps(data['coordinates'], sort_keys=True, indent=4, separators=(',', ': '))  
                print data['text']
                print "########## %.2f% %" % (100.0 * self.geotweets/self.tweets)             
                    
    def on_error(self, status_code, data):
        print status_code, data

stream = MyStreamer(CONSUMER_KEY, CONSUMER_SECRET, OAUTH_TOKEN, OAUTH_SECRET)

while True:
    try: 
        print "Nu jävlar"
        stream.statuses.filter(track='när, och, om, på, här, att, för')
        #stream.statuses.filter(track='twitter')

    except KeyboardInterrupt:
        print "\nAvslutar..."
        break
    except:
        traceback.print_exc(file=sys.stdout)
