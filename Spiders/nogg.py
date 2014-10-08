#!/usr/bin/env python
# encoding: utf-8
import requests
from bs4 import BeautifulSoup
from pprint import pprint
from urlparse import urljoin
from thready import threaded
import dataset

#import StringIO
import socket
import urllib
import socks    # SocksiPy module
import stem.process
from stem.util import term
#from stem import Signal
#from stem.control import Controller
import os

#import requests
import os
from hashlib import sha1
import dateutil.parser as dparser
import sys
import nltk
from dateutil.parser import *
from datetime import date, datetime


CACHE_DIR = os.path.join(os.path.dirname(__file__), 'cache')


### Cashe and TOR functions -------------------------------------

def urlToFilename(url):
    """ Make a URL into a file name, using SHA1 hashes. """

    # use a sha1 hash to convert the url into a unique filename
    hash_file = sha1(url).hexdigest() + '.html'
    return os.path.join(CACHE_DIR, hash_file)

def storeLocal(url, content):
    """ Save a local copy of the file. """

    # If the cache directory does not exist, make one.
    if not os.path.isdir(CACHE_DIR):
        os.makedirs(CACHE_DIR)

    # Save to disk.
    local_path = urlToFilename(url)
    with open(local_path, 'wb') as f:
        f.write(content)

def loadLocal(url):
    """ Read a local copy of a URL. """
    local_path = urlToFilename(url)
    if not os.path.exists(local_path):
        return None

    with open(local_path, 'rb') as f:
        return f.read()

def getContent(url):
    """ Wrap getWithTOR and return cashed if already downloaded """
    """
    # if you want cashe, here you go
    content = loadLocal(url)
    if content is None:
        response = getWithTOR(url)
        content = response
        storeLocal(url, content)
    return content
    """
    response = getWithTOR(url)
    content = response
    return content

def getWithTOR(url):
    """
    Uses urllib to fetch a site using SocksiPy for Tor over the SOCKS_PORT.
    """

    try:
        return urllib.urlopen(url).read()
    except:
        return "Unable to reach %s" % url


def print_bootstrap_lines(line):
    if "Bootstrapped " in line:
        print term.format(line, term.Color.BLUE)


def scrapeWithTOR(SOCKS_PORT=7010):
    """ Initialize TOR and call scraper functions """

    socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, '127.0.0.1', SOCKS_PORT)
    socket.socket = socks.socksocket

    print term.format("Starting Tor:\n", term.Attr.BOLD)

    try: 
        tor_process = stem.process.launch_tor_with_config(config = {'SocksPort': str(SOCKS_PORT)}, init_msg_handler = print_bootstrap_lines)
        print term.format("\nChecking endpoint:\n", term.Attr.BOLD)
        print getWithTOR("https://www.atagar.com/echo.php")

        print term.format("Scraping - please do not turn me off", term.Attr.BOLD)
        #scraperFunction()
        

    except:
        print term.format("TOR could not be started. Now running 'killall tor'. Please try again.", term.Attr.BOLD)
        os.system("killall tor")

def closeTOR():
    print term.format("Scraping done", term.Attr.BOLD)
    tor_process.kill()
### ----------------------------------------------------------------




### Scraping functions specific for site ---------------------------
### nogg


def getBlog(url, depth):
    startYear=date.today().year
    #startYear=2010
    endYear=startYear-10
    monthsSV = "December November Oktober September Augusti Juli Juni Maj April Mars Februari Januari".lower().split()
    repls = ('januari', 'january'), ('februari', 'february'), ('mars', 'march'), ('maj', 'may'), ('juni', 'june'), ('juli', 'july'), ('augusti', 'august'), ('oktober', 'october')
    monthENnr = {'december':12, 'november':11, 'october':10, 'september': 9, 'august':8, 'july':7, 'june':6, 'may':5, 'april': 4, 'march':3, 'february':2, 'january':1}

    response = getContent(url)
    response = response.replace("display: none;", "").replace("display:none;","")
    #print response
    soup = BeautifulSoup(response)
    
    links = soup.select(".menuLink1")
    linktexts = [link.text.encode('UTF-8').lower().strip().replace("\xc2\xa0", " ") for link in links]
    links = [link.get('href') for link in links]
    linkandlinktexts = zip(linktexts, links)   
    posts = []
    timestamps = []
    text = ""
    #print linktexts
    #for link in linktexts:
    #    print link
    
    # Hämta genom att leta länkar med år och månadsnamn

    #print "Letar efter arkivsidor med länkar innehållandes månadsnamn"
    counter = 0
    for i in range(startYear, endYear, -1):
        for month in monthsSV:
            #try:
            if str(i) + " " + month in linktexts:
                nextLink = BASE_URL + "/" + links[linktexts.index(str(i) + " " + month)]

                #print "hamtar: " + nextLink
                counter += 1

                soup = BeautifulSoup(getContent(nextLink))
                subposts = soup.select(".textBlogg2")
                for subpost in subposts:
                    posts.extend([subpost.text])
                    text = text + "\n\n" + subpost.text

                subtimestamps = soup.select("span.textBlack b")
                for subtimestamp in subtimestamps:
                    
                    subtimestamp = reduce(lambda a, kv: a.replace(*kv), repls, subtimestamp.text.lower()).split()
                    postmonth = int(monthENnr[subtimestamp[1]])
                    postday = int(subtimestamp[0])
                    postyear = int(subtimestamp[2])
                    timestamps.extend([datetime(postyear, postmonth, postday, 12,0,0)])

            if counter > depth:
                break
            #except:
            #    """ whatever """
        if counter > depth:
            break

    return text, posts, timestamps




def getUser(usrid):
    homepageurl = "http://www.nogg.se/startpage.asp?idHomepage=" + str(usrid)
    blogurl = "http://www.nogg.se/blogg.asp?idHomepage=" + str(usrid)
    
    response = getContent(homepageurl)
    soup = BeautifulSoup(response)

    try:
        metadata = soup.select("td.textBlack")[0].text.strip().split("\n")
        citycounty = metadata[-1].strip().split(", ")
        yeargender = metadata[-2].strip().encode('utf-8').split("år och")
        city = citycounty[0]
        county = citycounty[1]
        gender = yeargender[1].strip()
        year = int(yeargender[0])
        
        print gender, year, "år", city 
        
        #presentation = soup.select(".userPresentation")[0].text # presentation
        #blogurl = BASE_URL + soup.select(".userBlogUrl")[0].get('href') # urls
    
        #if not db['blogs'].find_one(username=username): # check if not already in db
        
        if len(city) > 1 and len(county) > 1:
            #print username
            db['blogs'].insert(dict(url=blogurl, city=city, gender=gender, county=county, age=year))
            justposted = db['blogs'].find_one(url=blogurl)
            #print justposted['id']
            
            # här vill jag ha flera poster istället
            text, posts, timestamps = getBlog(blogurl, 19) # gets 20 levels deep of blog data
            #print len(posts), len(timestamps)
            #print zip(timestamps, posts)
            #print posts
            for i, post in enumerate(posts):
                db['posts'].insert(dict(blog_id=justposted['id'], text=post, date=timestamps[i]))
            
        
        
    except:
        """ dunno """
        print sys.exc_info()[0]

### ----------------------------------------------------------------


if __name__ == '__main__':
    BASE_URL = 'http://www.nogg.se'
    db = dataset.connect('sqlite:///nogg.db')
    
    #scrapeWithTOR()

    ids = reversed(range(128244)) # 128253 aerr first
    for usrid in ids:
        #print usrid
        getUser(usrid)
        #break

    #closeTOR()
