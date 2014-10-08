#!/usr/bin/python
# -*- coding: utf-8 -*- 
from flask import Flask, jsonify, make_response, request
from textLoc26 import *

app = Flask(__name__)

from flaskapp import views