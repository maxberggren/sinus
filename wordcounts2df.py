from __future__ import division
from sqlalchemy import create_engine
import pandas as pd
import config as c

engine = create_engine(c.LOCATIONDB, echo=False)

df = pd.read_sql_query('SELECT * FROM wordcounts', engine, index_col='id')

print df.head()

def rel_error(values):
    if len(values) == 2:
        return abs((values[0] - values[1])/values[0])

grouped_count = df.groupby("token").frequency.agg(rel_error)

print grouped_count.head()