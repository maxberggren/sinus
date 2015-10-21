#!/usr/bin/python
# -*- coding: utf-8 -*- 
from __future__ import division
#import nltk
import dataset
import re
import numpy as np
from collections import Counter
import time
import string 
import sqlalchemy
import warnings
import config as c
import pandas as pd
from sqlalchemy import create_engine
import MySQLdb
import reverse_geocoder as rg
  
llcrnrlon = 9.5
llcrnrlat = 54.5
urcrnrlon = 28.5
urcrnrlat = 69.5

xBins = 9
xyRatio = 1.8

lon_bins = np.linspace(llcrnrlon, urcrnrlon+2, xBins)
lat_bins = np.linspace(llcrnrlat, urcrnrlat+1, xBins*xyRatio)

lon_w = lon_bins[1]-lon_bins[0]
lat_h = lat_bins[1]-lat_bins[0]

for lllon in lon_bins:
    for lllat in lat_bins:
        centre = lllat+lat_h*0.5, lllon+lon_w*0.5
        if rg.get(centre)['cc'] == 'SE':
            print "count_words_in_region('{}', ({}, {}, {}, {}), percent=100)".format(rg.get(centre)['admin1']+rg.get(centre)['admin2'],
                                                                                      lllon + lon_w,
                                                                                      lllat + lat_h,
                                                                                      lllon,
                                                                                      lllat)

