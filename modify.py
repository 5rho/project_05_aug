import os
db_path = os.path.abspath("sensor_data.db")
print("接続中のDBパス:", db_path)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
print("DB内テーブル一覧:", cursor.fetchall())



#データベース確認
import sqlite3
import pandas as pd
conn = sqlite3.connect("sensor_data.db")  # ← 実際のDBファイル名に置き換えてください
df = pd.read_sql_query("SELECT * FROM measurements", conn)
print(df.head())  # 中身を確認




import sqlite3
import pandas as pd

conn = sqlite3.connect("sensor_data.db")
df = pd.read_sql_query("SELECT * FROM sensor_measurements", conn)






df['discomfort_index'] = df.apply(
    lambda row: round(
        0.81 * row['temperature'] + 0.01 * row['humidity'] * (0.99 * row['temperature'] - 14.3) + 46.3,
        2
    ) if pd.isna(row['discomfort_index']) else row['discomfort_index'], 
    axis=1
)

df.to_sql("your_table", conn, if_exists="replace", index=False)
conn.close()

