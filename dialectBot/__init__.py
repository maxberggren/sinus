#!/usr/bin/python
# -*- coding: utf-8 -*- 
#import matplotlib
#matplotlib.use('Agg')
from flask import Flask, jsonify, make_response, request
import re

app = Flask(__name__)

@app.template_filter('italic')
def italic(s):
    my_regex = re.compile(r"\*\*(.+?)\*\*")
    return my_regex.sub(r'<em>\1</em>', s)

from dialectBot import views