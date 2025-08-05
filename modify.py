import os
import sqlite3
import pandas as pd

db_path = os.path.abspath("sensor_data.db")
print("接続中のDBパス:", db_path)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("DB内テーブル一覧:", cursor.fetchall())

if not tables:
    print("シートがファイルにないよ")
    conn.close()
    exit()

print("db一覧", tables)
table_name = tables[0][0]  # 最初のテーブル名を取得
print(f"使用するテーブル名: {table_name}")

df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
print("読み込んだデータの一部:")
print(df.head())


if 'temperature' in df.columns and 'humidity' in df.columns:
    df['discomfort_index'] = df.apply(
        lambda row: round(
            0.81 * row['temperature'] + 0.01 * row['humidity'] * (0.99 * row['temperature'] - 14.3) + 46.3,
            2
        ) if pd.isna(row['discomfort_index']) else row['discomfort_index'], 
        axis=1
    )
    print(ok,おわった)
else:
    print("temperature または humidity カラムが存在しません。")

new_table_name = f"{table_name}_with_index"
df.to_sql(new_table_name, conn, if_exists="replace", index=False)
print(f"加工済データを新しいテーブル '{new_table_name}' として保存しました。")

conn.close()

