SINUS
=====

Repository for the SINUS project. Beware of the swedish GUI.

Setup
-----

1. Install dependencies `pip install -r requirements.txt`
2. Set up a MySQL database
3. Edit `config.example.py` with your MySQL credentials and rename to `config.py`
4. Run `setupDB.py` to create all tables.
5. Import 
  * Example data from `blabla.com` or
  * Run spider scripts in `/spiders` and when finished import the data with corresponding importscript `<source>2mysql.py`
6. Add the fulltext indexing to make searches decently fast (on 18 GB of data this took 24h so keep that in mind) 
  *`mysql> ALTER TABLE posts ADD FULLTEXT FTItext (text);`