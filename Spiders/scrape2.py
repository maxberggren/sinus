import requests
from bs4 import BeautifulSoup
#from pprint import pprint
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
    content = loadLocal(url)
    if content is None:
        response = getWithTOR(url)
        content = response
        storeLocal(url, content)
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


def startScraping(scraperFunction, SOCKS_PORT=7010):
    """ Initialize TOR and call scraper functions """

    socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, '127.0.0.1', SOCKS_PORT)
    socket.socket = socks.socksocket

    print term.format("Starting Tor:\n", term.Attr.BOLD)

    try: 
        tor_process = stem.process.launch_tor_with_config(config = {'SocksPort': str(SOCKS_PORT)}, init_msg_handler = print_bootstrap_lines)
        print term.format("\nChecking endpoint:\n", term.Attr.BOLD)
        print getWithTOR("https://www.atagar.com/echo.php")

        print term.format("Scraping - please do not turn me off", term.Attr.BOLD)
        scraperFunction()
        print term.format("Scraping done", term.Attr.BOLD)
        tor_process.kill() # goodnight tor, see you next time
    except:
        print term.format("TOR could not be started. Now running 'killall tor'. Please try again.", term.Attr.BOLD)
        os.system("killall tor")

### ----------------------------------------------------------------




### Scraping functions specific for site ---------------------------

BASE_URL = 'http://newyork.craigslist.org/'
db = dataset.connect('sqlite:///missed_connections.db')


def scrapeMissedConnections():
    """ Scrape all the missed connections from a list """

    soup = BeautifulSoup(getContent(BASE_URL + "mis/"))

    missed_connections = soup.find_all('span', {'class':'pl'})

    urls = []
    for missed_connection in missed_connections:

        link = missed_connection.find('a').attrs['href']
        url = urljoin(BASE_URL, link)
        urls.append(url)


    threaded(urls, scrapeMissedConnection, num_threads=10)


def scrapeMissedConnection(url):
    """ Extract information from a missed connections's page. """

    response = getContent(url)
    soup = BeautifulSoup(response)
    

    data = {
        'source_url': url,
        'subject': soup.find('h2', {'class':'postingtitle'}).text.strip(),
        'body': soup.find('section', {'id':'postingbody'}).text.strip(),
        'datetime': soup.find('time').attrs['datetime']
    }

    #db['posts'].upert(dict(body=data['body'], url=data['source_url']))
    #db['posts'].insert(dict(body=data['body'], url=data['source_url']))
    db['posts'].insert(data)

### ----------------------------------------------------------------


if __name__ == '__main__':
    startScraping(scrapeMissedConnections)
