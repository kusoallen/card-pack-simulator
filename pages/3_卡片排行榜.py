import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="抽卡排行榜", layout="wide")

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
        legend_count = df[df["稀有度"] == "傳說"].shape[0]
        summary.append({
            "學號": ws.title,
            "總抽卡數": total_cards,
            "傳說卡數": legend_count
        })

    if summary:
        summary_df = pd.DataFrame(summary)
        summary_df = summary_df.sort_values(by=["傳說卡數", "總抽卡數"], ascending=False).reset_index(drop=True)
        st.dataframe(summary_df)
    else:
        st.info("目前沒有任何抽卡紀錄。")
