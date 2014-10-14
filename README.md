SINUS
=====

Repository for the SINUS project. Beware of the swedish GUI.

Setup
-----

1. Install dependencies `pip install -r requirements.txt` (TODO)
2. Set up a MySQL database
  * If your on OSX and like it easy try `brew install mysql` in terminal
  * If you dont have homebrew run `ruby <(curl -fsSk https://raw.github.com/mxcl/homebrew/go)` first in terminal
3. Edit `config.example.py` with your MySQL credentials and rename to `config.py`
4. Run `setupDB.py` to create all tables.
5. Get data: 
  * Example data from `blabla.com` or (TODO)
  * Run spider scripts in `/Spiders` 
6. Import the data with corresponding importscript `<source>2mysql.py`
7. Add the fulltext indexing to make searches decently fast (on 18 GB of data this took 24h so keep that in mind) 
  *`mysql> ALTER TABLE posts ADD FULLTEXT FTItext (text);`
8. Run `metadata2coordinates.py` to convert metadata to coordinates trough Google geoencoding API. This is limited to 2000 requests per 24h so if all your data is not converted, keep the script running for some days untill it's finished (if your bored you can continue but without all data avalible in the GUI).
8. Run `runflask.py` to start webserver
9. Point browser to `http://localhost:5000/sinus/` for GUI to explore the data.