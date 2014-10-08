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
import re

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
        lastid = int(soup.select("td.vbmenu_control")[2].text.split(" av ")[1])
        urls = [url + "&page=" + str(page) for page in range(1,lastid+1)]
        return urls
    except:
        return [url] # only return first url if no pages are found
    
def getThread(url):
    pageUrls = getPageUrls(url)
    
    if len(pageUrls) > 0:
        dates, users, citys, posts = [], [], [], []
        
        for url in pageUrls: # get every page of thread
            newdates, newusers, newposts = getData(url.encode("utf-8"))
            dates.extend(newdates)
            users.extend(newusers)
            posts.extend(newposts)
            
        print "Hittade " + str(len(posts)) + " poster.",
        count = saveData(dates, users, posts)
        print "Varav " + str(count) + " poster var lokaliserade."

def getUser(url):
    response = getContent(url)
    soup = BeautifulSoup(response)   

    try:
        details = soup.select("div.memberdetails")[0].prettify().split("\n")
        details = [detail.strip() for detail in details]
        usernameid = details.index(u'Användarnamn:')
        username = details[usernameid+2]
        cityid = details.index(u'Bor:')
        city = details[cityid+2].replace(" (","")
        
        if username and city:
            db['sources'].insert(dict(username=username, 
                                      city=city))    
        return username, city
    except:
        return None, None

def getData(url):
    response = getContent(url)
    soup = BeautifulSoup(response)   

    # get dates 
    today = datetime.date.today()
    yesterday = datetime.date.fromordinal(datetime.date.today().toordinal()-1)

    dates = soup.prettify().replace(",","").replace(u"Idag", unicode(today)) .replace(u"Igår", unicode(yesterday)).replace(u"\xa0", " ")

    date_reg_exp = re.compile('\d{4}[-/]\d{2}[-/]\d{2} \d{2}\:\d{2}')
    dates = date_reg_exp.findall(dates)
    dates = [parser.parse(date) for date in dates]
    
    # get posts
    for div in soup.findAll('fieldset', 'fieldset'):
        div.extract()
    for div in soup.findAll('div', 'smallfont'):
        div.extract()
    posts = soup.select("td.alt1 div")
    posts = [post.text.strip() for post in posts]
    posts = [post for post in posts if len(post) > 0]
    posts = posts[0:len(dates)]

    # get users
    users = soup.select(".bigusername")
    users = [user.text for user in users]

    #print "hittade " + str(len(posts)) + " poster"
    return dates, users, posts

def saveData(dates, users, posts):

    count = 0
    for date, user, post in zip(dates, users, posts):

        foundInDB = db['sources'].find_one(username=user)
        
        if foundInDB: # only save when a localized user is found
            count += 1
            userId = foundInDB['id']
            
            # insert the posts
            db['posts'].insert(dict(source_id=userId,
                                    text=post,
                                    date=date))
    return count


### ----------------------------------------------------------------


if __name__ == '__main__':
    BASE_URL = 'http://www.fotosidan.se/'
    db = dataset.connect('sqlite:///fotosidan.db')
    
    #print getPageUrls("http://www.zatzy.com/forum/showthread.php?&p=1550312")
    #print getData("http://www.zatzy.com/forum/showthread.php?154095-Måste-spolare-till-rutan-fungera-för-besiktning/page1")
    #print getUser("http://www.fotosidan.se/member/view.htm?ID=211834")
    
    """
    ids = reversed(range(211834)) # 
    urls = ["http://www.fotosidan.se/member/view.htm?ID=" + str(i) for i in ids]

    for i, url in enumerate(urls):
        print url
        print getUser(url)
    """
    #print getThread("http://www.fotosidan.se/forum/showthread.php?t=159481")
    #getThread("http://www.fotosidan.se/forum/showthread.php?t=159481&page=2")
    ids = reversed(range(159481)) # 
    urls = ["http://www.fotosidan.se/forum/showthread.php?p=" + str(i) for i in ids]

    for url in urls:
        print url
        print getThread(url)