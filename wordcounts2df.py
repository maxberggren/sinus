from __future__ import division
from sqlalchemy import create_engine
import pandas as pd
import config as c

engine = create_engine(c.LOCATIONDB, echo=False)

check_region = "skaune"
df = pd.read_sql_query('SELECT * FROM wordcounts '
                       'WHERE region = "country" '
                       'or region = "' + check_region + '"' 
                       'and frequency > 300', 
                       engine, index_col='id')

#df = df[df['frequency'] > 10]

def rel_frq(values):
    if len(values) == 2:
        return (values.values[1] - values.values[0])/values.values[0]
    else: 
        return 0.0

grouped_count = df.groupby("token").frequency.agg(rel_frq)

i = 0
for index, value in grouped_count.order(ascending=False).iteritems():
    print index.decode('latin-1').encode('utf-8'), value
    if value < 0.5:
        break
