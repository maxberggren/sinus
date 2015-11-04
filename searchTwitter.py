from __future__ import absolute_import
from pprint import pprint
import json

import tweepy

# == OAuth Authentication ==
#
# This mode of authentication is the new preferred way
# of authenticating with Twitter.

# The consumer keys can be found on your application's Details
# page located at https://dev.twitter.com/apps (under "OAuth settings")
consumer_key = "A99c0DYyJINGH7vP12ZwFYYYO"
consumer_secret = "3CWcZEIOVXnTQlQyq3SBxOGevq3DUpVTyb0O2ev0Dj3TRyVShO"

# The access tokens can be found on your applications's Details
# page located at https://dev.twitter.com/apps (located
# under "Your access token")
access_token = "18907132-LNzzRokXpKvbrm9npNHyn4y0r9rpGeViCLGE9PljH"
access_token_secret = "HqGuk2CpsWjJfZiWYrqgq5nH3F1OLa6AWs9pbFuzKI9s2"

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.secure = True
auth.set_access_token(access_token, access_token_secret)

api = tweepy.API(auth)

# If the authentication was successful, you should
# see the name of the account print out



for result in api.search(q="farit", lang="sv", geocode="63.902123,17.921551,100km"):
    pprint(result.text)
    print result._json
    print result._json['user']['location']
    print result._json['coordinates']
    print "\n\n"