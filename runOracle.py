#!/usr/bin/python
# -*- coding: utf-8 -*- 
import matplotlib  
matplotlib.use('Agg')
from oracleGUIapp import app
from flask.ext.markdown import Markdown
md = Markdown(app, extensions=['fenced_code'])

app.debug = True
app.run(host='0.0.0.0', port=5009)