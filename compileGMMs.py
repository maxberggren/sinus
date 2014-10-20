#!/usr/bin/python
# -*- coding: utf-8 -*- 

from textLoc26 import *

if __name__ == "__main__":
    model = tweetLoc()
    print model.createGMMs(model.commonWords())
