from __future__ import division
from sqlalchemy import create_engine
import pandas as pd
import config as c

pd.set_printoptions(max_rows=10000)

engine = create_engine(c.LOCATIONDB, echo=False)

df = pd.read_sql_query('SELECT * FROM wordcounts', engine, index_col='id')



print df.head()

def rel_error(values):
    if len(values) == 2:
        return abs((values.values[0] - values.values[1])/values.values[0])
    else: 
        return 0.0

grouped_count = df.groupby("token").frequency.agg(rel_error)

print grouped_count.order(ascending=False)