# -- coding: utf-8 --
import requests
from bs4 import BeautifulSoup
from pprint import pprint
from urlparse import urljoin
#from thready import threaded
import dataset

#import StringIO
import socket
import urllib
#import socks    # SocksiPy module
#import stem.process
#from stem.util import term
#import term
#from stem import Signal
#from stem.control import Controller
import os
import sys
#import requests
import os
from hashlib import sha1
import config as c



#from getch import _GetchUnix, _GetchWindows, _Getch, _GetchMacCarbon
#from getch import _GetchWindows, _Getch, _GetchMacCarbon
from getch import _GetchUnix

inkey = _GetchUnix()

with open('tatorter.txt') as f:
    tatorter = f.read().splitlines()
    tatorter = [tatort.decode('UTF-8') for tatort in tatorter]


if __name__ == '__main__':
    db = dataset.connect(c.LOCATIONDB+ "?charset=utf8")
    db.begin()
    table = db['blogs']
    nblogs = 13866
    print nblogs
    result = db.query("SELECT b.* FROM blogs b "
                      "WHERE (SELECT count(*) FROM posts p WHERE  "
                      "p.blog_id=b.id) > 0 AND "
                      "character_length(b.presentation) > 5 ")

    for i, row in enumerate(result):
        #print row['presentation']
        kandidater = []
        data = row['presentation'].split()
        data = [word.replace(".","").replace(",","").replace("!","").replace("?","") for word in data]
        for word in data:
            if word in tatorter:
                kandidater.append(word)

        if len(kandidater) > 0:
            os.system('clear') # on linux / os x
            print "{:.0%}".format(float(row['id'])/float(nblogs))
            print ""
            
            for word in row['presentation'].split():
                if word.replace(".","").replace(",","").replace("!","").replace("?","") in tatorter:
                    print word,
                else:
                    print word,

            print ""
            print "(0) Ej explicit angivet"
            print "(1) Tjej"
            print "(2) Kille"
            print "(9) Avsluta"
            print "\nTryck det nummer som representerar rätt kön. "

            try:
                var = int(inkey())
            except:
                var = 9
                
            if var == 9:
                db.commit()
                #db.begin()
                sys.exit(0)
            elif var == 0:
                userId = int(row['id'])
                table.update(dict(id=userId, manuellKon=0), ['id'])
                db.commit()
                db.begin()
            elif var == 1:
                userId = int(row['id'])
                table.update(dict(id=userId, manuellKon=1), ['id'])
                db.commit()
                db.begin()
            elif var == 2:
                userId = int(row['id'])
                table.update(dict(id=userId, manuellKon=2), ['id'])
                db.commit()
                db.begin()
        





