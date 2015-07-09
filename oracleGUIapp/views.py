#!/usr/bin/python
# -*- coding: utf-8 -*-

from oracleGUIapp import app
from flask import Flask, jsonify, make_response, request, render_template, redirect, url_for
from werkzeug import secure_filename

questions = [{'q': u'Sluddrar och pratar du grötigt?', 
              'sq': u'Detta är en undertext som **förklarar mer**.', 
              'alt': ['Ja', 'Nej'], 
              'id': 1},
              
             {'q': u'Fara eller åka?',
              'sq': u'Fyll i följande mening: **vi skulle...**',
              'alt': ['...fara till farmor', u'...åka till farmor'], 
              'id': 2},
              
             {'q': u'Polisen?',
              'sq': u'Vilket av följade använder du oftast för att tala om polisen?',
              'alt': [u'Bängen', 'Snuten', u'Farbror blå'], 
              'id': 3}]

@app.route('/oracle/', methods = ['GET', 'POST'])
@app.route('/oracle', methods = ['GET', 'POST'])
def oracle():
    return render_template("index.html", questions=questions, n_questions=len(questions))

    