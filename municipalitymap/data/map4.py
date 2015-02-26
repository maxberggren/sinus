#!/usr/bin/python
# -*- coding: utf-8 -*-
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from mpl_toolkits.basemap import Basemap
from mpl_toolkits.axes_grid1 import make_axes_locatable
from shapely.geometry import Point, Polygon, MultiPoint, MultiPolygon
from shapely.prepared import prep
from matplotlib.collections import PatchCollection
from descartes import PolygonPatch
import json
import datetime
from pysal.esda.mapclassify import Natural_Breaks
from data import data

words = [u'nästkusin', u'småkusin', u'tremänning', u'syssling']
words = [u'nästkusin']

def custom_colorbar(cmap, ncolors, labels, **kwargs):    
    """ Create a custom, discretized colorbar with correctly 
        formatted/aligned labels.
    
        cmap: the matplotlib colormap object you plan on using 
        for your graph
        ncolors: (int) the number of discrete colors available
        labels: the list of labels for the colorbar. Should be 
        the same length as ncolors.
    """
    from matplotlib.colors import BoundaryNorm
    from matplotlib.cm import ScalarMappable
        
    norm = BoundaryNorm(range(0, ncolors), cmap.N)
    mappable = ScalarMappable(cmap=cmap, norm=norm)
    mappable.set_array([])
    mappable.set_clim(-0.5, ncolors+0.5)
    colorbar = plt.colorbar(mappable, **kwargs)
    colorbar.set_ticks(np.linspace(0, ncolors, ncolors+1)+0.5)
    colorbar.set_ticklabels(range(0, ncolors))
    colorbar.set_ticklabels(labels)
    return colorbar

def opacify(cmap):
    """ Add opacity to a colormap going from full opacity to no opacity """
    cmap._init()
    alphas = np.abs(np.linspace(0, 1.0, cmap.N))
    cmap._lut[:-3,-1] = alphas
    return cmap

llcrnrlon = 8
llcrnrlat = 54.5
urcrnrlon = 26
urcrnrlat = 69.5

m = Basemap(projection='merc',
            resolution = 'i', 
            area_thresh=500,
            llcrnrlon=llcrnrlon, 
            llcrnrlat=llcrnrlat,
            urcrnrlon=urcrnrlon, 
            urcrnrlat=urcrnrlat) 

# County data
_out = m.readshapefile('data/alla_lan/alla_lan_Std', 
                       name='countys', drawbounds=False, 
                       color='none', zorder=2)

# Municipality data
_out = m.readshapefile('data/Kommuner_SCB/Kommuner_SCB_Std', 
                       name='muni', drawbounds=False, 
                       color='none', zorder=3)
_out = m.readshapefile('data/N2000-Kartdata-master/NO_Kommuner_pol_latlng', 
                       name='muni_no', drawbounds=False, 
                       color='none', zorder=3)
_out = m.readshapefile('data/finland/finland-11000000-administrative-regions', 
                       name='muni_fi', drawbounds=False, 
                       color='none', zorder=3)

lds, coord_count = [], {}

#for r in m.muni_fi_info:
#    print r

for d, word in zip(data, words):
    coord_count[word] = len(d)
    ld = pd.DataFrame(d, columns=['longitude', 'latitude'])
    ld['word'] = word
    lds.append(ld)

lds = pd.concat(lds)

# Municipality DF (SE + NO + FI)
polygons = [Polygon(p) for p in m.muni] + \
           [Polygon(p) for p in m.muni_no] + \
           [Polygon(p) for p in m.muni_fi]
names = [r['KNNAMN'] for r in m.muni_info] + \
        [r['NAVN'] for r in m.muni_no_info] + \
        [r['Kunta'] for r in m.muni_fi_info]
areas = [r['LANDAREAKM'] for r in m.muni_info] + \
        [r['Shape_Area'] for r in m.muni_no_info] + \
        [0 for r in m.muni_fi_info]

df_map_muni = pd.DataFrame({'poly': polygons, 'name': names, 'area': areas})

# County DF
df_map_county = pd.DataFrame({
    'poly': [Polygon(countys_points) for countys_points in m.countys],
    'name': [r['LAN_NAMN'] for r in m.countys_info]})

mapped_points, all_points, hood_polygons_county = {}, {}, {}
mapped_points_county, mapped_points_muni, hood_polygons_muni = {}, {}, {}

for word, ld in lds.groupby(['word']):
    
    # Convert our latitude and longitude into Basemap cartesian map coordinates
    mapped_points[word] = [Point(m(mapped_x, mapped_y)) 
                           for mapped_x, mapped_y 
                           in zip(ld['longitude'], ld['latitude'])]
                           
    all_points[word] = MultiPoint(mapped_points[word])

    # Use prep to optimize polygons for faster computation
    hood_polygons_county[word] = prep(MultiPolygon(list(df_map_county['poly'].values)))
    hood_polygons_muni[word] = prep(MultiPolygon(list(df_map_muni['poly'].values)))

    # Filter out the points that do not fall within the map we're making
    mapped_points_county[word] = filter(hood_polygons_county[word].contains, all_points[word])
    mapped_points_muni[word] = filter(hood_polygons_muni[word].contains, all_points[word])


