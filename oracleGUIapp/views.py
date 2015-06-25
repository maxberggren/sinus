#!/usr/bin/python
# -*- coding: utf-8 -*-

from oracleGUIapp import app
from flask import Flask, jsonify, make_response, request, render_template, redirect, url_for
from werkzeug import secure_filename

@app.route('/oracle/', methods = ['GET', 'POST'])
@app.route('/oracle', methods = ['GET', 'POST'])
def oracle():
    print "wat"
    return render_template("index.html")

    