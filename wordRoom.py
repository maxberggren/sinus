#!/usr/bin/python
# -*- coding: utf-8 -*- 

from textLoc26 import *
import sys, traceback
import dataset
import re
import numpy as np
import urllib2
import json
import datetime
import config as c
from elasticsearch import Elasticsearch
from elasticsearch import helpers
import gensim
import logging
import os

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

class ESiterator(object):
    def __init__(self):
        self.es = Elasticsearch()
        q = {"query": {"match_all": {}}}
        self.scan_resp = helpers.scan(client=self.es, query=q, scroll="10m", index="sinus-index", timeout="10m")
 
    def __iter__(self):
        for resp in self.scan_resp:
            yield resp["_source"]['text'].split()

sentences = ESiterator()
model = gensim.models.Word2Vec(workers=4)
model.build_vocab(sentences)
sentences = ESiterator()
model.train(sentences)  
model.save('/tmp/sinus')
model.similarity('litta', 'lite')

"""
model = gensim.models.Word2Vec(sentences, workers=4)
model.save('/tmp/sinus')
#model = gensim.models.Word2Vec.load('/tmp/sinus')
model.similarity('litta', 'lite')
"""