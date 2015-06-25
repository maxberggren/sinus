#!/usr/bin/python
# -*- coding: utf-8 -*- 
import matplotlib  
matplotlib.use('Agg')
from oracleGUIapp import app
import re

@app.template_filter('italic')
def italic(s):
    return re.sub('\*{2}(.+)\*{2}', '<i>\\1</i>', s)

app.debug = True
app.run(host='0.0.0.0', port=5009)