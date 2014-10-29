#!/usr/bin/python
# -*- coding: utf-8 -*- 
import matplotlib  
matplotlib.use('Agg')
from flaskapp import app
app.debug = False
app.run(host='0.0.0.0', port=5000)