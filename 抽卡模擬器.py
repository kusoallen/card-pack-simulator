# ✅ 優等卡牌抽卡模擬器（含學生抽卡限制版）
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import random
from datetime import datetime
import os
from PIL import Image
import time
import base64
import zipfile
import io
import pytz
import gspread
from google.oauth2.service_account import Credentials

SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(st.secrets["gspread_json"], scopes=SCOPE)
client = gspread.authorize(creds)

SHEET_URL = "https://docs.google.com/spreadsheets/d/1-uKCq-8w_c3EUItPKV9NnEVkRAQiC5I5vW2BZr8NFfg/edit"
sheet = client.open_by_url(SHEET_URL)

st.set_page_config(page_title="優等卡牌 抽卡模擬器", layout="wide")

BACKGROUND_IMAGE_PATH = "background.png"
if os.path.exists(BACKGROUND_IMAGE_PATH):
    with open(BACKGROUND_IMAGE_PATH, "rb") as f:
        bg_bytes = f.read()
        bg_base64 = base64.b64encode(bg_bytes).decode()
        page_bg = f"""
        <style>
        [data-testid="stApp"] {{
            background-image: url("data:image/jpg;base64,{bg_base64}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}
        </style>
        """
        st.markdown(page_bg, unsafe_allow_html=True)

cards_df = pd.read_excel("優等卡牌 的副本.xlsx", sheet_name="工作表4")
cards_df = cards_df[cards_df["類型"].isin(["學生卡", "知識卡", "武器卡"])]

# 🔍 抓取該學生已抽過的卡片數量
def get_student_drawn_counts(student_id):
    try:
        worksheet = sheet.worksheet(student_id)
        records = worksheet.get_all_records()
    except:
        return {}

    counts = {}
    for record in records:
        key = (record["卡名"], record["稀有度"])
        counts[key] = counts.get(key, 0) + 1
    return counts

# 🧮 建立符合該學生限制的卡池
def build_limited_card_pool(student_id):
    drawn_counts = get_student_drawn_counts(student_id)
    max_allowed = {"普通": 2, "稀有": 2, "史詩": 2, "傳說": 1}
    limited_pool = []
    for _, row in cards_df.iterrows():
        name = row["名稱"]
        rarity = row["稀有度"]
        key = (name, rarity)
        current_count = drawn_counts.get(key, 0)
        remaining = max(0, max_allowed.get(rarity, 0) - current_count)
        for _ in range(remaining):
            limited_pool.append((name, rarity))
    return limited_pool

# 🎴 抽卡邏輯（含限制）
def draw_single(student_id):
    pool = build_limited_card_pool(student_id)
    if not pool:
        st.warning("你已經抽滿所有卡片了！")
        return pd.DataFrame(columns=["卡名", "稀有度"])
    drawn = random.sample(pool, 1)
    return pd.DataFrame(drawn, columns=["卡名", "稀有度"])

def draw_pack(student_id):
    pool = build_limited_card_pool(student_id)
    if len(pool) < 5:
        drawn = random.choices(pool, k=5)
    else:
        drawn = random.sample(pool, 5)
    return pd.DataFrame(drawn, columns=["卡名", "稀有度"])

def simulate_draws(student_id, n_packs=10):
    all_packs = []
    for _ in range(n_packs):
        pack = draw_pack(student_id)
        all_packs.append(pack)
    return pd.concat(all_packs, ignore_index=True)

# ✅ 儲存抽卡紀錄（含 Google Sheet）
def save_draw_result(result_df, student_id):
    taipei = pytz.timezone("Asia/Taipei")
    now_tw = datetime.now(taipei).strftime("%Y-%m-%d %H:%M:%S")
    result_df.insert(0, "學號", student_id)
    result_df["抽取時間"] = now_tw

    folder = "抽卡紀錄"
    os.makedirs(folder, exist_ok=True)
    timestamp = datetime.now(taipei).strftime("%Y%m%d_%H%M%S")
    filename = f"{folder}/抽卡紀錄_{student_id}_{timestamp}.xlsx"
    result_df.to_excel(filename, index=False)

    write_to_google_sheet(result_df, student_id)
    return filename

def write_to_google_sheet(result_df, student_id):
    taipei = pytz.timezone("Asia/Taipei")
    now = datetime.now(taipei).strftime("%Y-%m-%d %H:%M:%S")
    sheet_titles = [ws.title for ws in sheet.worksheets()]

    if student_id not in sheet_titles:
        worksheet = sheet.add_worksheet(title=student_id, rows=1000, cols=10)
        worksheet.append_row(["學號", "卡名", "稀有度", "抽取時間"])
    else:
        worksheet = sheet.worksheet(student_id)

    for _, row in result_df.iterrows():
        worksheet.append_row([
            student_id,
            row["卡名"],
            row["稀有度"],
            now
        ])

# --- Streamlit 前端 ---
st.title("優等卡牌 抽卡模擬器")

# 背景音樂播放器
music_path = "sounds/bgm.mp3"
if os.path.exists(music_path):
    with open(music_path, "rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode()
        st.markdown(
            f"""
            <p>🎵 背景音樂：</p>
            <audio controls loop>
                <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
            """,
            unsafe_allow_html=True
        )

# 密碼保護
st.subheader("🔐 請先輸入密碼進入抽卡區")
password = st.text_input("密碼：", type="password", key="card_draw_pwd")
correct_password = "8341"
if password != correct_password:
    st.warning("請輸入正確密碼以開始抽卡。")
    st.stop()

# 學號輸入
student_id = st.text_input("請輸入學號：")
mode = st.radio("請選擇抽卡模式：", ["抽幾包卡（每包5張）", "單抽（1張卡）"])
animate = st.checkbox("啟用開包動畫模式", value=True)

if student_id:
    if mode == "抽幾包卡（每包5張）":
        packs = st.number_input("請輸入要抽幾包卡（每包5張）", min_value=1, max_value=5, value=1)
        if st.button("開始抽卡！"):
            result = simulate_draws(student_id, packs)
            st.success(f"已抽出 {packs} 包，共 {len(result)} 張卡！")
            saved_file = save_draw_result(result, student_id)
            st.info(f"抽卡紀錄已儲存至：{saved_file}")
            st.dataframe(result)
    else:
        if st.button("立即單抽！🎯"):
            result = draw_single(student_id)
            st.success("你抽到了 1 張卡片！")
            saved_file = save_draw_result(result, student_id)
            st.info(f"抽卡紀錄已儲存至：{saved_file}")
            st.dataframe(result)
else:
    st.warning("請先輸入學號才能進行抽卡。")
