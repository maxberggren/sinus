#!/usr/bin/python
# -*- coding: utf-8 -*- 

from textLoc26 import *

if __name__ == "__main__":
    model = tweetLoc()
    #model.loadTXT("/Users/maxberggren/Dropbox/Dokument/Python/Gavagai/testdata2.txt")
    
    model.createGMMs(model.commonWords())
    #start_time = time.time()
    #print model.predict("stockholm är en go plats".decode("utf-8"))
    #print time.time() - start_time, "seconds"
    