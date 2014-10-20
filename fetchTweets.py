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

print "hej"

tweetsdb = dataset.connect(c.LOCATIONDB)
tweetsdb.begin()
twittertable = tweetsdb['tweets']

class MyStreamer(TwythonStreamer):

    def on_success(self, data):
        if 'text' in data:
            if data['geo']:    
                #print data
                saveTweet(data)            
                #with open(filename, "a") as myfile:
                #    #print data
                #    myfile.write(parseJSON(data))
                #    #myfile.write("\n") 
                    
    def on_error(self, status_code, data):
        print status_code, data
        

def cleanData(inputText):
    """
    Tar bort förbjudna tecken och gör allt till lowercase.
    Kan vara bra när vild data läses in som ska bestämmas.
    """
    toFile = inputText
    #toFile = toFile.decode('utf-8') # ??
    toFile = toFile.lower()     
    #toFile = toFile.encode('utf-8') # ??           
    for deletePlz in (codecs.open("forbidden.txt", "r", "utf-8").read()).split():
        toFile = toFile.replace(deletePlz," ")
    toFile = toFile.replace("             ", " ")
    toFile = toFile.replace("            ", " ")
    toFile = toFile.replace("           ", " ")
    toFile = toFile.replace("          ", " ")
    toFile = toFile.replace("         ", " ")
    toFile = toFile.replace("        ", " ")
    toFile = toFile.replace("       ", " ")
    toFile = toFile.replace("      ", " ")
    toFile = toFile.replace("     ", " ")
    toFile = toFile.replace("    ", " ")
    toFile = toFile.replace("   ", " ")
    toFile = toFile.replace("  ", " ")
    toFile = toFile.replace("'", "")
    toFile = toFile.replace(" t ", " ")
    toFile = toFile.replace(" co ", " ")
    toFile = toFile.replace("http", " ")    

    toFile = toFile.replace("\r\n", "\n")     
    toFile = toFile.replace("\n\n\n", "\n\n")
    toFile = toFile.replace("\n\n\n\n", "\n\n")
    toFile = toFile.replace("\n\n\n\n\n", "\n\n")
    toFile = toFile.replace("\n\n\n\n\n\n", "\n\n")
    toFile = toFile.replace("\n\n\n\n\n\n\n", "\n\n")
    toFile = toFile.replace("\n\n\n\n\n\n\n\n", "\n\n")

    toFile = toFile.strip()

    toFile = toFile.replace("\t", "")      

    return toFile

def saveTweet(data):
    #bigram, words, data = [], [], ""
    #data = json.loads(data)
    #print data
    #print data
    if not float(data['coordinates']['coordinates'][0]) == 0:
        if not float(data['coordinates']['coordinates'][1]) == 0:
                        
            tweetText = data['text']
            tweetText = cleanData(tweetText)                                                 
            
            lon = data['coordinates']['coordinates'][0]
            lat = data['coordinates']['coordinates'][1]

            #METADATA
            try:
                country = data['place']['country'].lower()
            except:
                """
                print "Landnamn fanns ej i datan."  
                """
            try:
                location = cleanData(data['user']['location'].lower())
            except:
                """
                print "Användarlokation fanns ej i datan."  
                """

            try:
                username = "@" + cleanData(data['user']['screen_name'].lower())
            except:
                """
                print "Användarnamn fanns ej i datan."  
                """
            
            if country.lower() == c.TWITTERCOUNTRYFILTER_1 or country.lower() == c.TWITTERCOUNTRYFILTER_2:
                sys.stdout.write('.')  
                twittertable.insert(dict(tweet=tweetText, 
                                         lon=lon, 
                                         lat=lat, 
                                         metadata=country + " " + location,
                                         username=username,
                                         used=0))
                tweetsdb.commit()
                tweetsdb.begin()
            else:
                sys.stdout.write('x') 




stream = MyStreamer(CONSUMER_KEY, CONSUMER_SECRET, OAUTH_TOKEN, OAUTH_SECRET)

while True:
    try: 
        #stream.statuses.filter(track='twitter')
        print "Hämtar tweets"
        stream.statuses.filter(locations=c.TWITTERLOCFILTER)
    except KeyboardInterrupt:
        print "\nExiting..."
        break
    except:
        #print sys.exc_info()[0]
        traceback.print_exc(file=sys.stdout)
