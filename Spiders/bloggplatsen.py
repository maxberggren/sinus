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
import time
#from timeout import timeout
import nltk
import re
import pickle



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

class HeadRequest(urllib2.Request):
    def get_method(self):
        return "HEAD"

def passwordProtected(url):
    """ Vi vill slippa de bloggar som är lösenordsskyddade """
    request = HeadRequest(url)
    
    try:
        response = urllib2.urlopen(request)
        #response_headers = response.info()
        #response_headers.dict
    
    except urllib2.HTTPError, e:
        if e.code == 401:
           return True
        else:
           return False
    except:
        return True

def getBlog(url, depth):
    #startYear=date.today().year
    startYear=2010
    
    if not passwordProtected(url):
        text, nextLink, shouldProceed, posts, timestamps = "", None, True, [], []
        
        response = getContent(url)
        soup = BeautifulSoup(response)
            
        # Hämta länkar och dess texter ##################################
        links = soup.select("a")
        linktexts = [link.text.encode('UTF-8').lower() for link in links]
        links = [link.get('href') for link in links]
        linkandlinktexts = zip(linktexts, links)
        #################################################################
    
        # Hämta år från källkoden #######################################
        
        patn = re.compile(r'20[0-1][0-9]') # typiskt år
        years = set(patn.findall(soup.prettify())) # hitta alla
        # före startYear och unika
        years = [int(year) for year in years if int(year) <= startYear] 
        years = sorted(years, reverse=True) # sortera
        #################################################################
           
        
        # Blogspot, metrobloggen, wordpress.com, bloggplatsen ###########
        # Enl /2008/07 ##################################################
        
        #print "Använder mall för blogspot, metrobloggen och wordpress"
        counter, content = 0, ""
    
        for i in years:
            for month in range(12,0,-1):
            
                # Fixa att månader oftast inleds med nolla
                if month < 10:
                    month = "0" + str(month)
                
                # Bygg länk
                nextLink = url + "/" + str(i) + "/" + str(month) + "/"
                
                counter += 1
                content = getContent(nextLink)
                soup = BeautifulSoup(content)
                post = getAllText(soup)
                text = text + "\n\n" + post
                posts.extend([post])
                timestamps.extend([datetime(i, int(month),1, 12,0,0)])
                #print "hamtar: " + nextLink
                    
                if counter > depth:
                    break
            if counter > depth:
                break
    
        #################################################################
    
        return text, posts, timestamps
    else:
        print 'Bloggen är lösenordsskyddad'
        return None, None, None

def getAllText(soup):
    """ Hämta all text NLTK kan hitta som inte är html """
    
    text = nltk.clean_html(soup.prettify())
    # Vi fimpar alla rader som är för korta
    text = "\n\n".join([line for line in text.split("\n") if len(line) > 40])
    
    if len(text) < 300: # för lite data är ofta = skräp
        return ""
    
    return text

def delDupes(posts, timestamps):
    if not posts or not timestamps:
        return None, None
        
    uniquePosts, uniqueTimestamps = [], []

    for post, timestamp in zip(posts, timestamps):
        if not post in uniquePosts:
            uniquePosts.append(post)
            uniqueTimestamps.append(timestamp)
            
    return uniquePosts, uniqueTimestamps 

def getPlaces():
    startpoint = "http://www.bloggplatsen.se/bloggar/lan-ort/blekinge-lan/"
    response = getContent(startpoint)
    soup = BeautifulSoup(response)
    
    selects = soup.select("select")[0].select("option")
    selects = [select['value'] for select in selects]
    
    counties = soup.select("select")[0].select("option")
    counties = [county.text.split(" (")[0][1:] for county in counties]
    
    return selects, counties
 
def getMunicipalitys(url):
    response = getContent(url)
    soup = BeautifulSoup(response)
    
    selects = soup.select("select")[1].select("option")[1:]
    municipalitys = [select.text.split(" (")[0][1:] for select in selects]
    selects = [select['value'] for select in selects]
    
    return selects, municipalitys
 
def howManyPages(url):
    response = getContent(url + "sida-99999999/")
    soup = BeautifulSoup(response)
    
    urls = soup.select("#sidlankar .sidlank")
    urls = [int(url.text) for url in urls]
    
    try:
        return max(urls)
    except:
        return 0

def getBlogUrls(url):
    response = getContent(url)
    soup = BeautifulSoup(response)
    
    urls = soup.select(".rubriklank")
    urls = [url['href'] for url in urls]
    
    return urls

