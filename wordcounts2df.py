from sqlalchemy import create_engine
import pandas as pd
import config as c

engine = create_engine(c.LOCATIONDB, echo=False)

df = pd.read_sql_query('SELECT * FROM wordcounts', engine, index_col='id')

print df.head()