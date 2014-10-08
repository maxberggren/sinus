# -- coding: utf-8 --
import requests
from bs4 import BeautifulSoup
from pprint import pprint
from urlparse import urljoin
from thready import threaded
import dataset
import base64

#import StringIO
import socket
import urllib
import socks    # SocksiPy module
import stem.process
from stem.util import term
from stem import Signal
from stem.control import Controller
import os
import urllib2

#import requests
import sys
import os
from hashlib import sha1
from datetime import date, datetime
import datetime
import time
#from timeout import timeout
import nltk
import re
import pickle
from dateutil.parser import *
from stem import Signal
from stem.control import Controller




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


def changeEndpoint():
    with Controller.from_port(port = 9051) as controller:
        controller.authenticate()
        controller.signal(Signal.NEWNYM)

def print_bootstrap_lines(line):
    if "Bootstrapped " in line:
        print term.format(line, term.Color.BLUE)
"""
def changeIP():
    controller = Controller.from_port(port = 7010)
    controller.authenticate()
    controller.signal(Signal.HUP)
    controller.close()
"""

def scrapeWithTOR(SOCKS_PORT=7010):
    """ Initialize TOR and call scraper functions """

    socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, '127.0.0.1', SOCKS_PORT)
    socket.socket = socks.socksocket

    print term.format("Starting Tor:\n", term.Attr.BOLD)

    try: 
        global tor_process
        tor_process = stem.process.launch_tor_with_config(config = {'SocksPort': str(SOCKS_PORT)}, init_msg_handler = print_bootstrap_lines)
        print term.format("\nChecking endpoint:\n", term.Attr.BOLD)
        print getWithTOR("https://www.atagar.com/echo.php")

        print term.format("Scraping - please do not turn me off", term.Attr.BOLD)
        #scraperFunction()
        

    except:
        print term.format("TOR could not be started. Now running 'killall tor'. Please try again.", term.Attr.BOLD)
        os.system("killall tor")

def closeTOR():
    print term.format("Scraping done. Tor exited.", term.Attr.BOLD)
    tor_process.kill()
### ----------------------------------------------------------------




### Scraping functions specific for site ---------------------------

def getUser(username, userurl):
    
    try:
        url = BASE_URL + userurl
        response = getContent(url)
        soup = BeautifulSoup(response)
        
        city = soup.select(".profileHeadRight table tbody tr td")[1].text
        postlinks = soup.select("li.feedItem.forumPost a")
        postlinks = [BASE_URL + post.get("href") for post in postlinks]
        
        return city, postlinks
    except KeyboardInterrupt:
        pass
    except:
        return None, None
 
def getPosts(postlinks):
    posts = []
    timestamps = []
    
    for link in postlinks:
        try:
            postId = link.split("#")[-1].replace("post","")
            response = getContent(link)
            soup = BeautifulSoup(response) 
            posttext = soup.select("div#edit"+str(postId) + " div.forum_post_body")[0]
            
            for div in posttext.findAll('div', 'bbquote'):
                div.extract()
                
            posttext = posttext.text.strip()
            posts.append(posttext)
            
            timestamp = soup.select("div#edit"+str(postId) + " td")[0].text.strip().replace(",","")
            timestamps.append(timestamp) 
        except:
            pass

    return posts, timestamps

### ----------------------------------------------------------------


if __name__ == '__main__':
    BASE_URL = 'http://www.sweclockers.com/'
    db = dataset.connect('sqlite:///sweclockers.db')
    
    for pagenr in range(160,1681):
        url = "http://www.sweclockers.com/medlemmar?p=" + str(pagenr)
        print u"Hamtar sida: " + url + ", nr#" + str(pagenr)
        
        response = getContent(url)
        soup = BeautifulSoup(response)     
        
        users = soup.select("h4 a")
        for user in users:
            username = user.text
            userurl = user.get('href')
            
            city, postlinks = getUser(username, userurl)
            
            if city:
                posts, timestamps = getPosts(postlinks)
                print username.encode("utf-8"),
                print city.encode("utf-8"),
                print len(posts)
                
                alreadyInDB = db['sources'].find_one(user=username)
                if not alreadyInDB:
                    db['sources'].insert(dict(user=username,   
                                              city=city))
                    alreadyInDB = db['sources'].find_one(user=username)
                 
                for post, timestamp in zip(posts, timestamps):
                    try:
                        db['posts'].insert(dict(source_id=alreadyInDB['id'], 
                                                text=post, 
                                                date=parse(timestamp)))
                        sys.stdout.write('.')
                    except:
                        pass 
                print "\n"
        
        
        
        
        
        
        
        
        