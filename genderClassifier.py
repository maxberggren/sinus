from __future__ import print_function

from pprint import pprint
from time import time
import logging

from sklearn.datasets import fetch_20newsgroups
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.linear_model import SGDClassifier
from sklearn.grid_search import GridSearchCV
from sklearn.pipeline import Pipeline
import numpy as np
import dataset
import urllib2
import requests
from collections import OrderedDict
import config as c
import nltk
import codecs
from sklearn.cross_validation import train_test_split

# Get data
db = dataset.connect(c.LOCATIONDB+ "?charset=utf8")
db.query("set names 'utf8'")
result = db.query("SELECT b.* FROM blogs b "
                  "WHERE (SELECT count(*) FROM posts p WHERE " 
                  "       p.blog_id=b.id) > 0 AND "
                  "character_length(b.gender) > 0")
data = []
label = []

for row in result:
    posts = db['posts'].find(blog_id=row['id'])
    text = ""   
    for post in posts:
        text = text + u"\n\n" + post['text']
        
    if len(text) > 300:
        data.append(text)
        label.append(row['age'])
        #if row['gender'] == "man":
        #    label.append(0)
        #    data.append(text)
        #elif row['gender'] == "kvinna":
        #    label.append(1)
        #    data.append(text)

label = np.asarray(label)

X_train, X_test, Y_train, Y_test = train_test_split(data, label, test_size=0.33, random_state=42)


# Display progress logs on stdout
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s')

#print(type(data_train.data))
#print(type(data_train.target))

###############################################################################
# define a pipeline combining a text feature extractor with a simple
# classifier
pipeline = Pipeline([
    ('vect', CountVectorizer()),
    ('tfidf', TfidfTransformer()),
    ('clf', SGDClassifier()),
])

# uncommenting more parameters will give better exploring power but will
# increase processing time in a combinatorial way
parameters = {
    #'vect__max_df': (0.5, 0.75, 1.0),
    #'vect__max_features': (None, 5000, 10000, 50000),
    'vect__ngram_range': ((1, 1), (1, 2)),  # unigrams or bigrams
    #'tfidf__use_idf': (True, False),
    'tfidf__norm': ('l1', 'l2'),
    'clf__alpha': (0.00001, 0.000001),
    'clf__penalty': ('l2', 'elasticnet'),
    #'clf__n_iter': (10, 50, 80),
}



if __name__ == "__main__":
    # multiprocessing requires the fork to happen in a __main__ protected
    # block

    # find the best parameters for both the feature extraction and the
    # classifier
    grid_search = GridSearchCV(pipeline, parameters, n_jobs=-1, verbose=1)

    print("Performing grid search...")
    print("pipeline:", [name for name, _ in pipeline.steps])
    print("parameters:")
    pprint(parameters)
    t0 = time()
    
    grid_search.fit(X_train, Y_train)
    
    print("done in %0.3fs" % (time() - t0))
    print()

    print("Best score: %0.3f" % grid_search.best_score_)
    print("Best parameters set:")
    best_parameters = grid_search.best_estimator_.get_params()
    for param_name in sorted(parameters.keys()):
        print("\t%s: %r" % (param_name, best_parameters[param_name]))
                                     
    predicted = grid_search.predict(X_test)
    print(np.mean(predicted == Y_test))
    print("Done!")
