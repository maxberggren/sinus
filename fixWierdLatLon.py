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
            result = db.query("select * from blogs where "
                              "CAST(latitude AS DECIMAL) = CAST(62.1983 AS DECIMAL)  "
                              "and CAST(longitude AS DECIMAL) = CAST(17.565 AS DECIMAL) ")
                                  
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

                if coordinate == (62.1983, 17.565):
                    print "Sveriges mitt e inte sau gott"
                    coordinate = None
                  
                if coordinate:
                    print (city + "," if city else ""),
                    print (muni + "," if muni else ""),
                    print (county + "," if county else ""),
                    print (country + "," if country else ""),
                    print "->", coordinate
                    
                    try:
                        data = dict(longitude=coordinate[1],
                                    latitude=coordinate[0],
                                    city=city.decode('utf-8'),
                                    municipality=muni.decode('utf-8'),
                                    county=county.decode('utf-8'),
                                    country=country.decode('utf-8'))
                
                        db['blogs'].update(data, ['city',
                                                  'municipality',
                                                  'county',
                                                  'country'])
                
                    except:
                        print "Unexpected error:", sys.exc_info()[0]
        
                else: 
                    # No coordinate found -> flag as DoNotTryAgain
                    try:
                        data = dict(longitude=None,
                                    latitude=None,
                                    noCoordinate=1,
                                    city=city.decode('utf-8'),
                                    municipality=muni.decode('utf-8'),
                                    county=county.decode('utf-8'),
                                    country=country.decode('utf-8'))
                                   
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
            