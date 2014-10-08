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
### nattstad

def scrapeBlog(url, depth): # obs hackkkkkkkkk
    allText = ""
    pages = getPages(url)
    pages = pages[(depth+1):] # take the rest
    posts = []
    timestamps = []
    
    for url in pages:
        response = getContent(url)
        repls = ('januari', 'january'), ('februari', 'february'), ('mars', 'march'), ('maj', 'may'), ('juni', 'june'), ('juli', 'july'), ('augusti', 'august'), ('oktober', 'october')
        response = reduce(lambda a, kv: a.replace(*kv), repls, response.lower())
        
        soup = BeautifulSoup(response)
        
        
        try:
            poststext = soup.select(".blogposttext") # get posts text
            poststext = [nltk.clean_html(unicode(post)) for post in poststext]
            postsdatetime = soup.select(".blogpostheaderdate")
            
            postsdatetime = [nltk.clean_html(unicode(post)) for post in postsdatetime]
            postsdatetime = [parse(post, fuzzy=True) for post in postsdatetime]
            
            posts.extend(poststext[0:len(postsdatetime)])
            timestamps.extend(postsdatetime)
        except:
            pass
        #allText = allText + "\n\n" + getAllText(url)
    
    return posts, timestamps

def getAllText(url):
    response = getContent(url)
    soup = BeautifulSoup(response)
    paragraphs = soup.select("p") # get paragraphs
    text = ""
    for p in paragraphs:
        text = text + "\n\n" + p.text
    return text

def getPages(url):
    response = getContent(url)
    soup = BeautifulSoup(response)
    links = soup.select("a") # get links
    links = [link.get('href') for link in links]
    pagenumbers = []
    for link in links:
        try:
            if "/page/" in link:
                pagenumbers.append(link.split("/")[-1])
        except:
            """ dunno """
            
    try: 
        pagenumbers = [int(number) for number in pagenumbers]  
        pagenumbers = range(1, max(pagenumbers)) 
    except:
        pagenumbers = [0]
    
    pages = [url + "/page/" + str(pagenumber) for pagenumber in pagenumbers]
    pages = [page for page in pages if page is not None] # remove None:s

    return pages

def getUser(url):
    response = getContent(url)
    soup = BeautifulSoup(response)

    #try:
    if (soup.select("h1") and 
        soup.select(".userPresentation") and
        soup.select(".userBlogUrl")):
            
        username = soup.select("h1")[0].text # username
        presentation = soup.select(".userPresentation")[0].text # presentation
        blogurl = BASE_URL + soup.select(".userBlogUrl")[0].get('href') # urls
    
        #if not db['blogs'].find_one(username=username): # check if not already in db
    
        if len(username) > 1 and len(presentation) > 2:
            print username.encode('utf-8')
    
            alreadyInDB = db['blogs'].find_one(url=blogurl)
            if not alreadyInDB:
                db['blogs'].insert(dict(url=blogurl, 
                                        username=username, 
                                        presentation=presentation, 
                                        manuellStad=None))
                #db.commit()
                #db.begin()
                alreadyInDB = db['blogs'].find_one(url=blogurl)
            
            posts, timestamps = scrapeBlog(blogurl, 19) # gets after the first 19 pages
            print len(posts)
            #print posts[0].encode('utf-8')
            # handar inte om encoding utan att databsen är stängd
            #print zip(timestamps, posts)
            #print posts
            for i, post in enumerate(posts):
                db['posts'].insert(dict(blog_id=alreadyInDB['id'], 
                                        text=post, 
                                        date=timestamps[i]))
                sys.stdout.write('.')
            #db.commit()
            #db.begin()
    else:
        print "Användaren existerar ej längre / ingen angiven presentation"

    #except IndexError:
    #    print "Användaren existerar ej längre / ingen angiven presentation"
    #except:
    #    """ dunno """
    #    print sys.exc_info()[0]

### ----------------------------------------------------------------


if __name__ == '__main__':
    BASE_URL = 'http://www.nattstad.se'
    db = dataset.connect('sqlite:///nattstad.db')
    #db.begin()
    #scrapeWithTOR()

    ids = reversed(range(741426)) #  989823 aerr first
    urls = ["http://www.nattstad.se/visit_presentation.aspx?id=" + str(i) for i in ids]
    #threaded(urls, getUser, num_threads=10)
    for i, url in enumerate(urls):
        print url
        getUser(url)

    #closeTOR()
