import sqlite3
import pandas as pd

conn = sqlite3.connect("sensor_data.db")
df = pd.read_sql_query("SELECT * FROM your_table", conn)

df['new_column'] = df.apply(
    lambda row: row['colA'] * row['colB'] if pd.isna(row['new_column']) else row['new_column'], 
    axis=1
)

df.to_sql("your_table", conn, if_exists="replace", index=False)
conn.close()
