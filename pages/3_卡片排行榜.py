import os
from PIL import Image
from io import BytesIO
import base64
import zipfile

import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="抽卡排行榜", layout="wide")

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


# Google Sheet 授權與連結
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(st.secrets["gspread_json"], scopes=SCOPE)
client = gspread.authorize(creds)

SHEET_URL = "https://docs.google.com/spreadsheets/d/1-uKCq-8w_c3EUItPKV9NnEVkRAQiC5I5vW2BZr8NFfg/edit"
sheet = client.open_by_url(SHEET_URL)

st.title("🏆 優等卡牌 抽卡排行榜")

if st.button("載入排行榜"):
    all_worksheets = sheet.worksheets()
    summary = []
    for ws in all_worksheets:
        if ws.title == "進度表":
            continue
        records = ws.get_all_records()
        df = pd.DataFrame(records)
        total_cards = len(df)
        if "稀有度" in df.columns:
            legend_count = df[df["稀有度"] == "傳說"].shape[0]
        else:
            legend_count = 0
        if "稀有度" in df.columns:
            epic_count = df[df["稀有度"] == "史詩"].shape[0]
            rare_count = df[df["稀有度"] == "稀有"].shape[0]
            normal_count = df[df["稀有度"] == "普通"].shape[0]
            unique_cards = df["卡名"].nunique() if "卡名" in df.columns else 0
        else:
            epic_count = rare_count = normal_count = unique_cards = 0

        summary.append({
            "學號": ws.title,
            "總抽卡數": total_cards,
            "卡片種類數": unique_cards,
            "傳說卡數": legend_count,
            "史詩卡數": epic_count,
            "稀有卡數": rare_count,
            "普通卡數": normal_count
        })

    if summary:
        summary_df = pd.DataFrame(summary)
        summary_df = summary_df.sort_values(by=["傳說卡數", "總抽卡數"], ascending=False).reset_index(drop=True)

        # 名次箭頭比較資料來源：昨日名次
        try:
            rank_ws = sheet.worksheet("排行榜記錄")
        except:
            rank_ws = sheet.add_worksheet(title="排行榜記錄", rows=1000, cols=10)
            rank_ws.append_row(["日期", "學號", "名次"])

        today_str = datetime.now().strftime("%Y-%m-%d")
        yesterday_str = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        past_records = rank_ws.get_all_records()
        yesterday_ranks = {
            r["學號"]: int(r["名次"]) for r in past_records if r["日期"] == yesterday_str
        }

        # 插入名次與箭頭
        badges = ["🥇", "🥈", "🥉"]
        rank_col = []
        for i, row in summary_df.iterrows():
            curr_rank = i + 1
            student_id = row["學號"]
            prev_rank = yesterday_ranks.get(student_id, curr_rank)
            if prev_rank > curr_rank:
                arrow = " 🔺"
            elif prev_rank < curr_rank:
                arrow = " 🔻"
            else:
                arrow = " ⏺"
            badge = badges[i] if i < 3 else str(curr_rank)
            rank_col.append(badge + arrow)

            # ✅ 自動寫入今日名次紀錄（避免重複）
            already_logged = any(
                r["日期"] == today_str and r["學號"] == student_id for r in past_records
            )
            if not already_logged:
                rank_ws.append_row([today_str, student_id, curr_rank])

        summary_df.insert(0, "名次", rank_col)
        summary_df.insert(0, "名次", [badges[i] if i < 3 else f"{i+1}" for i in range(len(summary_df))])
        # 使用樣式讓前三名整列變色
        def highlight_top_rows(row):
            if row.name == 0:
                return ["background-color: gold"] * len(row)
            elif row.name == 1:
                return ["background-color: silver"] * len(row)
            elif row.name == 2:
                return ["background-color: #cd7f32"] * len(row)  # 銅色
            else:
                return [""] * len(row)

        styled_df = summary_df.style.apply(highlight_top_rows, axis=1)
        st.dataframe(styled_df, use_container_width=True)
    else:
        st.info("目前沒有任何抽卡紀錄。")