def num_of_contained_points(apolygon, mapped_points):
    """ Counts number of points that fall into a polygon """
    return int(len(filter(prep(apolygon).contains, mapped_points)))

for word in words:
    df_map_county[word] = df_map_county['poly'].apply(num_of_contained_points, 
                                                      args=(mapped_points_county[word],))
    df_map_muni[word] = df_map_muni['poly'].apply(num_of_contained_points, 
                                                  args=(mapped_points_muni[word],))

# Get total occurencies in every county/municipality
df_map_county["sum"] = df_map_county[words].sum(axis=1)
df_map_muni["sum"] = df_map_muni[words].sum(axis=1)

# Convert to percentages and skip where there is none
def df_percent(df_map):
    df_map = df_map[df_map['sum'] > 0]
    df_map[words] = df_map[words].astype('float').div(df_map["sum"].astype('float'), axis='index')
    return df_map

df_map_county = df_percent(df_map_county)
df_map_muni = df_percent(df_map_muni)

# We'll only use a handful of distinct colors for our choropleth. 
# These will be overwritten if only one word is being plotted.
breaks = [0., 0.25, 0.5, 0.75, 1.0]

def self_categorize(entry, breaks):
    for i in range(len(breaks)-1):
        if entry > breaks[i] and entry <= breaks[i+1]:
            return i
    return -1

labels = ['0 %', '25 %', '50 %', '75 %', '100 %']
colorCycle = ['Reds', 'Blues', 'BuGn', 'Purples', 'PuRd',
              'Reds', 'Blues', 'BuGn', 'Purples', 'PuRd',
              'Reds', 'Blues', 'BuGn', 'Purples', 'PuRd',
              'Reds', 'Blues', 'BuGn', 'Purples', 'PuRd',
              'Reds', 'Blues', 'BuGn', 'Purples', 'PuRd',
              'Reds', 'Blues', 'BuGn', 'Purples', 'PuRd']


fig = plt.figure(figsize=(3.25*len(words),6))

for i, word in enumerate(words):
    df_map_county['jenks_bins_'+word] = df_map_county[word].apply(self_categorize, args=(breaks,))
    df_map_muni['jenks_bins_'+word] = df_map_muni[word].apply(self_categorize, args=(breaks,))

    ax = fig.add_subplot(1, len(words), int(i+1), axisbg='w', frame_on=False)
    ax.set_title(u"{word} - hits: {hits}".format(word=word, hits=coord_count[word]), 
                 y=1.01, fontsize=9)

    cmap = plt.get_cmap(colorCycle[i])
    cmap = opacify(cmap)
    
    #for df_map in [df_map_county, df_map_muni]:
    for df_map in [df_map_muni]:

        if len(words) == 1: # When only one word, use Jenkins natural breaks
            breaks = Natural_Breaks(df_map['sum'], initial=300, k=3)
            df_map['jenks_bins_'+word] = breaks.yb
            
            labels = ['0', "> 0"] + ["> %d"%(perc) for perc in breaks.bins[:-1]]

        # Draw neighborhoods with grey outlines
        df_map['patches'] = df_map['poly'].map(lambda x: PolygonPatch(x, 
                                                                      ec='#111111', 
                                                                      lw=0, 
                                                                      alpha=0, 
                                                                      zorder=4))
        pc = PatchCollection(df_map['patches'], match_original=True)
        # Apply our custom color values onto the patch collection
        cmap_list = [cmap(val) for val in (df_map['jenks_bins_'+word].values - 
                                           df_map['jenks_bins_'+word].values.min())/(
                                                  df_map['jenks_bins_'+word].values.max()-
                                                  float(df_map['jenks_bins_'+word].values.min()))]
        pc.set_facecolor(cmap_list)
        ax.add_collection(pc)
        
    m.drawcoastlines(linewidth=0.5)
    m.drawcountries()
    m.drawstates()
    m.drawmapboundary()
    m.fillcontinents(color='white', lake_color='black', zorder=0)
    m.drawmapboundary(fill_color='black')

    divider = make_axes_locatable(plt.gca())
    cax = divider.append_axes("bottom", 
                              "2%", 
                              pad="2.5%")
                    
    cbar = custom_colorbar(cmap, ncolors=len(labels)+1, 
                           labels=labels, 
                           orientation='horizontal', 
                           cax=cax)
    cbar.ax.tick_params(labelsize=6)
    
    
        
fig.tight_layout(pad=2.5, w_pad=0.1, h_pad=0.0) 
plt.plot()
plt.savefig('koroplet.pdf', dpi=100, bbox_inches='tight')





