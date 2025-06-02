import sqlite3
import pandas as pd

conn = sqlite3.connect('amostras.db')
df = pd.read_sql_query("SELECT * FROM amostras", conn)
conn.close()

print(df)
