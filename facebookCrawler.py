#!/usr/bin/python
# -*- coding: utf-8 -*-

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
import time
import cPickle as pickle

EMAIL = 'maxberggren@gmail.com'
USERNAME = 'maxberggren'
PASSWORD = 'wig6?aEPA'

browser = webdriver.Firefox() # Get local session of firefox
browser.get("https://facebook.com/") # Load page

try:
    # Try to load old cookies with login credentials
    cookies = pickle.load(open("cookies.pkl", "rb"))
    for cookie in cookies:
        browser.add_cookie(cookie)

    browser.get("https://facebook.com/") # Load page again with credentials
except IOError: # Cookie file not there
    pass

def login():
    elem = browser.find_element_by_id("email")
    time.sleep(1.2) 
    elem.send_keys(EMAIL)

    elem = browser.find_element_by_class_name("uiInputLabelLabel")
    elem.click()

    elem = browser.find_element_by_id("pass")
    time.sleep(1) 
    elem.send_keys(PASSWORD + Keys.RETURN)

    time.sleep(0.2)
    pickle.dump(browser.get_cookies() , open("cookies.pkl","wb"))

try: # If login found, login...
    found = browser.find_element_by_xpath("//input[@id='email']")
    login()
except NoSuchElementException:
    pass

def friends():
    browser.get("https://www.facebook.com/{}/friends".format(USERNAME))
    time.sleep(1) 

    for i in range(20):
        browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(0.2) 

    friends = []
    elements = browser.find_elements_by_xpath("//a")
    for elem in elements:
        if elem.get_attribute("href"):
            if "friends_tab" in elem.get_attribute("href"):
                friend = elem.get_attribute("href").split("?")[0]
                friends.append(friend)

    friends = list(set(friends))
    friends_about_pages = [f + "/about" for f in friends]

    return friends, friends_about_pages

def friends_origin(friend):

    browser.get(friend)

    try:
        elements = browser.find_element_by_xpath("//div[@data-overviewsection='places']")
    except NoSuchElementException:
        return None

    for elem in elements.text.split(u"\n"):
        text = elem
        lives_in, friend_from = None, None

        if u"Från " in text:
            return text.replace(u"Från ", u"")
        if u"Bor i" in text:
            lives_in = text.replace(u"Bor i ", u"")

    return lives_in

def user_posts(user_url, scroll=50):
    browser.get(user_url)    

    for full_name in browser.find_elements_by_xpath("//span[@id='fb-timeline-cover-name']"):
        name = full_name.text
        print name

    for i in range(scroll):
        browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1) # Let the page load, will be added to the API

    posts = []
    comments = []

    # User posts
    for post in browser.find_elements_by_class_name('userContentWrapper'):

        try:
            found = post.find_element_by_xpath(".//h5/span/span/span/a").text.strip()
        except NoSuchElementException:
            found = ""

        if found == name: # If the friends own content
            try:
                text = post.find_element_by_xpath(".//div[contains(@class, 'userContent')]/p").text
                posts.append(text.strip())
            except NoSuchElementException:
                pass

    # User comments
    elements = browser.find_elements_by_xpath("//div[@class='UFICommentContent']")
    for elem in elements:
        commenter_name = elem.find_elements_by_xpath("./span")[0].text
        if commenter_name == name:
            comments.append(elem.find_elements_by_xpath("./span")[1].text)

    return posts, comments

# Get all friends
friends_urls, friends_about_pages = friends()
print friends_urls
print friends_about_pages
for friend, about_page in zip(friends_urls, friends_about_pages):

    print friend
    print friends_origin(about_page)
    print user_posts(friend, scroll=30)



