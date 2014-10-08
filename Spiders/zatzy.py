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

def getPageUrls(url):
    response = getContent(url)
    soup = BeautifulSoup(response)
    try:
        lasturl = soup.select("div#pagination_bottom form span.first_last a")[0].get("href")
        lasturl = lasturl.split("&")[0]
        linkbase = lasturl.split("/page")[0]
        lastpage = int(lasturl.split("/page")[1])
        pageUrls = ["http://www.zatzy.com/forum/" + linkbase + "/page" + str(pageId) for pageId in range(1,lastpage+1)]
        return pageUrls
    except:
        return [url] # only return first url if no pages are found
    
def getThread(url):
    pageUrls = getPageUrls(url)
    
    if len(pageUrls) > 0:
        dates, users, citys, posts = [], [], [], []
        
        for url in pageUrls: # get every page of thread
            newdates, newusers, newcitys, newposts = getData(url.encode("utf-8"))
            dates.extend(newdates)
            users.extend(newusers)
            citys.extend(newcitys)
            posts.extend(newposts)
            
        saveData(dates, users, citys, posts)
        print "Hittade " + str(len(posts)) + " poster"

def getData(url):
    response = getContent(url)
    soup = BeautifulSoup(response)   

    # get posts
    for div in soup.findAll('div', 'bbcode_quote'):
        div.extract()
    posts = soup.select("blockquote.postcontent")
    posts = [post.text.strip() for post in posts]
    
    
    # get dates 
    today = datetime.date.today()
    yesterday = datetime.date.fromordinal(datetime.date.today().toordinal()-1)

    dates = soup.select("span.postdate")
    dates = [date.text.replace(",","").strip() for date in dates]
    dates = [date.replace(u"Idag", unicode(today)) for date in dates]
    dates = [date.replace(u"Igår", unicode(yesterday)) for date in dates]
    dates = [date.replace(u"\xa0", " ") for date in dates]
    
    dates = dates[0:len(posts)]
    dates = [parser.parse(date) for date in dates]

    # get users
    users = soup.select("a.username strong")
    users = [user.text for user in users]

    # get city
    citys = soup.select("dl.userinfo_extra")
    citys = [city.text.split("\n")[3].replace("Ort ","") for city in citys]
    
    #print "hittade " + str(len(posts)) + " poster"
    return dates, users, citys, posts

def saveData(dates, users, citys, posts):

    for date, user, city, post in zip(dates, users, citys, posts):

        foundInDB = db['sources'].find_one(username=user)
        
        # if user not in db, create him
        if not foundInDB:
            db['sources'].upsert(dict(username=user,city=city), ['username'])
            foundInDB = db['sources'].find_one(username=user)
            
        userId = foundInDB['id']
        
        # insert the posts
        db['posts'].upsert(dict(source_id=userId,
                                text=post,
                                date=date),
                                ['text'])

### ----------------------------------------------------------------


if __name__ == '__main__':
    BASE_URL = 'http://www.zatzy.com/'
    db = dataset.connect('sqlite:///zatzy.db')
    
    #print getPageUrls("http://www.zatzy.com/forum/showthread.php?&p=1550312")
    #print getData("http://www.zatzy.com/forum/showthread.php?154095-Måste-spolare-till-rutan-fungera-för-besiktning/page1")
    
    ids = reversed(range(765227)) # 
    urls = ["http://www.zatzy.com/forum/showthread.php?&p=" + str(i) for i in ids]

    for i, url in enumerate(urls):
        print url
        getThread(url)

