import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import base64
import os

st.set_page_config(page_title="抽卡紀錄查詢")

# ✅ 背景圖片設定
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

st.title("📚 查詢學生抽卡紀錄")

# ✅ Google Sheet 授權連結
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(st.secrets["gspread_json"], scopes=SCOPE)
client = gspread.authorize(creds)

# ✅ 連接到指定 Google Sheet
SHEET_URL = "https://docs.google.com/spreadsheets/d/1-uKCq-8w_c3EUItPKV9NnEVkRAQiC5I5vW2BZr8NFfg/edit"
sheet = client.open_by_url(SHEET_URL)

query_id = st.text_input("請輸入要查詢的學號：", key="query")
if query_id:
    try:
        worksheet = sheet.worksheet(query_id)
        records = worksheet.get_all_records()
        if records:
            df = pd.DataFrame(records)
            st.subheader("📋 抽過的卡片統計：")
            if "卡名" in df.columns and "稀有度" in df.columns:
                summary = df.groupby(["卡名", "稀有度"]).size().reset_index(name="抽中次數")
                summary = summary.sort_values("抽中次數", ascending=False)
                st.dataframe(summary, use_container_width=True)
            st.subheader("📑 抽卡紀錄明細：")
            st.dataframe(df, use_container_width=True)
        else:
            st.info("尚無抽卡紀錄。")
    except:
        st.warning("找不到該學號的紀錄，請確認是否輸入正確或已完成抽卡。")