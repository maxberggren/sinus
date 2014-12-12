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
#import pylab as pl
from sklearn import mixture
import dataset    
import codecs   
import datetime
import time
from operator import itemgetter
import config as c
from sqlite_cache import SqliteCache
import re
from collections import Counter
from sets import Set
import string
import geocode 
from geocode import latlon

from mpl_toolkits.basemap import Basemap, cm, maskoceans
import matplotlib.cm as cm
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.colors import LogNorm
from matplotlib.ticker import LogFormatter
from mpl_toolkits.axes_grid1 import make_axes_locatable
import matplotlib.pyplot as plt
import random


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
    def __init__(self, db=c.LOCATIONDB, dbtweets=c.LOCATIONDB, regexpes=None):
        self.db = dataset.connect(db)
        utf8 = self.db.query("set names 'utf8'")
        self.cache = SqliteCache("cache")
        self.words = []
        self.patterns = []

        # Add all Swedish villages/citys to a set
        self.towns = Set()
        f = codecs.open("orter.txt", encoding="utf-8")
        for line in f:
            self.towns.add(line.lower().strip())
        
        if regexpes:
            for regexp in regexpes:
                pattern = regexp.strip()
                p = re.compile(pattern)
                self.patterns.append(p)
        else:
            patterns = codecs.open("ortgrammatik_analytisk6.txt", encoding="utf-8")
            for pattern in patterns:
                pattern = " " + pattern.strip() + " "
                p = re.compile(pattern)
                self.patterns.append(p)
    
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
            try:                  
                coordinateData = self.getCoordinatesFor(word)
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
        
        # If only one coordinates is inputed, return that.
        if len(coordinates) == 1:
            return coordinates[0], scores[0]
        
        if len(coordinates) > 0:
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
            
            score = denominator / float(numberOfCoordinates) # avg score
                
            return weightedMean, score 
            
            """
            # Vektoriserat alternat
            
            if np.sum(scores) > 0:
                nominator = np.sum(np.multiply(coordinates.T, scores).T, axis=0)
                denominator = np.sum(scores)
                score = float(np.sum(scores))/float(len(coordinates))

                return nominator/denominator, score
            else:
                return [0.0, 0.0], 0.0 
            """
            
        else:
            return [0.0, 0.0], 0.0

    def predict(self, text, threshold=float(1e40), mergeSubGMMs=True):
        """ 
        Förutsäger en koordinat för en bunte text
        Input: text
        Output: koordinat (lon, lat) och "platsighet" (hur säker modellen är),
                de top 20 mest platsiga orden samt procent out of vocabulary
        """  
           
        if not threshold:
            threshold = 1e40
        
        self.db.query("set names 'utf8'")
        words = self.cleanData(text).split() # tar bort en massa snusk och tokeniserar 
        #words = [word.encode('utf-8') for word in words]                         
        coordinates, scores, acceptedWords, OOVcount, wordFreqs = [], [], [], 0, []
 
        # Hämta alla unika datum (batchar) där GMMer satts in i databasen
        batches, wordFreqs = [], []
        
        if not self.cache.get("batches"):
            for row in self.db.query("SELECT DISTINCT date FROM GMMs"):
                batches.append(row['date'])
            self.cache.set("batches", batches, timeout=60*60) # cache for 1 hours    
        else:
            batches = self.cache.get("batches")
        
        print len(words)
        for word in words:
            batchscores, batchcoordinates = [], []
            wordFreq, freqInBatch = 0, 0
            
            for date in batches:
                result = self.db.query("SELECT * FROM GMMs " 
                                       "WHERE word = '" + word + "' "
                                       "AND date = '" + date + "' "
                                       "AND n_coordinates > 100")                   
                subscores, subcoordinates = [], []
                for row in result:
                    subscores.append(row['scoring'])
                    subcoordinates.append([row['lat'], row['lon']])
                    freqInBatch = row['n_coordinates']
                    if not freqInBatch:
                        freqInBatch = 0
                
                if mergeSubGMMs:
                    # Run weighted mean in the three GMMs
                    coordinate, score = self.weightedMean(subcoordinates, subscores)
                    batchscores.append(score)
                    batchcoordinates.append(coordinate)
                else:
                    # Treat the GMMs as if they where seperate words
                    batchscores.extend(subscores)
                    batchcoordinates.extend(subcoordinates)
                
                wordFreq += freqInBatch
            
            # Vikta samman batcharna. TODO: fallande vikt efter datum
            coordinate, score = self.weightedMean(batchcoordinates, batchscores)   
             
            if float(score) > float(threshold):
                coordinates.append(coordinate)
                scores.append(score)
                acceptedWords.append(word)
                wordFreqs.append(wordFreq)
        
            # Räkna ord som är out of vocabulary
            if score == 0.0:
                OOVcount += 1 
        
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
        

    def lookup(self, word):
        """ Lookup placeness score in DB """  
           
        self.db.query("set names 'utf8'")
        score = 0
        
        try:
            result = self.db.query("SELECT * FROM GMMs " 
                                   "WHERE word = '" + word.encode('utf-8') + "' "
                                   "ORDER BY scoring DESC")                   
            for row in result:
                score = row['scoring']
                break
        except:
            pass
                    
        return score


    def findBestGrammar(self, text):
        """ 
        Berättar vilka regexpar som är bäst
        Input: text
        Output: list of mean grammars for the regexpes
        """
        
        c = Counter()
        text = text.lower()
        patternMeans = []
        for pattern in self.patterns:
            threshold = 1e20
            found = re.findall(pattern, text)
            patternScores = []
            for word in found:
                patternScores.append(self.lookup(word))
            
            patternScores = np.array(patternScores)
            
            if len(patternScores) > 0:
                overThres = float(len(patternScores[patternScores > threshold]))/float(len(patternScores))
                patternMeans.append(overThres)
            else:
                patternMeans.append(0)
        
        return np.nan_to_num(patternMeans).tolist()


    def predictByVote1(self, text, threshold=float(1e40)):
        """ 
        Förutsäger en koordinat för en bunte text
        Implementatation av röstningsförfarandet
        Input: text, tröskelvärde för platsighet
        Output: koordinat (lon, lat) och "platsighet" (hur säker modellen är),
                de top 20 mest platsiga orden samt procent out of vocabulary
        """  
           
        if not threshold:
            threshold = 1e40
        
        self.db.query("set names 'utf8'")
        words = self.cleanData(text).split() # Sanitize and tokenize 
        coordinates, scores, acceptedWords, OOVcount, wordFreqs = [], [], [], 0, []
 
        ### Get uniqe dates for batches
        batches, wordFreqs = [], []
        
        if not self.cache.get("batches"):
            for row in self.db.query("SELECT DISTINCT date FROM GMMs"):
                batches.append(row['date'])
            self.cache.set("batches", batches, timeout=60*60) # Cache for 1 hours    
        else: # If already in cache, use that
            batches = self.cache.get("batches")
        
        ### Set up grid
        xyRatio = 1.8
        xBins = 20
        lon_bins = np.linspace(8, 26, xBins)
        lat_bins = np.linspace(54.5, 69.5, xBins*xyRatio)
        theGrid = np.zeros((len(lat_bins),len(lon_bins)))

        def addToGrid(theGrid, add, lat, lon, lat_bins, lon_bins):
            """ Add something to the correct bin in the grid """
            
            lat_idx = np.abs(lat_bins-lat).argmin()
            lon_idx = np.abs(lon_bins-lon).argmin()
            theGrid[lat_idx,lon_idx] += add

            return theGrid
        
        for word in words:
            batchscores, batchcoordinates = [], []
            wordFreq, freqInBatch = 0, 0
            
            for date in batches:
                result = self.db.query("SELECT * FROM GMMs " 
                                       "WHERE word = '" + word + "' "
                                       "AND date = '" + date + "' "
                                       "AND n_coordinates > 100")                   
                subscores, subcoordinates = [], []
                for row in result:
                    
                    if float(row['scoring']) > float(threshold):
                        subscores.append(row['scoring'])
                        subcoordinates.append([row['lat'], 
                                               row['lon']])
                                               
                        
                        theGrid = addToGrid(theGrid,
                                            add=row['scoring'],
                                            lat=row['lat'],
                                            lon=row['lon'],
                                            lat_bins=lat_bins,
                                            lon_bins=lon_bins)
                    
                    freqInBatch = row['n_coordinates']
                    if not freqInBatch:
                        freqInBatch = 0
                
                wordFreq += freqInBatch
                                        
        topLatInd, topLonInd = np.where(theGrid==theGrid.max())
        score = theGrid[np.where(theGrid==theGrid.max())][0]
        
        if score > 0.0:
            # Get bin coordinate of bin with highest score
            coordinate = [lat_bins[topLatInd[0]], lon_bins[topLonInd[0]]]
        else:
            coordinate = [0.0, 0.0]
            
        ### Generate a figure of the grid
        
        fig = plt.figure(figsize=(3.25,6))
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

        lon_bins_2d, lat_bins_2d = np.meshgrid(lon_bins, 
                                               lat_bins)
        xs, ys = m(lon_bins_2d, lat_bins_2d)
                
        # Colormap transparency
        theCM = cm.get_cmap("Blues")
        theCM._init()
        alphas = np.abs(np.linspace(0, 1.0, theCM.N))
        theCM._lut[:-3,-1] = alphas
        
        p = plt.pcolor(xs, ys, theGrid, 
                               cmap=theCM, 
                               norm=LogNorm(), 
                               vmin=1, 
                               antialiased=True)                    
        # Add colorbar
        divider = make_axes_locatable(plt.gca())
        cax = divider.append_axes("bottom", 
                                  "2%", 
                                  pad="2.5%")
        colorbar = plt.colorbar(p, 
                                cax=cax, 
                                orientation='horizontal')
        
        
        colorbar.set_ticks([0, 1e10, 1e20, 1e30, 1e40, 1e50])            
        #colorbar.set_ticklabels(["0",
        #                         "25 %",
        #                         "50 %", 
        #                         "75 %",
        #                         "100 %"])
        colorbar.ax.tick_params(labelsize=6) 
            
        fig.tight_layout(pad=2.5, w_pad=0.1, h_pad=0.0)  
    
        filename = "thegrid_" + str(random.randrange(0, 99999))
        #print filename
        #plt.savefig("sinusGUIapp/static/maps/" + filename +".png", dpi=100)
        plt.savefig("sinusGUIapp/static/maps/" + filename +".pdf", dpi=100, bbox_inches='tight')   
            
        return coordinate, score, {}, 0, {}



    def predictByGrammar(self, text, threshold=float(1e40)):
        """ 
        Förutsäger en koordinat för en bunte text
        Implementatation av gramatikförfarandet
        Input: text
        Output: koordinat (lon, lat)
        """
        
        lenText = len(text)
        lenWords = int(lenText / 8.3)
        lowerPercent = 0.00008 # Ger frekvens median 3
        lowerBound = int(lenWords*lowerPercent) 
        topBound = int(lenWords/300.0)
        
        if topBound == 0:
            topBound = 999999999999999999999999
            
        print "low ", lowerBound, "top ", topBound

        c = Counter()
        text = text.lower()
        for pattern in self.patterns:
            found = re.findall(pattern, text)
            if found:
                c.update(found)

        wordsInSpan = [t[0] for t in c.most_common() if t[1] > lowerBound and t[1] < topBound]
        print "lenord i spann", len(wordsInSpan)
        text = " ".join(wordsInSpan)
                
        #return self.predict(text, threshold=threshold)
        return text 

    def predictByUnique(self, text, threshold=float(1e40)):
        """ 
        Förutsäger en koordinat för en bunte text
        Tar endast och använder det vanliga på unika ord
        Input: text
        Output: koordinat (lon, lat)
        """
        lenText = len(text)
        lenWords = int(lenText / 8.3)
        lowerPercent = 0.00008 # Ger frekvens median 3
        lowerBound = int(lenWords*lowerPercent) 
        topBound = int(lenWords/300.0)
        
        if topBound == 0:
            topBound = 999999999999999999999999
            
        print "low ", lowerBound, "top ", topBound
        
        words = self.cleanData(text).split()
        c = Counter()
        c.update(words)

        wordsInSpan = [t[0] for t in c.most_common() if t[1] > lowerBound and t[1] < topBound]
        print "lenord i spann", len(wordsInSpan)
        text = " ".join(wordsInSpan)
                
        return self.predict(text, threshold=threshold)


    def predictByTown(self, text, threshold=float(1e40)):
        """ 
        Förutsäger en koordinat för en bunte text
        Använder endast städer för att positionera
        Output: koordinat (lon, lat)
        """
        if not threshold:
            threshold = 1e40
        
        words = self.cleanData(text).split() # tar bort en massa snusk och tokeniserar        
        coordinates, scores, acceptedWords, OOVcount, wordFreqs = [], [], [], 0, []
 
        # if in set
        # latlon(word)
        
        xyRatio = 1.8
        xBins = 20
        lon_bins = np.linspace(8, 26, xBins)
        lat_bins = np.linspace(54.5, 69.5, xBins*xyRatio)
        theGrid = np.zeros((len(lat_bins),len(lon_bins)))

        def addToGrid(theGrid, add, lat, lon, lat_bins, lon_bins):
            """ Add something to the right bin in the grid """
            lat_idx = np.abs(lat_bins-lat).argmin()
            lon_idx = np.abs(lon_bins-lon).argmin()
            
            theGrid[lat_idx,lon_idx] += add

            return theGrid
        
        for word in words:
            if word in self.towns:      
                #print word.encode('utf-8'), 
                try:
                    while True:
                        try:
                            coordinate = latlon(word.encode('utf-8'))
                                                                         
                            theGrid = addToGrid(theGrid,
                                                add=1,
                                                lat=coordinate[0],
                                                lon=coordinate[1],
                                                lat_bins=lat_bins,
                                                lon_bins=lon_bins)
                            break
                        except geocode.QueryLimitError:
                            print "Limit nådd. Väntar 24 h."
                            time.sleep(60*60*24+10)
                            pass 
                except geocode.NoResultError:
                    pass
                                        
        topLatInd, topLonInd = np.where(theGrid==theGrid.max())
        score = theGrid[np.where(theGrid==theGrid.max())][0]
        
        if score > 0.0:
            # Get bin coordinate of bin with highest score
            coordinate = [lat_bins[topLatInd[0]], lon_bins[topLonInd[0]]]
        else:
            coordinate = [0.0, 0.0]
            
        return coordinate, score, {}, 0, {}


        
        
