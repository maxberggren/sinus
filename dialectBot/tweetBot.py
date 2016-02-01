# -*- coding: utf-8 -*-

import sys

OAUTH_TOKEN = '4793631879-xiPV85oSFRimaFoHoiz6ZX0vidk55fOe2WdF1Fv'
OAUTH_SECRET = '0KUQMANJnWueAYOchgT29Bjgg3dF4YraLgbryiRJiXSCy'
CONSUMER_KEY = 'LtW6NFJPOsfb18Mx7y9z5mTrD'
CONSUMER_SECRET = 'aHOb1d4A866HQLTb7NKTydB9GClMmrZAAdHng6GXq27InjtKeA'

from twython import TwythonStreamer
import json
from config import questions

import tweepy

class MyStreamer(TwythonStreamer):

    def on_success(self, data):
        #print json.dumps(data, indent=2, sort_keys=True)
        if data['place']['country'] in ['Sverige', 'Finland']:
            username = data['user']['screen_name']
            #username = "maxberggren"
            place = data['place']['full_name']
            city = data['place']['name']
            country = data['place']['country']
            coordinates = data['place']['bounding_box']['coordinates']
            middle_of_box = coordinates[0][1]
            lat = middle_of_box[0]
            lon = middle_of_box[1]

            print data['place']

            question_links = ""
            q = questions[1]
            i = 1
            for index, a in enumerate(q['answers']):
                question_links += u"({}) http://dialektbot.se:5050/{}/-------------------------/{}/{}/{}/{}/\n".format(1+index, a, username, i, lat, lon)


            tweet = '@{username}\n\n{question_links}'.format(username=username,
                                                             question_links=question_links)
            print tweet

            # Let's tweet
            auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
            auth.set_access_token(OAUTH_TOKEN, OAUTH_SECRET)
            api = tweepy.API(auth)

            api.update_with_media(q['img_path'], status=tweet) 


                    
    def on_error(self, status_code, data):
        print status_code, data



stream = MyStreamer(CONSUMER_KEY, CONSUMER_SECRET, OAUTH_TOKEN, OAUTH_SECRET)

while True:
    try: 
        #stream.statuses.filter(track='twitter')
        print "Hämtar tweets"
        stream.statuses.filter(locations='10, 54.329444, 25.068611, 69.329444')
        #stream.read_data_from_file()
    except KeyboardInterrupt:
        del stream
        break
    #except:
    #    print sys.exc_info()[0]
