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
#from stem import Signal
#from stem.control import Controller
import os
import urllib2

#import requests
import sys
import os
from hashlib import sha1
from datetime import date
import time
#from timeout import timeout
import nltk




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


def scrapeBlog(url, depth):
    allText = ""
    pages = getPages(url)
    pages = pages[0:depth] # only take 11 first

    for url in pages:
        allText = allText + "\n\n" + getAllText(url)
    
    return allText

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

def getBlog(url, depth):
    #startYear=date.today().year
    startYear=2010
    endYear=startYear-10
    
    if passwordProtected(url):
        raise IOError('Bloggen är lösenordsskyddad')
    
    response = getContent(url)
    soup = BeautifulSoup(response)
    
    if len(getAllText(soup)) < 1000:
        raise IOError('Hittade för lite data för att det ska kunna antas vara en aktiv blogg')
    
    text = ""
    months = "january february march april may june july august september october november december".split()
      
    links = soup.select("a")
    linktexts = [link.text.encode('UTF-8') for link in links]
    links = [link.get('href') for link in links]
    linkandlinktexts = zip(linktexts, links)   

    """
    # Hämta genom att leta efter länkar som leder till föregående sida
    for each in range(depth):
        commonNextLinks = ["Nästa", "Äldre inlägg", "« Äldre inlägg", "Older", "← Äldre inlägg", "&rsaquo;"]
        nextlink = [linktext[1] for linktext in linkandlinktexts if linktext[0] in commonNextLinks]
        
        try:
            nextlink = nextlink[0]

            url = nextlink
            soup = BeautifulSoup(getContent(url))
            text = text + "\n\n" + getAllText(soup)
            #print url

        except:
            nextlink = None
            #print "Kunde ej gå djupare än bloggens första sida genom att hitta länkar som tar en bakåt. Testar därför nu att leta efter arkivlänkar."
            break
    """

    # Hämta genom att ta arkivsidor efter deras månad och år
    nextlink = None
    if nextlink == None:
        print "Letar efter arkivsidor med länkar innehållandes månadsnamn"
        counter = 0
        for i in range(startYear, endYear, -1):
            for month in months:

                try:
                    nextlink = url + links[linktexts.index(month + " "+ str(i))]
                    print "hämtar: " + nextLink
                    counter += 1

                    soup = BeautifulSoup(getContent(nextlink))
                    text = text + "\n\n" + getAllText(soup)

                    if counter > depth:
                        break
                except:
                    """ whatever """
            if counter > depth:
                break

    # Hämta genom att leta efter typisk arkivsidestruktur
    
    if nextlink == None:
        print "Inga arkivlänkar hittades, brute force:ar och testar länkar på formatet /2014/march osv"
        counter = 0
        print linkandlinktexts
        print range(startYear, endYear, -1)
        for i in range(startYear, endYear, -1):
            for month in months:
            	if "/" + str(i) + "/" + month + "/" in links or url + "/" + str(i) + "/" + month + "/" in link:
                    
                    nextlink = url + "/" + str(i) + "/" + month + "/"
                    print "hamtar: " + nextlink
                    counter += 1
    
                    soup = BeautifulSoup(getContent(nextlink))
                    text = text + "\n\n" + getAllText(soup)
                if counter > depth:
                    break
            if counter > depth:
                break

    # Hämta genom att leta efter typisk arkivsidestruktur
    
    if nextlink == None:
        print "Inga arkivlänkar hittades, brute force:ar och testar länkar på formatet /2014/03 osv"
        counter = 0
        for i in range(startYear, endYear, -1):
            for month in range(1,13):
                #if "/" + str(i) + "/" + str(month) + "/" in links:
                if month < 10:
                    month = "0" + str(month)
                
                nextlink = url + "/" + str(i) + "/" + str(month) + "/"
                print "hamtar: " + nextlink
                counter += 1

                soup = BeautifulSoup(getContent(nextlink))
                text = text + "\n\n" + getAllText(soup)
                if counter > depth:
                    break
            if counter > depth:
                break
    """
    # Sista försöket är att på på /page/x och se om de hittas
    if nextlink == None:
        for i in range(depth):
            #print url + "/page/" + str(i+1)
            try:
                nextlink = url + "/page/" + str(i+1)
                soup = BeautifulSoup(getContent(url))
                text = text + "\n\n" + getAllText(soup)
            except:
                print "Kunde ej heller hitta /page/x efter urlen"
                nextlink = None
                break
    """

    return text

