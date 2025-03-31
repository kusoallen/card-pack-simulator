import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="查詢學生紀錄")
# ✅ 背景圖片設定
BACKGROUND_IMAGE_PATH = "background.png"  # 可改成 background.png 等
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

query_id = st.text_input("請輸入要查詢的學號：", key="query")
if query_id:
    folder = "抽卡紀錄"
    matched_files = []
    if os.path.exists(folder):
        matched_files = [f for f in os.listdir(folder) if f.startswith(f"抽卡紀錄_{query_id}_") and f.endswith(".xlsx")]
    if matched_files:
        all_records = []
        for file in matched_files:
            df = pd.read_excel(os.path.join(folder, file))
            all_records.append(df)
        combined = pd.concat(all_records, ignore_index=True)

        # 統計表格
        summary = combined.groupby(["卡名", "稀有度"]).size().reset_index(name="抽中次數")
        summary = summary.sort_values("抽中次數", ascending=False)

        st.subheader("📋 抽過的卡片統計：")
        st.dataframe(summary, use_container_width=True)

        st.subheader("📑 抽卡紀錄明細：")
        st.dataframe(combined, use_container_width=True)
    else:
        st.info("查無此學號的紀錄。")