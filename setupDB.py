#!/usr/bin/python
# -*- coding: utf-8 -*- 

from textLoc26 import *
import dataset
import config as c

print c.LOCATIONDB

if __name__ == "__main__":
    documents = dataset.connect(c.LOCATIONDB)

    q = "set names 'utf8'"
    documents.query(q)
    
    q = """
        CREATE TABLE IF NOT EXISTS GMMs (
          id int(11) NOT NULL AUTO_INCREMENT,
          date varchar(25) COLLATE utf8_general_ci DEFAULT NULL,
          scoring double NOT NULL,
          lat float DEFAULT NULL,
          word varchar(255) COLLATE utf8_general_ci DEFAULT NULL,
          lon float DEFAULT NULL,
          n_coordinates int(11) DEFAULT NULL,
          PRIMARY KEY (id),
          KEY idx_word (word),
          KEY idx_date (date)
        ) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci ;
        """

    documents.query(q)
    q = """
        CREATE TABLE IF NOT EXISTS blogs (
          city varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
          url varchar(800) COLLATE utf8_unicode_ci DEFAULT NULL,
          country varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
          municipality varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
          county varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
          id int(11) NOT NULL AUTO_INCREMENT,
          intrests text COLLATE utf8_unicode_ci,
          presentation text COLLATE utf8_unicode_ci,
          longitude float DEFAULT NULL,
          latitude float DEFAULT NULL,
          gender text COLLATE utf8_unicode_ci,
          age int(11) DEFAULT NULL,
          rank int(11) DEFAULT NULL,
          source text COLLATE utf8_unicode_ci,
          noCoordinate int(1) DEFAULT NULL,
          KEY (id),
          KEY url (url(255)),
          KEY country (country),
          KEY munici (municipality),
          KEY county (county),
          KEY city (city)
        ) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci ;
        """

    documents.query(q)
    q = """
        CREATE TABLE IF NOT EXISTS ngrams (
          id int(11) NOT NULL AUTO_INCREMENT,
          ngram int(11) DEFAULT NULL,
          frequency int(11) DEFAULT NULL,
          token varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
          entropy float DEFAULT NULL,
          deltaEnt50 float DEFAULT NULL,
          deltaEnt20 float DEFAULT NULL,
          deltaEnt10 float DEFAULT NULL,
          deltaEnt30 float DEFAULT NULL,
          deltaEnt40 float DEFAULT NULL,
          PRIMARY KEY (id),
          KEY ind_tok (token)
        ) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci ;
        """

    documents.query(q)
    q = """
        CREATE TABLE IF NOT EXISTS posts (
          id int(11) NOT NULL AUTO_INCREMENT,
          date datetime DEFAULT NULL,
          text text COLLATE utf8_unicode_ci,
          blog_id int(11) DEFAULT NULL,
          posttitle text COLLATE utf8_unicode_ci,
          posturl text COLLATE utf8_unicode_ci,
          PRIMARY KEY (id),
          KEY blog_id (blog_id)
        ) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci ;
        """

    documents.query(q)
    q = """
        CREATE TABLE IF NOT EXISTS tempngrams (
          id int(11) NOT NULL AUTO_INCREMENT,
          ngram int(11) DEFAULT NULL,
          frequency int(11) DEFAULT NULL,
          token varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
          PRIMARY KEY (id),
          KEY ind_tok (token)
        ) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci ;

        """

    documents.query(q)
    
    
    q = """
        CREATE TABLE IF NOT EXISTS tweets (
          id int(11) NOT NULL AUTO_INCREMENT,
          username text COLLATE utf8_unicode_ci,
          used int(11) DEFAULT NULL,
          lat float DEFAULT NULL,
          tweet varchar(255) COLLATE utf8_unicode_ci,
          lon float DEFAULT NULL,
          metadata varchar(255) COLLATE utf8_unicode_ci,
          PRIMARY KEY (`id`),
          FULLTEXT (tweet,metadata)
        ) ENGINE=InnoDB AUTO_INCREMENT=937 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci ;
    
        """
    documents.query(q)
    
    q = "ALTER DATABASE "+ c.DATABASENAME +" CHARACTER SET 'utf8' COLLATE 'utf8_unicode_ci'; "
    documents.query(q)
    
    q = "set character_set_client = 'utf8'"
    documents.query(q)
    
    q = "set character_set_connection = 'utf8'" 
    documents.query(q)
    
    q = "set character_set_database = 'utf8'"
    documents.query(q)
    
    q = "set character_set_results = 'utf8'"
    documents.query(q)
    
    q = "set character_set_server = 'utf8'"
    documents.query(q)
    
 