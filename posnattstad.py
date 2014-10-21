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
import term
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
    db = dataset.connect('sqlite:///nattstad.db')
    db.begin()
    table = db['blogs']
    result = db.query('SELECT count(*) as nblogs FROM blogs WHERE LENGTH(presentation) > 1 and manuellStad is NULL')
    for row in result:
        nblogs = row['nblogs']
    print nblogs
    
    result = db.query('SELECT * FROM blogs WHERE LENGTH(presentation) > 1 and manuellStad is NULL order by id')
    

    for row in result:
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
                    print term.format(term.format(word, term.Attr.BOLD), term.Attr.HILIGHT),
                else:
                    print word,
            print "\nKandidater:\n"
            if len(kandidater) > 1:
                for i, kandidat in enumerate(kandidater):
                    print term.format("("+str(i+1)+") "+kandidat, term.Attr.BOLD)
            else:
                print term.format(term.format("(1) "+kandidater[0], term.Color.GREEN), term.Attr.BOLD)
            print term.format("(0) Inget alternativ rätt", term.Attr.BOLD)
            print term.format("(9) Avsluta", term.Attr.BOLD)
            print "\nTryck det nummer som representerar rätt stad. "

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
                table.update(dict(id=userId, manuellStad="n/a"), ['id'])
                db.commit()
                db.begin()
            else:
                userId = int(row['id'])
                table.update(dict(id=userId, manuellStad=kandidater[var-1]), ['id'])
                db.commit()
                db.begin()
        



#http://sv.wikipedia.org/w/index.php?title=Kategori:T%C3%A4torter_i_Sverige&pageuntil=Burl%C3%B6vs+egnahem#mw-pages






