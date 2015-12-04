#!/usr/bin/python
# -*- coding: utf-8 -*- 
from __future__ import division
import dataset
import re
import numpy as np
from collections import Counter
import time
import string 
import sqlalchemy
import warnings
import config as c
import gensim
import logging
import os
import sys

db = dataset.connect(c.LOCATIONDB)
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.ERROR)

def data_generator(bounding_box, percent=50):

    urcrnrlon, urcrnrlat, llcrnrlon, llcrnrlat = bounding_box
    
    # Find number of documents
    result = db.query("SELECT count(*) as count "
                      "FROM posts INNER JOIN blogs ON "
                      "blogs.id=posts.blog_id "
                      "WHERE blogs.latitude is not NULL "
                      "AND blogs.longitude is not NULL "
                      "AND blogs.rank <= 4 "
                      "AND blogs.longitude > " + str(llcrnrlon) + " "
                      "AND blogs.longitude < " + str(urcrnrlon) + " "
                      "AND blogs.latitude > " + str(llcrnrlat) + " "
                      "AND blogs.latitude < " + str(urcrnrlat) + " "
                      "AND blogs.source <> 'fotosidan' ")

    for row in result:
        nPosts = row['count']
    print "{} dokument finns i rutan".format(nPosts) 

    batch = 10000
    print "Hämtar {} procent av datat i batchar om {}".format(percent, batch)

    nPosts = int(percent*nPosts/100.0) 
    offsets = xrange(0, nPosts, batch)
    
    transtab = string.maketrans("ABCDEFGHIJKLMNOPQRSTUVXYZÅÄÖÉ",
                                "abcdefghijklmnopqrstuvxyzåäöé")
    punkter = string.punctuation
    
    for offset in offsets:
        start = time.time()
        sentences = []

        result = db.query("SELECT posts.text "
                          "FROM posts INNER JOIN blogs ON "
                          "blogs.id=posts.blog_id "
                          "WHERE blogs.latitude is not NULL "
                          "AND blogs.longitude is not NULL "
                          "AND blogs.rank <= 4 "
                          "AND blogs.longitude > " + str(llcrnrlon) + " "
                          "AND blogs.longitude < " + str(urcrnrlon) + " "
                          "AND blogs.latitude > " + str(llcrnrlat) + " "
                          "AND blogs.latitude < " + str(urcrnrlat) + " "
                          "AND blogs.source <> 'fotosidan' "
                          "LIMIT "+ str(batch) +" offset " + str(offset))

        remainingBatches = (nPosts - offset)/batch
        print str(100*offset/nPosts)[0:4], "%", "- Tog:", int((time.time() - start)), "sekunder."    
        
        for row in result:
            words = row['text'].translate(transtab, punkter).split()
            words = [w.strip() for w in words]
            sentences.append(words)
            yield words

def make_dictionary(bounding_box, percent=50, filename='riket.dict'):

    # Set up empty object
    model = gensim.models.Word2Vec(workers=4, size=100, min_count=0.005*percent*100)
    # Fill with vocabulary
    model.build_vocab(data_generator(bounding_box, percent=percent))
    model.save(filename)

    return filename
    

def make_wordroom(bounding_box, dict_filename, filename, percent=50):

    # Always take dict state from whole country
    model = gensim.models.word2vec.Word2Vec.load(dict_filename)
    model.train(data_generator(bounding_box, percent=percent)) 
    model.save("wordrooms/"+filename)

if __name__ == "__main__":

    if gensim.models.word2vec.FAST_VERSION == -1:
        print "Kan inte använda alla processorer, någe e fel."

    base_word = sys.argv[1]
    pattern = "{wordroom:>10} | {similar} "

    print pattern.format(wordroom="ordrum",
                         similar="mest likt: {}".format(base_word))

    print pattern.format(wordroom="-"*10,
                         similar="-"*40)

    for filename in ['riket.m', 'skane.m', 'norrland.m', 'finland.m', 'gotland.m']:
        model = gensim.models.word2vec.Word2Vec.load("wordrooms/" + filename)

        most_sim = u""
        for i, (word, sim) in enumerate(model.most_similar(positive=[base_word.decode('utf-8').encode('latin-1')], topn=8)):
            most_sim += u"{}) {} ".format(i+1, word.decode('latin-1'))

        print pattern.format(wordroom=filename.replace(".m",""),
                             similar=most_sim.encode('utf-8'))

    print ""
    print ""



    """
    dict_filename = make_dictionary(bounding_box=(26, 69.5, 8, 54.5), percent=11)

    # Riket
    make_wordroom((26, 69.5, 8, 54.5), 
                   dict_filename='riket.dict',
                   filename='riket.m',
                   percent=100)

    # Skåne
    make_wordroom((14.653015, 56.256273, 12.551880, 55.349353), 
                   dict_filename='riket.dict',
                   filename='skane.m',
                   percent=100)

    # Norrland
    make_wordroom((25.975690, 69.173527, 12.372609, 62.213702), 
                   dict_filename='riket.dict',
                   filename='norrland.m',
                   percent=100)

    # Finland
    make_wordroom((26.971690, 65.189505, 20.643567, 59.497556), 
                   dict_filename='riket.dict',
                   filename='finland.m',
                   percent=100)

    # Gotland
    make_wordroom((19.593651, 58.081954, 17.739940, 56.724710), 
                   dict_filename='riket.dict',
                   filename='gotland.m',
                   percent=100)
    """








