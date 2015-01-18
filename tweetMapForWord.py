#!/usr/bin/python
# -*- coding: utf-8 -*- 
import matplotlib  
matplotlib.use('Agg')
import collections
from collections import OrderedDict
import itertools
import os
import random
from math import radians, cos, sin, asin, sqrt, isnan, exp, isnan
import numpy as np
#import pylab as pl
from sklearn import mixture
import dataset    
import codecs   
import datetime
import time
from operator import itemgetter
import config as c
from sqlite_cache import SqliteCache
import re
from collections import Counter
from sets import Set
import string
import geocode 
from geocode import latlon

from mpl_toolkits.basemap import Basemap, cm, maskoceans
import matplotlib.cm as cm
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.colors import LogNorm
from matplotlib.ticker import LogFormatter
from mpl_toolkits.axes_grid1 import make_axes_locatable
import matplotlib.pyplot as plt
import random
from matplotlib import rcParams
rcParams['font.family'] = 'serif'
import config as c


db = dataset.connect(c.LOCATIONDB+ "?charset=utf8")
db.query("set names 'utf8'")
result = db.query(u"select * from tweets where MATCH (tweet) AGAINST ('litta')")

lons, lats = [], []

for row in result:
    lons.append(row['lon'])
    lats.append(row['lat'])

fig = plt.figure(figsize=(3.25,4))
llcrnrlon = 8
llcrnrlat = 54.5
urcrnrlon = 26
urcrnrlat = 69.5
#urcrnrlat = 63.5

m = Basemap(projection='merc',
            resolution = 'i', 
            area_thresh=500,
            llcrnrlon=llcrnrlon, 
            llcrnrlat=llcrnrlat,
            urcrnrlon=urcrnrlon, 
            urcrnrlat=urcrnrlat,)   

m.drawcoastlines(linewidth=0.5)
m.drawcountries()
m.drawstates()
m.drawmapboundary()
m.fillcontinents(color='white',
                 lake_color='black',
                 zorder=0)
m.drawmapboundary(fill_color='black')
               

# Predicted latlon
xp, yp = m(lons, lats)
tweets = plt.scatter(xp, yp, s=5, c='r', lw=1, edgecolor='w') 

plt.legend((tweets),
           ('Predicted'),
           scatterpoints=1,
           loc='upper right',
           prop={'size':7})

    
fig.tight_layout(pad=2.5, w_pad=0.1, h_pad=0.0)  

filename = "tweetmap_" + str(random.randrange(0, 99999))
plt.savefig("sinusGUIapp/static/maps/" + filename +".pdf", dpi=100, bbox_inches='tight')   
