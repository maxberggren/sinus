#!/usr/bin/python
# -*- coding: utf-8 -*- 

from __future__ import division
import collections
from collections import OrderedDict
import itertools
import os
import random
from math import radians, cos, sin, asin, sqrt, isnan, exp, isnan
import numpy as np
import pylab as pl
from sklearn import mixture
import dataset    
import codecs   
import datetime
import time
from operator import itemgetter
import config as c
from sqlite_cache import SqliteCache

def haversine(coord1, coord2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    """
    lon1, lat1 = coord1[0], coord1[1]
    lon2, lat2 = coord2[0], coord2[1]
    
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 

    # 6367 km is the radius of the Earth
    km = 6367 * c
    return km 

def timing(f):
    def wrap(*args):
        time1 = time.time()
        ret = f(*args)
        time2 = time.time()
        print '%s function took %0.3f ms' % (f.func_name, (time2-time1)*1000.0)
        return ret
    return wrap

class tweetLoc:
    def __init__(self, db=c.LOCATIONDB, dbtweets=c.LOCATIONDB):
        self.db = dataset.connect(db)
        utf8 = self.db.query("set names 'utf8'")
        self.cache = SqliteCache("cache")
        
        self.words = []
    
    def cleanData(self, inputText):
        """
        Tar bort förbjudna tecken och gör allt till lowercase.
        """
        toFile = inputText
        toFile = toFile.lower()     
        forbiddenPath = os.path.dirname(os.path.realpath(__file__)) + os.path.sep + "forbidden.txt"
        for deletePlz in (codecs.open(forbiddenPath, "r", "utf-8").read()).split():
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

    def commonWords(self, threshold=5):
        """
        Returnerar ord vanligare än tröskelvärdet threshold i databasen tweets
        """
        result = self.db.query("SELECT * FROM tweets")
        
        for row in result:
            self.words.extend(row['tweet'].split()) # sparar alla ord i en lista
   
        counter = dict(collections.Counter(self.words).most_common())
        theCommonWords = []
        
        # Sparar alla ord över tröskelvärdet 
        for key, value in counter.iteritems():
            if value >= threshold:
                theCommonWords.append(key)

        return theCommonWords

    def getCoordinatesFor(self, word):
        """
        Letar rätt på alla koordinater från träningdatan som hör till ett ord.
        Ex. "Stockholm" -> [18.23, 59.43], [18.23, 59.23], [18.543, 59.345]
        Dessa hämtas från databasen. 
        """
        outputCoordinates = []
        
        # Hämta koordinater som har ordet i tweeten eller i metadatan
        # Metadata är användarens självspecifierade ort ex. "svettiga svedala" 
        # Hämta bara de som är flaggade som used. Dvs ett snapshot.
        
        q = "SELECT * FROM tweets WHERE MATCH(tweet, metadata) AGAINST('{}') and used = 1".format(word)
        result = self.db.query(q)

        for row in result:
            outputCoordinates.append([row['lon'], row['lat']])

        return outputCoordinates
                               
    def createGMMs(self, words):
        """
        Skapar sklearn-objekt för alla inskickade ord och returnerar alla
        ord som framgångsrikt gick att skapa modell på.
        Stoppar även in alla GMMer i en databas som sedan predict läser ifrån
        """
        if not words:
            print "The database did not contain any tweets that haven't already been compiled."
            return None
            
        print "Compiling GMMs..."
        
        # Flagga snapshotet som ska användas
        result = self.db.query("UPDATE tweets set used = 1")
            
        wordsWithModelAccepted = []
        # Skapar en GMM för alla ord
        for i, word in enumerate(words):
            #print word
            try:                  
                coordinateData = self.getCoordinatesFor(word)
                #print coordinateData
                if len(coordinateData) > 3:
                    print str(i) + "/" + str(len(words)) + " " + word
    
                    myGMM = mixture.GMM(n_components=3, covariance_type='tied')
                    myGMM.fit(np.asarray(coordinateData)) # sklearn wants nparray
                    
                    for coordinate in myGMM.means_: # en GMM tar fram 3 toppar
                        # Empiriskt satt score
                        scoring = np.exp(-100 / myGMM.score([coordinate]))[0]   
                        
                        # In met i databasen         
                        self.db['GMMs'].insert(dict(word=word, 
                                                    lon=coordinate[0], 
                                                    lat=coordinate[1], 
                                                    scoring=scoring,
                                                    date=datetime.date.today(),
                                                    n_coordinates=len(coordinateData)))
                    del myGMM 
                    wordsWithModelAccepted.append(word)     
            except:
                """
                Ordet kunde inte skapas en GMM på
                """

        # Kasta gamla använda tweets
        result = self.db.query("DELETE from tweets WHERE used = 1")
        
        return wordsWithModelAccepted

    def weightedMean(self, coordinates, scores):
        """ 
        Viktat medelvärde
        Input: koordinater och deras vikt 
        Output: koordinat och dess säkerhet
        """
        if len(coordinates) > 0:
            """"
            numberOfCoordinates, nominator, denominator = 0, 0, 0
            
            for score, coordinate in zip(scores, coordinates):
                numberOfCoordinates += 1
                nominator += float(score) * np.array([coordinate[0], coordinate[1]])
                denominator += float(score)           
                 
            if denominator == 0.0:
                weightedMean = [0.0, 0.0]
            else:
                weightedMean = nominator / denominator
                weightedMean = weightedMean.tolist()
            
            score = denominator / numberOfCoordinates # avg score
                
            return weightedMean, score 
            """
            if np.sum(scores) > 0:
                print "coord", coordinates
                print "scores", scores
                print "sum", np.sum(scores)
                print (np.multiply(coordinates, scores) / np.sum(scores)), np.sum(scores)/len(coordinates)
            
        else:
            return [0.0, 0.0], 0.0

    def predict(self, text, threshold=float(1e40)):
        """ 
        Förutsäger en koordinat för en bunte text
        Input: text
        Output: koordinat (lon, lat) och "platsighet" (hur säker modellen är),
                de top 20 mest platsiga orden samt procent out of vocabulary
        """      
        if not threshold:
            threshold = 1e40
        
        words = self.cleanData(text).split() # tar bort en massa snusk och tokeniserar                          
        acceptedWords, OOVcount, wordFreqs = [], 0, []
        coordinates = np.array([])
        scores = np.array([])
 
        # Hämta alla unika datum (batchar) där GMMer satts in i databasen
        batches, wordFreqs = [], []
        
        if not self.cache.get("batches"):
            for row in self.db.query("SELECT DISTINCT date FROM GMMs"):
                batches.append(row['date'])
            self.cache.set("batches", batches, timeout=60*60) # cache for 1 hours    
        else:
            batches = self.cache.get("batches")
        
        for word in words:
            batchscores, batchcoordinates = np.array([]), np.array([])
            wordFreq, freqInBatch = 0, 0
            
            for date in batches:
                result = self.db.query("SELECT * FROM GMMs " 
                                       "WHERE word = '" + word + "' "
                                       "AND date = '" + date + "'")
                                       
                subscores, subcoordinates = np.array([]), np.array([])
                for row in result:
                    subscores = np.append(subscores, [row['scoring']])
                    latlon = np.asarray([row['lat'], row['lon']])
                    subcoordinates = np.concatenate((subcoordinates, latlon)) 
                    
                    
                    freqInBatch = row['n_coordinates']
                    if not freqInBatch:
                        freqInBatch = 0
                
                print "subcoord", subcoordinates
                coordinate, score = self.weightedMean(subcoordinates, subscores)
                np.append(batchscores, score)
                np.append(batchcoordinates, coordinate)
                wordFreq += freqInBatch
            
            # Vikta samman batcharna. TODO: fallande vikt efter datum
            coordinate, score = self.weightedMean(batchcoordinates, batchscores)    
                
            if score > threshold:
                np.append(coordinates, coordinate)
                np.append(scores, score)
                acceptedWords.append(word)
                wordFreqs.append(wordFreq)
        
            # Räkna ord som är out of vocabulary
            if score == 0.0:
                OOVcount += 1 
                
        #print acceptedWords, wordFreqs
                 
        # Vikta samman alla ord efter deras "platsighet"
        coordinate, score = self.weightedMean(coordinates, scores)
  
        wordsAndScores = zip(acceptedWords, scores, wordFreqs)
        # Sortera
        sortedByScore = sorted(wordsAndScores, key=itemgetter(1), reverse=True)
        
        # Skapa dict med platsighet för top 50
        mostUsefullWords = OrderedDict((word, score) for word, score, wordFreq in 
                                        sortedByScore[0:50]) 
        # Skapa dict med koordinatfrekvens för top 50                                
        mentions = OrderedDict((word, int(wordFreq)) for word, score, wordFreq in 
                                sortedByScore[0:50]) 
        
        if len(words) == 0:
            outOfVocabulary = 0                                
        else:
            outOfVocabulary = (float(OOVcount) / float(len(words)))
                                        
        return coordinate, score, mostUsefullWords, outOfVocabulary, mentions


if __name__ == "__main__":

    model = tweetLoc()
    print model.predict("Helsingborg (1912–1971 stavat Hälsingborg) är centralort i Helsingborgs kommun och ligger i Skåne län. Den är med över 91 000 invånare befolkningsmässigt Sveriges åttonde största tätort[4] och ingår i Öresundsregionen. Helsingborg ligger vid Öresunds smalaste del. Endast fyra kilometer skiljer Helsingborg från Helsingör i Danmark. Stadens geografi domineras av den branta sluttningen Landborgen. Den löper längs Öresund, något indragen från kusten. Mellan strandterrassen och landborgsterrassen finns ett antal raviner som bildats under den senaste istiden. I centrum är arkitekturen en tätbyggd stenstad, med monumentala och storstadsmässiga hus mot paradgatorna Drottninggatan och Järnvägsgatan, samt mot Stortorget, Sankt Jörgens plats och Trädgårdsgatan. I gatorna bakom denna bebyggelse är arkitekturen mer småskalig och intim. Helsingborgs historia sträcker sig tillbaka till vikingatiden. Den viktiga plats där Öresund är som smalast har gett staden en strategisk position under lång tid. På medeltiden var staden och dess slott ett av Nordens mäktigaste fästen och därmed inblandat i mycket av den tidens maktspel. Under århundradena har Helsingborg varit platsen för flera politiska konflikter och strider. De många krigen mellan Sverige och Danmark gick hårt åt staden och dess bebyggelse. Men sedan 1700-talet har staden levt i fred. På 1800-talet lyckades Helsingborg återhämta sig ordentligt. Helsingborg blev en av Sveriges snabbast växande städer som en viktig hamn- och industristad. Industrin i Helsingborg domineras inte av några stora privata företag utan består av flera mindre. Den största privata arbetsgivaren är Ikea, som har sitt svenska huvudkontor i staden. Andra viktiga företag sysslar med handel och kommunikationer, samt livsmedel, kemi och läkemedelsteknik. Stadens goda läge gör att det finns flera åkeriföretag och distributionscentraler. Hamnen är även Sveriges näst största containerhamn efter Göteborg och färjetrafiken är omfattande. Två rederier har färjetrafik över Öresund med avgångar dygnet runt. Smeknamn: Sundets pärla alternativt Pärlan vid Sundet. Slogan: Staden för dig som vill något".decode("utf-8"))