def getUser(usrid, depth=120):
    
    try:
        url = "http://www.bloggportalen.se/BlogPortal/view/BlogDetails?id=" + str(usrid)
    
        response = getContent(url)
        soup = BeautifulSoup(response)
    
        # Hämta länk och fixa lite vanliga fel ##########################
        link = soup.select("h3 a")[0].get('href') # links
        if "BlogPortal" in link:
            
            link = soup.select("h3 a")[1].get('href').strip()
            link = link.replace(",", ".")
            link = link.replace("http//", "http://")
            link = link.replace("http:///", "http://").replace("http://http://", "http://")
            if link[0:3] == "www.":
                link = "http://" + link
        #################################################################
    
        # Hämta presentationstext #######################################
        presentation = soup.select(".presentation")[0].text.split("\n")
        ort = None
        
        for i, pres in enumerate(presentation):
            if pres[0:3] == "Ort":
                ort = presentation[i+1].replace("\t","").replace("\n","")
                break
        #################################################################
        
        if ort:
            # Har bloggen redan laddats ner?
            exists = db['blogs'].find_one(url=link)
            if not exists:
                text, posts, timestamps = getBlog(link, depth)
                # Mindre än 1000 tecken är förmodligen ingen bra blogg
                if len(text) > 1000:
                    db['blogs'].insert(dict(url=link, presentation=presentation[2], ort=ort))
                    justposted = db['blogs'].find_one(url=link)
                    
                    posts, timestamps = delDupes(posts, timestamps)
                    
                    for i, post in enumerate(posts):
                        if len(post) > 300:
                            db['posts'].insert(dict(blog_id=justposted['id'], 
                                                    text=post, 
                                                    date=timestamps[i]))
                        
                    print "Id: " + str(usrid) + " " + link + " " + ort + " #### laddade ner " + str(len(text)) + " tecken"
            else:
                    #print link + " fanns redan i databasen. Hoppar over."
                    pass
        else:
            #print "Ingen ort fanns hos " + link + " # " + url
            pass
            
    except KeyboardInterrupt:
        sys.exit()
    except IOError:
        #print "Kunde inte hämta blogg. Länken är förmodligen nere eller lösenordsskyddad. # " + url
        pass
    except:
        #print "http://www.bloggportalen.se/BlogPortal/view/BlogDetails?id=" + str(usrid) + " gav felet: ", sys.exc_info()[0]
        pass


### ----------------------------------------------------------------


if __name__ == '__main__':
    BASE_URL = 'http://www.bloggplatsen.se/'
    db = dataset.connect('sqlite:///bloggplatsen.db')
    
    """
    #scrapeWithTOR()

    data = []
    urls, counties = getPlaces()

    
    for url, county in zip(urls, counties):
        municipalityUrls, municipalitys = getMunicipalitys(url)
        
        for municipalityUrl, municipality in zip(municipalityUrls, municipalitys):
            
            nrPages = howManyPages(municipalityUrl)
            print county, municipality
            
            allBlogUrls = []
            for i in range(1,nrPages+1):
                try:
                    pageToGetBlogsFrom = municipalityUrl + "sida-"+str(i)+"/"
                
                    allBlogUrls.extend(getBlogUrls(pageToGetBlogsFrom))
                except:
                    pass
                
            data.append([county, municipality, allBlogUrls])
            
    
    pickle.dump(data, open("data.p", "wb"))
    print "Dattan laddaddd!"
    """
    
    print "Laddar blogurls från pickle"
    data = pickle.load(open("data.p", "rb"))
    
    i = 0
    for row in data:
        county = row[0]
        municipality = row[1]
        urls = row[2]
        
        for url in urls:
            i += 1
            if i > 1541:
                print url, i, 
                text, posts, timestamps = getBlog(url, 120)
                #print posts, timestamps

                #posts, timestamps = delDupes(posts, timestamps)
                
                if not posts or not timestamps:
                    print "Hoppar över bloggen, pga förmodligen inget pre 2010." 
                    continue
                
                if len(text) > 3000:
                    db['blogs'].insert(dict(url=url, county=county, municipality=municipality))
                    justpostedId = db['blogs'].find_one(url=url)['id']
                    
                    for post, timestamp in zip(posts, timestamps):
                        if len(post) > 300:
                            db['posts'].insert(dict(blog_id=justpostedId, 
                                                    text=post, 
                                                    date=timestamp))
                    print "Sparar " + str(len(text)) + " tecken"
                    
                else: # To few characters to be bothered
                   print "Hoppar över bloggen, för få tecken."            

                        
                        
                        
                    
                    
                