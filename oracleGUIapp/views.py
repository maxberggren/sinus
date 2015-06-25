#!/usr/bin/python
# -*- coding: utf-8 -*-

from oracleGUIapp import app
from flask import Flask, jsonify, make_response, request, render_template, redirect, url_for
from werkzeug import secure_filename

questions = [(u'Sluddrar och pratar du grötigt?', 
              u'Detta är en undertext som _förklarar mer_.', 
              ['Ja', 'Nej']),
              
             (u'Fara eller åka?',
              u'Använder du ibland fara som i _vi skulle vara till farmor_?',
              ['Jo', 'Nej'])]

@app.route('/oracle/', methods = ['GET', 'POST'])
@app.route('/oracle', methods = ['GET', 'POST'])
def oracle():
    return render_template("index.html", questions=questions, n_questions=len(questions))

    