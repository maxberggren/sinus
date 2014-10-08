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
    
    if passwordProtected(url):
        raise IOError('Bloggen är lösenordsskyddad')
        
    text, nextLink, shouldProceed, posts, timestamps = "", None, True, [], []
    
    months = ['december', 'november', 'october', 'september', 
              'august', 'july', 'june', 'may', 'april', 'march', 
              'february', 'january']
              
    monthsSV = ['december', 'november', 'oktober', 'september', 
                'augusti', 'juli', 'juni', 'maj', 'april', 'mars', 
                'februari', 'januari']

    monthSVnr = {'december':12, 'november':11, 'oktober':10, 
                 'september': 9, 'augusti':8, 'juli':7, 'juni':6, 
                 'maj':5, 'april': 4, 'mars':3, 'februari':2, 'januari':1}
                 
    monthENnr = {'december':12, 'november':11, 'october':10, 
                 'september': 9, 'august':8, 'july':7, 'june':6, 'may':5, 
                 'april': 4, 'march':3, 'february':2, 'january':1}
    
    response = getContent(url)
    soup = BeautifulSoup(response) 
        
    # Hämta länkar och dess texter ##################################
    links = soup.select("a")
    linktexts = [link.text.encode('UTF-8').lower() for link in links]
    links = [link.get('href') for link in links]
    # samt dropdownmenyer
    dropdowns = soup.select("option")
    dropdowntexts = [link.text.encode('UTF-8').lower().strip() for link in dropdowns]
    dropdownlinks = [link.get('value') for link in dropdowns]
    linktexts.extend(dropdowntexts)
    links.extend(dropdownlinks)
    
    linkandlinktexts = zip(linktexts, links)
    #print linkandlinktexts  
    #################################################################

    # Hämta år från källkoden #######################################
    
    patn = re.compile(r'20[0-1][0-9]') # typiskt år
    years = set(patn.findall(soup.prettify())) # hitta alla
    # före startYear och unika
    years = [int(year) for year in years if int(year) <= startYear] 
    years = sorted(years, reverse=True) # sortera
    #################################################################

    if len(years) < 2: # Om inga år kunde hittas i källkoden
        return "", [], []
    
    # Blogspot, metrobloggen, wordpress.com #########################
    # Enl /2008/07 ##################################################
    
    if ("blogspot" in url or 
        "metrobloggen" in url or 
        "wordpress" in url) and shouldProceed:
        
        #print "Använder mall för blogspot, metrobloggen och wordpress"
        counter, content = 0, ""
        url = url.replace("blogspot.com", "blogspot.se") # blogspotfix
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

        shouldProceed = False
    #################################################################

    # Blogg.se, webblogg.se #########################################
    # Enligt 2014/june ##############################################
    
    if ("blogg.se" in url or "webblogg.se" in url) and shouldProceed: 
        #print "Mall för blogg.se används"
        counter, content = 0, ""
        for i in years:
            for month in months:                    
                nextLink = url + "/" + str(i) + "/" + month + "/"
                #print "Hamtar: " + nextLink
                counter += 1

                soup = BeautifulSoup(getContent(nextLink))
                post = getAllText(soup)
                text = text + "\n\n" + post
                posts.extend([post])
                timestamps.extend([datetime(i, monthENnr[month],1, 12,0,0)])
                
                if counter > depth:
                    break
            if counter > depth:
                break
                
        shouldProceed = False

    #################################################################


    # Mer generella mallar ##########################################
    # Hämta genom att leta länkar med år och månadsnamn #############
    
    if shouldProceed:
        #print "Letar efter arkivsidor med länkar innehållandes månadsnamn"
        counter = 0
        for i in years:
            for month in monthsSV:
                #try:
                if month + " " + str(i) in linktexts:
                    if "http://" in links[linktexts.index(month + " "+ str(i))]:
                        nextLink = links[linktexts.index(month + " "+ str(i))]
                    else:
                        nextLink = url + links[linktexts.index(month + " "+ str(i))]

                    #print "hamtar: " + nextLink
                    counter += 1

                    soup = BeautifulSoup(getContent(nextLink))
                    post = getAllText(soup)
                    text = text + "\n\n" + post
                    posts.extend([post])
                    timestamps.extend([datetime(i, monthSVnr[month],1, 12,0,0)])

                #if counter > depth:
                #    break
                #except:
                #    pass
            if counter > depth:
                break
                
    if len(text) > 1000:
        shouldProceed = False
    ###################################################################

    # Hämta genom att leta efter typisk arkivsidestruktur enl 2014/03 #
    
    if shouldProceed:
        #print "Inga arkivlänkar hittades, brute force:ar och testar länkar på formatet /2014/03 osv"
        counter = 0
        content = ""
        for i in years:
            for month in range(12,0,-1):
            
                # Fixa att månader oftast inleds med nolla
                if month < 10:
                    month = "0" + str(month)
                
                # Bygg länk
                nextLink = url + "/" + str(i) + "/" + str(month) + "/"
                
                # Om antalet tecken är ungefär samma som vid förra 
                # sidhämtningen är det förmodligen en tom arkivsida 
                # där det inte finns något på den månanden 
                tolerance = 30
                if (len(content) - tolerance) <= len(getContent(nextLink)) <= (len(content) + tolerance):
                    #print "Verkar vara samma som forra sidan"
                    pass
                else:
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

    if len(text) < 1000:
        shouldProceed = True
    ##########################################################################
                
    # Hämta genom att leta efter typisk arkivsidestruktur enl /2014/march ####
    
    if shouldProceed:
        #print "Inga arkivlänkar hittades, brute force:ar och testar länkar på formatet /2014/march osv"
        counter = 0
        content = ""
        for i in years:
            for month in months:  
                nextLink = url + "/" + str(i) + "/" + month + "/"

                tolerance = 30
                if (len(content) - tolerance) <= len(getContent(nextLink)) <= (len(content) + tolerance):
                    #print "Verkar vara samma som forra sidan"
                    pass
                else:
                    #print "hamtar: " + nextLink
                    counter += 1
    
                    soup = BeautifulSoup(getContent(nextLink))
                    post = getAllText(soup)
                    text = text + "\n\n" + post
                    posts.extend([post])
                    timestamps.extend([datetime(i, monthENnr[month],1, 12,0,0)])
                    
                if counter > depth:
                    break
            if counter > depth:
                break

    return text, posts, timestamps

