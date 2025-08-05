import sqlite3
import pandas as pd

conn = sqlite3.connect("sensor_data.db")
df = pd.read_sql_query("SELECT * FROM your_table", conn)



"""
df['new_column'] = df.apply(
    lambda row: row['colA'] * row['colB'] if pd.isna(row['new_column']) else row['new_column'], 
    axis=1
)

    di = 0.81 * temperature + 0.01 * humidity * (0.99 * temperature - 14.3) + 46.3
    return round(di, 2)
"""



df['discomfort_index'] = df.apply(
    lambda row: round(
        0.81 * row['temperature'] + 0.01 * row['humidity'] * (0.99 * row['temperature'] - 14.3) + 46.3,
        2
    ) if pd.isna(row['discomfort_index']) else row['discomfort_index'], 
    axis=1
)

df.to_sql("your_table", conn, if_exists="replace", index=False)
conn.close()

