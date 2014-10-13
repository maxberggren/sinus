#!/usr/bin/python
# -*- coding: utf-8 -*- 

from textLoc26 import *
import dataset
import config as c

if __name__ == "__main__":
    documents = dataset.connect(c.DOCDB_URI)

    q = """
        CREATE TABLE IF NOT EXISTS GMMs (
          id int(11) NOT NULL AUTO_INCREMENT,
          date varchar(25) COLLATE utf8_unicode_ci DEFAULT NULL,
          scoring double NOT NULL,
          lat float DEFAULT NULL,
          word varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
          lon float DEFAULT NULL,
          n_coordinates int(11) DEFAULT NULL,
          PRIMARY KEY (id),
          KEY idx_word (word),
          KEY idx_date (date)
        ) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci ;

        """

    documents.query(q)