def getAllText(soup):
    """ Hämta all text NLTK kan hitta som inte är html """
    
    text = nltk.clean_html(soup.prettify())
    # Vi fimpar alla rader som är för korta
    text = "\n\n".join([line for line in text.split("\n") if len(line) > 40])
    
    if len(text) < 300: # för lite data är ofta = skräp
        return ""
    
    return text

def delDupes(posts, timestamps):
    uniquePosts, uniqueTimestamps = [], []

    for post, timestamp in zip(posts, timestamps):
        if not post in uniquePosts:
            uniquePosts.append(post)
            uniqueTimestamps.append(timestamp)
            
    return uniquePosts, uniqueTimestamps 

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
    BASE_URL = 'http://www.bloggportalen.se/'
    db = dataset.connect('sqlite:///bloggportalen.db')
    #db.begin()
    
    #scrapeWithTOR()

    #ids = xrange(43,151457) #  151457 är senaste
    ids = range(0, 151457) #  151457 är senaste 2 juli 2014

    #threaded(ids, getUser, num_threads=10)

    #start_time = time.time()
    for usrid in ids:
        print usrid
        getUser(usrid)
    
    #getUser(14043)
    #getUser(545)
    #getUser(352)
    #getBlog("http://juliaskott.wordpress.com/", 120)
    #getUser(33009) # julia skott
    #getUser(314)
    #getUser(219)
    #print time.time() - start_time, "seconds to run excluding TOR startup"
    #closeTOR()

    #print getBlog("http://dedicatedtotraining.blogg.se", 10)    
    #print getBlog("http://alexias.blogg.se", 10)

    #getUser(140975)
    #egetUser(24)
    #getUser("http://www.bloggportalen.se/BlogPortal/view/BlogDetails?id=59062")
    #getUser("http://www.bloggportalen.se/BlogPortal/view/BlogDetails?id=126435")
    #getUser("http://www.bloggportalen.se/BlogPortal/view/BlogDetails?id=128226")
    #getUser("http://www.bloggportalen.se/BlogPortal/view/BlogDetails?id=90937")
    #getUser("http://www.bloggportalen.se/BlogPortal/view/BlogDetails?id=132300")
    #getUser("http://www.bloggportalen.se/BlogPortal/view/BlogDetails?id=76059")
    #getUser("http://www.bloggportalen.se/BlogPortal/view/BlogDetails?id=98693")
    #getUser("http://www.bloggportalen.se/BlogPortal/view/BlogDetails?id=98563")
    #getUser("http://www.bloggportalen.se/BlogPortal/view/BlogDetails?id=98373")