from __future__ import division
# -*- coding: utf-8 -*-
import matplotlib  
matplotlib.use('Agg')
from textLoc26 import *
from mpl_toolkits.basemap import Basemap, cm, maskoceans
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.colors import LogNorm
#from scipy import stats
#from scipy import misc
from scipy import ndimage
import numpy as np
import matplotlib.pyplot as plt

def genFigures(words=['han']):
    
    binNrScaleFactor = 50 # control how many bins
    xyRatio = 1.75 # to control the squarness of bins
    blurFactor = 0.3 # how much to smooth the density
    
    # Colors
    nicered = [0.9, 0.03, 0.16]
    blue = [126/255, 175/255, 212/255]
    purple = [216/255, 14/255, 166/255]
    
    colorCycle = [blue, nicered, purple]
    model = tweetLoc(dbtweets='sqlite:///tweets15aug.db')
    
    searchWords = ()
    
    for word in words:
        searchWords = searchWords + (model.getCoordinatesFor(word, getUsed=True, limit=None),)
    
    totCoordinates = 0
    for kordinater in searchWords:
        totCoordinates += len(kordinater)
    
    fig = plt.figure(figsize=(3.25*len(searchWords),6))
    
    for i, kordinater in enumerate(searchWords):
    
        ax = fig.add_subplot(int("1"+str(len(searchWords))+str(i+1)))
        
        m = Basemap(projection='merc', lat_0=58, lon_0=18,
            resolution = 'i', area_thresh=500,
            llcrnrlon=8, llcrnrlat=54.5,
            urcrnrlon=26, urcrnrlat=69.5,)   
        
        m.drawcoastlines()
        m.drawcountries()
        m.drawstates()
        m.drawmapboundary()
        m.fillcontinents(color='white',lake_color='black',zorder=0)
        m.drawmapboundary(fill_color='black')
    
        lons, lats = zip(*kordinater) 
        #lonsmesh, latsmesh = np.meshgrid(lons, lats)
        
        lons = np.array(lons)
        lats = np.array(lats)
    
        lon_bins = np.linspace(8, 26, binNrScaleFactor)
        lat_bins = np.linspace(54.5, 69.5, binNrScaleFactor*xyRatio)    
            
        density, _, _ = np.histogram2d(lats, lons, [lat_bins, lon_bins])
        density = ndimage.gaussian_filter(density, blurFactor) # gaussian blur
        #density = maskoceans(lonsmesh, latsmesh, density)
    
        lon_bins_2d, lat_bins_2d = np.meshgrid(lon_bins, lat_bins)
        xs, ys = m(lon_bins_2d, lat_bins_2d)
        xs = xs[0:density.shape[0], 0:density.shape[1]]
        ys = ys[0:density.shape[0], 0:density.shape[1]]
        
        cdict = {'red':  ( (0.0,  1.0,  1.0),
                           (1.0,  colorCycle[i][0],  1.0) ),
                 'green':( (0.0,  1.0,  1.0),
                           (1.0,  colorCycle[i][1], 0.0) ),
                 'blue': ( (0.0,  1.0,  1.0),
                           (1.0,  colorCycle[i][2], 0.0) ) }
                           
        custom_map = LinearSegmentedColormap('custom_map', cdict)
        custom_map._init()
        alphas = np.linspace(0, 1, custom_map.N+3)
        custom_map._lut[:,-1] = alphas
        custom_map.set_bad(alpha=0.0)
        
        plt.register_cmap(cmap=custom_map)
        
        #p = plt.contourf(xs, ys, density, cmap="custom_map", 
        #                 norm=LogNorm(), vmin=1, vmax=float(totCoordinates)/70.0, 
        #                 antialiased=True)
        p = plt.contourf(xs, ys, density, 
                         norm=LogNorm(), vmin=1, vmax=float(totCoordinates)/70.0, 
                         antialiased=True)
    
    fig.tight_layout()   
    plt.savefig("karta.png", dpi=200)
    plt.savefig("karta.eps", dpi=200)

genFigures(['han'])