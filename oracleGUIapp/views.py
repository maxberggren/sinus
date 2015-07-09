#!/usr/bin/python
# -*- coding: utf-8 -*-

from oracleGUIapp import app
from flask import Flask, jsonify, make_response, request, render_template, redirect, url_for
from werkzeug import secure_filename

questions = [{'question': u'Sluddrar och pratar du grötigt?', 
              'explanation': u'Detta är en undertext som **förklarar mer**.', 
              'answers': ['Ja', 'Nej'], 
              'id': 1},
              
             {'question': u'Fara eller åka?',
              'explanation': u'Fyll i följande mening: **vi skulle...**',
              'answers': ['...fara till farmor', u'...åka till farmor'], 
              'id': 2},
              
             {'question': u'Polisen?',
              'explanation': u'Vilket av följade använder du oftast för att tala om polisen?',
              'answers': [u'Bängen', 'Snuten', u'Farbror blå'], 
              'id': 3}]

@app.route('/oracle/', methods = ['GET', 'POST'])
@app.route('/oracle', methods = ['GET', 'POST'])
def oracle():
    return render_template("index.html", questions=questions, n_questions=len(questions))


@app.route('/oracle/predict', methods=['POST'])
def predict(): 
    x = request.json['uname']
                           
    return jsonify( { 'city1': x )

    