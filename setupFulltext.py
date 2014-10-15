#!/usr/bin/python
# -*- coding: utf-8 -*- 

from textLoc26 import *
import dataset
import config as c

print c.LOCATIONDB

if __name__ == "__main__":
    documents = dataset.connect(c.LOCATIONDB)

    yesno = raw_input("Add fulltext? (y/n)")
    if yesno == "y":
        q = "ALTER TABLE posts ADD FULLTEXT FTItext (text)"
        documents.query(q)    
 