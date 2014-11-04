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
9. Run `runGUI.py` to start webserver
10. Point browser to `http://localhost:5000/sinus/` for GUI to explore the data. See *usage* for more details.
11. Run `getWordlist.py` to generate a wordlist.
12. Run `getEntropy.py` to start collecting words with low entropy. This corresponds to words being used very locally. E.g. `nypotatis` will have low entropy because that it's mainly used in southern Sweden. Words like `och, att, på` will have high entropy as they are used in the whole country. The findings of `getEntropy.py` can be found in the web GUI under `/explore`.

Geotagger
---------

To use the geotagger to tag data without metadata:

1. Run `fetchTweets.py` for a couple of months. This will get geotagged tweets to be used as a training set.
2. Run `compileGMMs.py` to build the model.
3. Run `tagData.py` to give your data coordinates (of resonable accuracy) if it is without metadata.
4. Search in the GUI with the flag `lowqualdata: 1`. This includes the inferred data `tagData.py` has produced.

Usage of GUI
------------

The GUI is usually accessible through `http://localhost:5000/sinus/`. Email `maxberggren@gmail.com` if you want to try our setup.

### Searching the document database for a word

Results will be on logaritimic frequency when only one search term is used.

![Search for a single term](../master/readmeimages/litta3.gif?raw=true)

This animation uses `xbins: <number>` that specifies how many bins/pixels that should be used on the x-axis. This coresponds to how fine grained resolution you want.

![Search with scatterdata as result](../master/readmeimages/litta_scatter.gif?raw=true)

Here `scatter: 1` will force it to produce a scatterplot instead. This can be better in some cases where the hits in the database are very few.

`binthreshold: <number>` will set how many hits per bin that is required for it to count. Default is 5 if not specified.

`uselowqualdata: 1` will use data of low rank. That means that e.g. tagged with the geotagger will be used.

### Searching the document database for words/terms against each other

Search results will now be in percent. E.g. av search for `tipspromenad` vs `tipsrunda` vs `poängpromenad` (a common swedish game) will show in percent how many of the hits corresponding to each term against the other.

![Geotag text](../master/readmeimages/multiple.gif?raw=true)

And let's try searching of phrases rather than just words. `flak öl` vs `platta öl` vs `karta öl` (different phrases in swedish describing 24 beer cans). Notice how it used a scatterplot since the last term `karta öl` had so few hits in the database.

![Geotag text](../master/readmeimages/kartaplatta.gif?raw=true)

### Trying out the geotager (that is used by `tagData.py`)

The GUI can also access the geotagger that is used to tag data that have no metadata. 

![Geotag text](../master/readmeimages/hbg.gif?raw=true)