def getAllText(soup):
    paragraphs = soup.select("p") # get paragraphs
    text = ""
    for p in paragraphs:
        text = text + "\n\n" + p.text
    
    if len(text) < 300: # ibland är antagandet att brödtexten finns i p-taggar felaktig
        #text = soup.get_text()
        text = nltk.clean_html(soup.prettify())
    
    if len(text) < 300: # fortfarande lite data
        return ""
        
    return text

def getUser(url, depth=10):
    
    try:
        response = getContent(url)
        soup = BeautifulSoup(response)
    
        # get link and fix some common url misstakes ####################
        link = soup.select("h3 a")[0].get('href') # links
        if "BlogPortal" in link:
            
            link = soup.select("h3 a")[1].get('href').strip()
            link = link.replace(",", ".")
            link = link.replace("http//", "http://")
            link = link.replace("http:///", "http://").replace("http://http://", "http://")
            if link[0:3] == "www.":
                link = "http://" + link
        #################################################################

        # get presentation text #########################################
        presentation = soup.select(".presentation")[0].text.split("\n")

        for i, pres in enumerate(presentation):
            if pres[0:3] == "Ort":
                ort = presentation[i+1].replace("\t","").replace("\n","")
                break
        #################################################################
            
        text = getBlog(link, depth)
        print link + " " + ort + " #### laddade ner " + str(len(text)) + " tecken"
        #print url
        #print text
        
    except UnboundLocalError:
        print "Användaren har ej specifierat ort. Blogg hämtades ej."
    except IOError:
        print "Kunde inte hämta blogg. Länken är förmodligen nere eller lösenordsskyddad."
        print "url: " + url
    except:
        print "ERROR:", sys.exc_info()[0]
        #print "fel på länk: " + unicode(link)
        #print "presurl: " +  unicode(url)


### ----------------------------------------------------------------


if __name__ == '__main__':
    BASE_URL = 'http://www.bloggportalen.se/'
    db = dataset.connect('sqlite:///bloggportalen.db')
    
    #scrapeWithTOR()

    #ids = reversed(range(140976)) #  150976 är senaste
    #urls = ["http://www.bloggportalen.se/BlogPortal/view/BlogDetails?id=" + str(i) for i in ids]
    #threaded(urls, getUser, num_threads=10)

    #start_time = time.time()
    #for url in urls:
    #    getUser(url)

    #print time.time() - start_time, "seconds to run excluding TOR startup"
    #closeTOR()

    #print getBlog("http://dedicatedtotraining.blogg.se", 10)    
    #print getBlog("http://alexias.blogg.se", 10)

    #getUser("http://www.bloggportalen.se/BlogPortal/view/BlogDetails?id=140975")
    #getUser("http://www.bloggportalen.se/BlogPortal/view/BlogDetails?id=126574")
    getUser("http://www.bloggportalen.se/BlogPortal/view/BlogDetails?id=59062")
    
    getBlog("http://adsdsaadsadsads.blogg.se/", 10)
    #getUser("http://www.bloggportalen.se/BlogPortal/view/BlogDetails?id=126435")
    #getUser("http://www.bloggportalen.se/BlogPortal/view/BlogDetails?id=128226")
    #getUser("http://www.bloggportalen.se/BlogPortal/view/BlogDetails?id=90937")
    #getUser("http://www.bloggportalen.se/BlogPortal/view/BlogDetails?id=132300")
    #getUser("http://www.bloggportalen.se/BlogPortal/view/BlogDetails?id=76059")
    #getUser("http://www.bloggportalen.se/BlogPortal/view/BlogDetails?id=98693")