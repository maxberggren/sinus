#!/usr/bin/python
# -*- coding: utf-8 -*-
import matplotlib
matplotlib.use('Agg')
from oracleGUIapp import app
import re

@app.template_filter('italic')
def italic(s):
    my_regex = re.compile(r"\*\*(.+?)\*\*")
    return my_regex.sub(r'<em>\\1</em>', s)

app.debug = True
app.run(host='0.0.0.0', port=5011)
