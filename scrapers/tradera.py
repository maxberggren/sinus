#!/usr/bin/python
# -*- coding: utf-8 -*- 

import pandas as pd
import sqlalchemy as sq
from bs4 import BeautifulSoup, SoupStrainer
import requests
import re
import warnings
import urllib2
import httplib
from socket import error as SocketError
from io import BytesIO
import requests
import binascii

import sys
import os

from progressbar import AnimatedMarker, Bar, BouncingBar, Counter, ETA, \
    FileTransferSpeed, FormatLabel, Percentage, \
    ProgressBar, ReverseBar, RotatingMarker, \
    SimpleProgress, Timer

from grab.spider import Spider, Task
from grab.error import DataNotFound
from pybloom import BloomFilter
import cPickle as pickle
import logging 

import dataset
import datetime
import time
from random import shuffle

catch_errors = (urllib2.HTTPError, 
                urllib2.URLError, 
                httplib.BadStatusLine, 
                httplib.IncompleteRead, 
                httplib.InvalidURL,
                SocketError, 
                UnicodeEncodeError, 
                ValueError)

logging.basicConfig(level=logging.ERROR)

# Set up bloomfilter from file if that exists
global bloom
bloom_cap = 1000000
bloom_filename = 'bloomfilter_tradera.pkl'
if os.path.isfile(bloom_filename):
    with open(bloom_filename, 'r') as f:
        bloom = pickle.load(f) 
else:
    bloom = BloomFilter(capacity=bloom_cap, error_rate=0.001)

mysqldb = dataset.connect("mysql://sinus:5NU4KbP8@locationdb.gavagai.se/sinus2")
mysqldb.query("set names 'utf8'") # Might help
skiplinks = []

class LinkSpider(Spider):
    """  Will crawl a site for all it's urls """

    def __init__(self, url=None, restrict_to=None, skip=None, thread_number=20, network_try_limit=10):
        super(self.__class__, self).__init__(thread_number=thread_number, network_try_limit=network_try_limit)

        self.initial_urls = [url]
        self.base_url = url
        self.urls_found = []
        self.start_time = time.time()
        self.skip = skiplinks
        self.skip += skip

        if not restrict_to:
            self.restrict_to = ""
        else:
            self.restrict_to = restrict_to

    def task_initial(self, grab, task):
        for elem in grab.doc('//a'):
            try:
                url = grab.make_url_absolute(elem.attr('href'))

                if self.restrict_to in url \
                                    and not any(word in url for word in self.skip):

                    if len(url) > 26 + len(self.base_url):
                        self.urls_found += [url]

                    yield Task('lvl1', 
                               url=url)

            except DataNotFound:
                pass

    def task_lvl1(self, grab, task):
        for elem in grab.doc('//a'):
            try:
                url = grab.make_url_absolute(elem.attr('href'))

                if self.restrict_to in url \
                                    and not any(word in url for word in self.skip) \
                                    and url not in bloom:

                    if len(url) > 26 + len(self.base_url):
                        self.urls_found += [url]

                    yield Task('save', 
                               url=url)

            except DataNotFound:
                pass

    def task_save(self, grab, task):
        for elem in grab.doc('//a'):
            try:
                url = grab.make_url_absolute(elem.attr('href'))

                if self.restrict_to in url \
                                    and not any(word in url for word in self.skip) \
                                    and url not in bloom:

                    if len(url) > 26 + len(self.base_url):
                        self.urls_found += [url]

            except DataNotFound:
                pass



class ContentSpider(Spider):
    """  Will crawl a list of urls for it texts """

    def __init__(self, urls=[], thread_number=3, network_try_limit=10, name="", subsections=[]):
        super(self.__class__, self).__init__(thread_number=thread_number, network_try_limit=network_try_limit)

        self.initial_urls = urls
        self.urls_found = []
        self.counter = 0
        self.img_counter = 0
        self.start_time = time.time()
        self.bloom_at_capacity = False

        self.name = name

        self.all_names = []
        self.tot_fem_pronouns = 0
        self.tot_male_pronouns = 0
        self.nordic = 0
        self.international_names = []
        self.nordic_names = []
        self.all_article_texts = ""
        self.progressbar = ProgressBar(term_width=60, maxval=len(urls), 
                                       widgets=[name + ": ", Percentage(), ' ',
                                       Bar(marker='-', left='[', right=']'), ' ', ETA()]).start()

    def task_initial(self, grab, task):

        self.counter += 1
        try:
            if self.progressbar.update(self.counter + 1):
                print self.progressbar.update(self.counter + 1)
        except ValueError:
            pass

        found_location = None
        for elem in grab.doc('//li[@class="view-item-details-list-seller-city"]'):
            found_location = elem.text().replace("Ort: ","")

        if found_location:
            text = ""
            for elem in grab.doc('//div[@class="content-text view-item-long-description-content"]'):
                text += elem.text()

            random_handler = binascii.b2a_hex(os.urandom(15))[:10]
            uniqe_handler = "tradera://" + random_handler    

            blog = dict(url=uniqe_handler, 
                        source="tradera",
                        rank=2,
                        city=found_location.encode('utf-8'))

            mysqldb['blogs'].upsert(blog, ['url'])
            inserted_id = mysqldb['blogs'].find_one(url=uniqe_handler)['id']

            post = dict(blog_id=inserted_id, 
                        date=datetime.datetime.now(),
                        text=text.encode('utf-8'))

            mysqldb['posts'].insert(post)

            print "{}: {} tecken".format(found_location.encode('utf-8'), len(text))


def put_in_bloom(links):
    try:
        for url in links:
           bloom.add(url)
           pass
    except IndexError:
        print "Bloomfilter full. Restarting it (link counts will now go up)."
        global bloom
        bloom = BloomFilter(capacity=bloom_cap, error_rate=0.001)    

    with open(bloom_filename, 'wb') as f:
        pickle.dump(bloom, f, -1) 

    print "Stoppade {} urls i bloom".format(len(links))

from difflib import SequenceMatcher

def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

def normalize_links(links, restrict_to):

    # Check for custom linkstart
    try: 
        linkprefix = customlinkprefix[region][restrict_to]
    except KeyError: # Not in config
        linkprefix = "http://www."

    parsed_links = []

    for link in list(links):
        try:
            newlink = linkprefix + link.split("#")[0]\
                                                    .split("?")[0]\
                                                    .replace("https://www.", "")\
                                                    .replace("http://www.", "")\
                                                    .replace("http://", "")\
                                                    .replace("https://", "")
            # Remove trailing slash
            if newlink[-1] == "/":
                newlink = newlink[0:-1]

            parsed_links.append(newlink)
        except:
            pass

    parsed_links = list(set(parsed_links))

    return parsed_links
    

if __name__ == "__main__":

    while True:
        bot = LinkSpider("http://www.tradera.com", 
                         restrict_to="tradera.com", 
                         skip=[], 
                         thread_number=50,
                         network_try_limit=10)

        bot.run()
        scraped_urls = set(bot.urls_found)
        put_in_bloom(scraped_urls)
        print "Hittade {} urls".format(len(scraped_urls))

        bot = ContentSpider(scraped_urls, thread_number=50, network_try_limit=10)
        bot.run()
        bot.progressbar.finish()
        print "Done! Waiting a day..."
        time.sleep(60*60*24)
