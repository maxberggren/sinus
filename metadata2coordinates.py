#!/usr/bin/python
# -*- coding: utf-8 -*- 

from textLoc26 import *
#import sys
import dataset
import re
from geocode import latlon
import geocode
import numpy as np
import urllib2
import requests
import json
from collections import OrderedDict
import types
import sys
import time
from datetime import datetime, timedelta
import config as c
import sqlalchemy

NumberTypes = (types.IntType, types.LongType, types.FloatType, types.ComplexType)

class NoResultError(Exception):
    def __init__(self, code):
        self.code = code
    def __str__(self):
        return repr(self.code)


if __name__ == "__main__":
    db = dataset.connect(c.LOCATIONDB)
    db.query("set names 'utf8'") 
    
    while True:
        try:
            result = db.query("SELECT distinct np.city, np.municipality, "
                              "np.county, np.country FROM "
                              "(select * from blogs "
                              "  WHERE (latitude is NULL "
                              "         AND noCoordinate is NULL "
                              "         AND city = 'Rörö') "
                              "  AND "
                              "        ((city is not NULL or "
                              "          municipality is not NULL "
                              "          OR county is not NULL) "
                              "         OR "
                              "         (city <> '' or "
                              "          municipality <> '' "
                              "          OR county <> ''))"
                              " )np ")
                                  
            for row in result:
                # Set Nones to empty strings so latlon gets it
                
                city = (row['city'] if row['city'] else "")
                muni = (row['municipality'] if row['municipality'] else "")
                county = (row['county'] if row['county'] else "")
                country = (row['country'] if row['country'] else "")
                                
                coordinate = None
        
                # ------------------------------------------------
                # This wierd code says:
                # Can't find city + muni + county + country try:
                #                   muni + county + country then:
                #                          county + country
                # But if that fails give up.
                
                try:
                    coordinate = latlon(city + ", " + 
                                       muni + ", " + 
                                       county + ", " + 
                                       country)
                except geocode.NoResultError as error:
                    print error
                    try:
                        coordinate = latlon(muni + ", " + 
                                           county + ", " + 
                                           country)
                    except geocode.NoResultError as error:
                        print error
                        try:
                            coordinate = latlon(county + ", " + 
                                               country)
                        except geocode.NoResultError as error:
                            print error
                            coordinate = None
                # ------------------------------------------------
        
                city = row['city']
                muni = row['municipality'] 
                county = row['county'] 
                country = row['country']   
                  
                if coordinate:
                    print (city + "," if city else ""),
                    print (muni + "," if muni else ""),
                    print (county + "," if county else ""),
                    print (country + "," if country else ""),
                    print "->", coordinate
                    #try:
                    data = dict(longitude=coordinate[1],
                                latitude=coordinate[0],
                                city=city.decode('utf-8'),
                                municipality=muni.decode('utf-8'),
                                county=county.decode('utf-8'),
                                country=country.decode('utf-8'))

                    
                    city = (row['city'] if row['city'] else u"")
                    muni = (row['municipality'] if row['municipality'] else u"")
                    county = (row['county'] if row['county'] else u"")
                    country = (row['country'] if row['country'] else u"")                     
                    
                    print "hej"

                          
                    db['blogs'].update(data, ['city',
                                              'municipality',
                                              'county',
                                              'country'])
                
                    #except:
                    #    print "Unexpected error:", sys.exc_info()[0]
        
                else: 
                    # No coordinate found -> flag as DoNotTryAgain
                    try:
                        data = dict(noCoordinate=1,
                                    city=city,
                                    municipality=muni,
                                    county=county,
                                    country=country)
                                   
                        db['blogs'].update(data, ['city',
                                                  'municipality',
                                                  'county',
                                                  'country'])
        
                    except:
                        print "Unexpected error:", sys.exc_info()[0]
            break
        except KeyboardInterrupt:
            break
            print "Avslutar"
            
        except sqlalchemy.exc.OperationalError:
            continue
            
        except geocode.QueryLimitError:
            print "Googles API bjuder inte på mer nu. Måste vänta 24h."
            print "Väntar till",
            twentfourfromnow = datetime.now() + timedelta(hours=24)
            print '{:%H:%M}'.format(twentfourfromnow)
            time.sleep(60*60*24 + 10) # 24h + 10 s
            