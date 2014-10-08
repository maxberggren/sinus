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
from dateutil import parser
import datetime


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
### garaget

def getThread(url):
    nrPages = howManyPages(url) # how many pages are there?
    
    if nrPages > 0:
        dates, users, citys, posts = [], [], [], []
        
        for pageId in range(1, nrPages+1): # get every page of thread
            newdates, newusers, newcitys, newposts = getData(url, pageId)
            dates.extend(newdates)
            users.extend(newusers)
            citys.extend(newcitys)
            posts.extend(newposts)
            
        saveData(dates, users, citys, posts)

def howManyPages(url):
    response = getContent(url)
    soup = BeautifulSoup(response)
    
    try:
        nrPages = int(soup.select(".title_right")[0]
                                  .text
                                  .split(" | ")[0]
                                  .split(" / ")[1])
    except:
        nrPages = 0
    return nrPages

def getData(url, pageId):
    url = url + "&p=" + str(pageId)
    response = getContent(url)
    soup = BeautifulSoup(response)   

    # get posts
    posts = soup.select(".postmsg")
    posts = [post.text for post in posts]
    
    # get dates 
    today = datetime.date.today()
    yesterday = datetime.date.fromordinal(datetime.date.today().toordinal()-1)

    dates = soup.select("div.blockpost div.sideContentWindow .title")
    dates = [date.text for date in dates]
    dates = [date.replace(u"Idag", unicode(today)) for date in dates]
    dates = [date.replace(u"Igår", unicode(yesterday)) for date in dates]
    dates = dates[0:len(posts)]
    dates = [parser.parse(date) for date in dates]

    # get users
    users = soup.select(".cluetip_username")
    users = [user.text for user in users]

    # get city
    citys = soup.select("dl dd")
    citys = [city.text.replace(u"Från: ", "") for city in citys if u"Från: " in city.text]

    return dates, users, citys, posts

def saveData(dates, users, citys, posts):

    for date, user, city, post in zip(dates, users, citys, posts):

        foundInDB = db['blogs'].find_one(username=user)
        
        # if user not in db, create him
        if not foundInDB:
            db['blogs'].upsert(dict(username=user,city=city), ['username'])
            foundInDB = db['blogs'].find_one(username=user)
            
        blogId = foundInDB['id']
        
        # insert the posts
        db['posts'].upsert(dict(blog_id=blogId,
                                text=post,
                                date=date),
                                ['text'])

### ----------------------------------------------------------------


if __name__ == '__main__':
    BASE_URL = 'http://www.garaget.org/'
    db = dataset.connect('sqlite:///garaget.db')
    
    #scrapeWithTOR()
    #getThread(url="http://www.garaget.org/forum/viewtopic.php?id=288368")
    
    ids = reversed(range(213285)) # 294943 senaste 15 juli
    urls = ["http://www.garaget.org/forum/viewtopic.php?id=" + str(i) for i in ids]
    #threaded(urls, getUser, num_threads=10)
    for i, url in enumerate(urls):
        print url
        getThread(url)

    #closeTOR()