if __name__ == "__main__":

    model = tweetLoc()
    print model.predict("Helsingborg (1912–1971 stavat Hälsingborg) är centralort i Helsingborgs kommun och ligger i Skåne län. Den är med över 91 000 invånare befolkningsmässigt Sveriges åttonde största tätort[4] och ingår i Öresundsregionen. Helsingborg ligger vid Öresunds smalaste del. Endast fyra kilometer skiljer Helsingborg från Helsingör i Danmark. Stadens geografi domineras av den branta sluttningen Landborgen. Den löper längs Öresund, något indragen från kusten. Mellan strandterrassen och landborgsterrassen finns ett antal raviner som bildats under den senaste istiden. I centrum är arkitekturen en tätbyggd stenstad, med monumentala och storstadsmässiga hus mot paradgatorna Drottninggatan och Järnvägsgatan, samt mot Stortorget, Sankt Jörgens plats och Trädgårdsgatan. I gatorna bakom denna bebyggelse är arkitekturen mer småskalig och intim. Helsingborgs historia sträcker sig tillbaka till vikingatiden. Den viktiga plats där Öresund är som smalast har gett staden en strategisk position under lång tid. På medeltiden var staden och dess slott ett av Nordens mäktigaste fästen och därmed inblandat i mycket av den tidens maktspel. Under århundradena har Helsingborg varit platsen för flera politiska konflikter och strider. De många krigen mellan Sverige och Danmark gick hårt åt staden och dess bebyggelse. Men sedan 1700-talet har staden levt i fred. På 1800-talet lyckades Helsingborg återhämta sig ordentligt. Helsingborg blev en av Sveriges snabbast växande städer som en viktig hamn- och industristad. Industrin i Helsingborg domineras inte av några stora privata företag utan består av flera mindre. Den största privata arbetsgivaren är Ikea, som har sitt svenska huvudkontor i staden. Andra viktiga företag sysslar med handel och kommunikationer, samt livsmedel, kemi och läkemedelsteknik. Stadens goda läge gör att det finns flera åkeriföretag och distributionscentraler. Hamnen är även Sveriges näst största containerhamn efter Göteborg och färjetrafiken är omfattande. Två rederier har färjetrafik över Öresund med avgångar dygnet runt. Smeknamn: Sundets pärla alternativt Pärlan vid Sundet. Slogan: Staden för dig som vill något".decode("utf-8"))

