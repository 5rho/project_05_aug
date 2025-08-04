# 必要なライブラリをインポートします。
import streamlit as st
import pandas as pd
import sqlite3
import uuid
from datetime import date, time

# SQLiteデータベースファイル名
DB_FILE = "sensor_data.db"

def init_db():
    """データベースを初期化し、テーブルが存在しない場合は作成します。"""
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS measurements (
                id TEXT PRIMARY KEY,
                lat REAL NOT NULL,
                lon REAL NOT NULL,
                temperature REAL NOT NULL,
                humidity REAL NOT NULL,
                date TEXT NOT NULL,
                time TEXT NOT NULL
            );
        """)

def save_data(lat, lon, temperature, humidity, measurement_date, measurement_time):
    """新しいデータをデータベースに保存します。"""
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute(
            "INSERT INTO measurements (id, lat, lon, temperature, humidity, date, time) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), lat, lon, temperature, humidity, str(measurement_date), str(measurement_time))
        )

def load_data():
    """データベースからすべてのデータをロードして、pandas DataFrameとして返します。"""
    with sqlite3.connect(DB_FILE) as conn:
        df = pd.read_sql_query("SELECT id, date AS 日付, time AS 時刻, lat AS 緯度, lon AS 経度, temperature AS '温度(℃)', humidity AS '湿度(%)' FROM measurements", conn)
    return df

# アプリの起動時にデータベースを初期化
init_db()

# Streamlitアプリのタイトルを設定します。
st.title('センサーデータ可視化アプリ')
st.write('Google マップからコピーした座標を含め、温度、湿度、測定位置のデータを入力し、テーブルと地図に表示します。')
st.write('データは自動的に保存され、再起動後も保持されます。')

# ---
# データ入力用のUIコンポーネントを配置します。
st.header('データの入力')

# Google マップからのコピーを想定した入力ヒント
st.info('Google マップのピンをクリックすると表示される座標（例: 35.681236, 139.767125）をコピーして、緯度と経度の入力欄にペーストしてください。')

with st.form("input_form"):
    st.write("新しい測定データを入力してください。")
    
    # 日付と時刻の入力フィールドを追加
    measurement_date = st.date_input('測定日', value=date.today())
    measurement_time = st.time_input('測定時間', value=time(hour=12, minute=0))

    # 緯度と経度をテキスト入力に変更し、ユーザーがコピペしやすいようにします。
    lat_str = st.text_input('緯度 (例: 35.681236)')
    lon_str = st.text_input('経度 (例: 139.767125)')
    
    # 温度、湿度の入力フィールドはそのままnumber_inputを使用します。
    temperature = st.number_input('温度 (℃)', min_value=-50.0, max_value=100.0, format="%.2f", value=25.0)
    humidity = st.number_input('湿度 (%)', min_value=0.0, max_value=100.0, format="%.2f", value=60.0)
    
    # データを追加するボタン
    submitted = st.form_submit_button("データを追加")

    if submitted:
        try:
            # 入力された文字列をfloatに変換します。
            lat = float(lat_str)
            lon = float(lon_str)

            # 変換した値の範囲をチェックします。
            if not (-90.0 <= lat <= 90.0):
                st.error('緯度は -90.0 から 90.0 の間で入力してください。')
            elif not (-180.0 <= lon <= 180.0):
                st.error('経度は -180.0 から 180.0 の間で入力してください。')
            else:
                # データをSQLiteデータベースに保存します。
                save_data(lat, lon, temperature, humidity, measurement_date, measurement_time)
                st.success('データが追加されました！')
                # データを再度ロードしてUIを更新します。
                st.session_state['data'] = load_data()
        except ValueError:
            st.error("緯度と経度には半角数字を入力してください。")

# ---
# データベースからデータをロードします。
data_df = load_data()

# テーブルにデータを表示します。
st.header('記録データ一覧')
if not data_df.empty:
    # id列をインデックスとして表示し、見やすくします。
    st.dataframe(data_df.set_index('id'))
    # --- ダウンロードボタンの追加 ---
    st.markdown("---")
    st.write("テーブルのデータをCSV形式でダウンロードできます。")
    # DataFrameをCSV形式に変換
    csv_data = data_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="CSVファイルをダウンロード",
        data=csv_data,
        file_name='sensor_data.csv',
        mime='text/csv',
    )
else:
    st.info('まだデータがありません。')

# ---
# 地図にデータを表示します。
st.header('測定位置の地図')
if not data_df.empty:
    # st.mapは緯度と経度の列名が'lat'と'lon'であることを要求します。
    # 既存のデータフレームをコピーして列名を変更します。
    map_data = data_df[['緯度', '経度']].rename(columns={'緯度': 'lat', '経度': 'lon'})

    # データを元に中心点とズームレベルを計算
    center_lat = map_data['lat'].mean()
    center_lon = map_data['lon'].mean()
    
    # 緯度と経度の最大差を計算してズームレベルを調整
    # このロジックは、データの広がりを考慮して最適なズームレベルを推測します。
    max_lat_diff = map_data['lat'].max() - map_data['lat'].min()
    max_lon_diff = map_data['lon'].max() - map_data['lon'].min()
    
    zoom_level = 12
    if max_lat_diff > 1 or max_lon_diff > 1:
        zoom_level = 5
    elif max_lat_diff > 0.1 or max_lon_diff > 0.1:
        zoom_level = 8
    
    st.map(map_data, zoom=zoom_level, use_container_width=True)
else:
    st.info('地図に表示するデータがありません。')

st.markdown("""
<style>
    /* 全体的なレイアウト調整 */
    section.main > div {
        max-width: 900px;
        padding-left: 2rem;
        padding-right: 2rem;
    }
</style>
""", unsafe_allow_html=True)
