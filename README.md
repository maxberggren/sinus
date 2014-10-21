SINUS
=====

Project for exploring Swedish social media data to find dialectal differences in the language. 

Setup
-----

1. Install dependencies `pip install -r requirements.txt` (TODO)
2. Set up a MySQL database
  * If your on OSX and like it easy try `brew install mysql` in terminal
  * If you dont have homebrew run `ruby <(curl -fsSk https://raw.github.com/mxcl/homebrew/go)` first in terminal
3. Edit `config.example.py` with your MySQL credentials and rename to `config.py`
4. Run `setupDB.py` to create all tables.
5. Run `mysql> set character_set_client = 'utf8'; set character_set_connection = 'utf8'; set character_set_database = 'utf8'; set character_set_results = 'utf8'; set character_set_server = 'utf8';` in mysql
5. Get data: 
  * Run spider scripts in `/Spiders` 
  * or bring your own data
6. Import the data with corresponding importscript `<source>2mysql.py`
7. Add the fulltext indexing to make searches decently fast (on 58 GB of data this took 24h so keep that in mind) 
  * Run `setupFulltext.py`
  * Note that for me the fulltext index needed 250 GB free hard drive space temporarily while generating the index on 58 GB.
8. Run `metadata2coordinates.py` to convert metadata to coordinates trough Google geoencoding API. This is limited to 2000 requests per 24h so if all your data is not converted, keep the script running for some days untill it's finished (if your bored you can continue but without all data avalible in the GUI).
9. Run `runflask.py` to start webserver
10. Point browser to `http://localhost:5000/sinus/` for GUI to explore the data.