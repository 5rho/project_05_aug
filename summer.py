# 必要なライブラリをインポートします。
import streamlit as st
import pandas as pd
import sqlite3
import uuid
from datetime import date, time
import pydeck as pdk

# SQLiteデータベースファイル名
DB_FILE = "sensor_data.db"

# セッションステートを初期化
if 'submitted_data' not in st.session_state:
    st.session_state.submitted_data = None
if 'save_confirmed' not in st.session_state:
    st.session_state.save_confirmed = False

def init_db():
    """データベースを初期化し、テーブルが存在しない場合は作成します。
       不快指数カラムが存在しない場合は追加します。"""
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS measurements (
                id TEXT PRIMARY KEY,
                lat REAL NOT NULL,
                lon REAL NOT NULL,
                temperature REAL NOT NULL,
                humidity REAL NOT NULL,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                discomfort_index REAL
            );
        """)
        # 不快指数カラムが既存のテーブルにない場合のために追加
        cursor = conn.execute("PRAGMA table_info(measurements);")
        columns = [column[1] for column in cursor.fetchall()]
        if 'discomfort_index' not in columns:
            conn.execute("ALTER TABLE measurements ADD COLUMN discomfort_index REAL;")


def calculate_discomfort_index(temperature, humidity):
    """気温(℃)と相対湿度(%)から不快指数を計算します。
    
    Args:
        temperature (float): 気温 (℃)
        humidity (float): 相対湿度 (%)
    
    Returns:
        float: 不快指数
    """
    # 不快指数の計算式
    # 0.81T + 0.01H(0.99T - 14.3) + 46.3
    di = 0.81 * temperature + 0.01 * humidity * (0.99 * temperature - 14.3) + 46.3
    return round(di, 2)


def save_data(lat, lon, temperature, humidity, measurement_date, measurement_time, discomfort_index):
    """新しいデータをデータベースに保存します。"""
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute(
            "INSERT INTO measurements (id, lat, lon, temperature, humidity, date, time, discomfort_index) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), lat, lon, temperature, humidity, str(measurement_date), str(measurement_time), discomfort_index)
        )

def load_data():
    """データベースからすべてのデータをロードして、pandas DataFrameとして返します。"""
    with sqlite3.connect(DB_FILE) as conn:
        df = pd.read_sql_query(
            "SELECT id, date AS 日付, time AS 時刻, lat AS 緯度, lon AS 経度, temperature AS '温度(℃)', humidity AS '湿度(%)', discomfort_index AS '不快指数' FROM measurements", 
            conn
        )
    return df

def load_data_for_map():
    """pydeck用にデータベースからデータをロードし、元の列名でDataFrameとして返します。"""
    with sqlite3.connect(DB_FILE) as conn:
        df = pd.read_sql_query("SELECT lat, lon, temperature, humidity, discomfort_index FROM measurements", conn)
    # 欠損値がある行を削除し、データが正しく表示されるようにします。
    df = df.dropna()
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
    
    measurement_date = st.date_input('測定日', value=date.today())
    measurement_time = st.time_input('測定時間', value=time(hour=12, minute=0))

    lat_str = st.text_input('緯度 (例: 35.681236)')
    lon_str = st.text_input('経度 (例: 139.767125)')
    
    temperature = st.number_input('温度 (℃)', min_value=-50.0, max_value=100.0, format="%.2f", value=25.0)
    humidity = st.number_input('湿度 (%)', min_value=0.0, max_value=100.0, format="%.2f", value=60.0)
    
    # リアルタイムで不快指数を表示
    try:
        realtime_discomfort_index = calculate_discomfort_index(temperature, humidity)
        st.metric(label="不快指数", value=f"{realtime_discomfort_index:.2f}")
    except (TypeError, ValueError):
        st.metric(label="不快指数", value="---")

    submitted = st.form_submit_button("データを追加")

    if submitted:
        try:
            lat = float(lat_str)
            lon = float(lon_str)

            if not (-90.0 <= lat <= 90.0):
                st.error('緯度は -90.0 から 90.0 の間で入力してください。')
            elif not (-180.0 <= lon <= 180.0):
                st.error('経度は -180.0 から 180.0 の間で入力してください。')
            else:
                # セッションステートに一時的にデータを保存
                st.session_state.submitted_data = {
                    'lat': lat,
                    'lon': lon,
                    'temperature': temperature,
                    'humidity': humidity,
                    'date': measurement_date,
                    'time': measurement_time,
                    'discomfort_index': realtime_discomfort_index
                }
                st.session_state.save_confirmed = True
                st.rerun()
        except ValueError:
            st.error("緯度と経度には半角数字を入力してください。")

# 確認ダイアログの表示
if st.session_state.save_confirmed:
    st.write("---")
    st.write("以下の情報を保存しますか？")
    col1, col2 = st.columns(2)
    with col1:
        if st.button('はい'):
            data_to_save = st.session_state.submitted_data
            save_data(data_to_save['lat'], data_to_save['lon'], data_to_save['temperature'], data_to_save['humidity'], data_to_save['date'], data_to_save['time'], data_to_save['discomfort_index'])
            st.success('データが追加されました！')
            st.session_state.submitted_data = None
            st.session_state.save_confirmed = False
            st.rerun()
    with col2:
        if st.button('いいえ'):
            st.warning('データの保存はキャンセルされました。')
            st.session_state.submitted_data = None
            st.session_state.save_confirmed = False
            st.rerun()

# ---
# ダウンロードボタンの追加
st.markdown("---")
st.write("テーブルのデータをCSV形式でダウンロードできます。")
data_df = load_data()
if not data_df.empty:
    csv_data = data_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="CSVファイルをダウンロード",
        data=csv_data,
        file_name='sensor_data.csv',
        mime='text/csv',
    )
else:
    st.info('ダウンロードするデータがありません。')

# ---
# 地図にデータを表示します。
st.header('測定位置の地図')
# pydeckを使用するように変更
pydeck_data_df = load_data_for_map()
if not pydeck_data_df.empty:
    st.info('地図上の点をタップすると、詳細情報が表示されます。')
    
    # データを元に中心点とズームレベルを計算
    center_lat = pydeck_data_df['lat'].mean()
    center_lon = pydeck_data_df['lon'].mean()
    
    # 緯度と経度の最大差を計算してズームレベルを調整
    max_lat_diff = pydeck_data_df['lat'].max() - pydeck_data_df['lat'].min()
    max_lon_diff = pydeck_data_df['lon'].max() - pydeck_data_df['lon'].min()
    
    zoom_level = 12
    if max_lat_diff > 1 or max_lon_diff > 1:
        zoom_level = 5
    elif max_lat_diff > 0.1 or max_lon_diff > 0.1:
        zoom_level = 8
    
    # pydeckのビューポートを設定
    view_state = pdk.ViewState(
        latitude=center_lat,
        longitude=center_lon,
        zoom=zoom_level,
        pitch=0
    )
    
    # ScatterplotLayerでプロットを作成
    scatter_layer = pdk.Layer(
        'ScatterplotLayer',
        data=pydeck_data_df,
        get_position='[lon, lat]',
        get_color='[200, 30, 0, 160]',
        get_radius=20,
        pickable=True, # ツールチップを有効にするために必須
    )
    
    # 地図のレンダリング
    r = pdk.Deck(
        layers=[scatter_layer],
        initial_view_state=view_state,
        tooltip={
            "html": "<b>温度:</b> {temperature:.2f} ℃<br/><b>湿度:</b> {humidity:.2f} %<br/><b>不快指数:</b> {discomfort_index:.2f}",
            "style": {
                "color": "white"
            }
        },
    )
    
    st.pydeck_chart(r, use_container_width=True)

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
