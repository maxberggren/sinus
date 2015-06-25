#!/usr/bin/python
# -*- coding: utf-8 -*- 
from flask import Flask, jsonify, make_response, request

app = Flask(__name__)

from oracleGUIapp import views