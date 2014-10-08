import requests
from bs4 import BeautifulSoup
from pprint import pprint
from urlparse import urljoin
from thready import threaded
import dataset
from cashhtml import * # caching functions


import StringIO
import socket
import urllib
import socks    # SocksiPy module
import stem.process
from stem.util import term
from stem import Signal
from stem.control import Controller



BASE_URL = 'http://newyork.craigslist.org/'
db = dataset.connect('sqlite:///missed_connections.db')


def scrapeMissedConnections():
    """ Scrape all the missed connections from a list """

    response = requests.get(BASE_URL + "mis/")
    soup = BeautifulSoup(response.content)

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





if __name__ == '__main__':
    scrapeMissedConnections()
