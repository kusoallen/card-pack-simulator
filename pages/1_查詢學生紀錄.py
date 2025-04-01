import streamlit as st
import pandas as pd
import os
import io
import zipfile
import base64
from datetime import datetime

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


# 📦 一鍵打包下載：每位學號合併為一份 Excel
import pytz  # 加入台灣時區

with st.expander("📥 匯出每位學生的合併抽卡紀錄 (ZIP)"):
    folder = "抽卡紀錄"
    if os.path.exists(folder):
        files = [f for f in os.listdir(folder) if f.endswith(".xlsx") and f.startswith("抽卡紀錄_")]
        student_groups = {}

        # 分學號彙整檔案
        for file in files:
            parts = file.replace(".xlsx", "").split("_")
            if len(parts) >= 3:
                student_id = parts[1]
                student_groups.setdefault(student_id, []).append(file)

        if student_groups:
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zipf:
                for sid, file_list in student_groups.items():
                    all_records = []
                    for f in file_list:
                        try:
                            df = pd.read_excel(os.path.join(folder, f), sheet_name=0)
                            if not df.empty:
                                all_records.append(df)
                        except Exception as e:
                            st.warning(f"{f} 無法讀取，已略過：{e}")
                    if all_records:
                        combined = pd.concat(all_records, ignore_index=True)
                        if "抽取時間" not in combined.columns:
                            taipei = pytz.timezone("Asia/Taipei")
                            now_tw = datetime.now(taipei).strftime("%Y-%m-%d %H:%M:%S")
                            combined["抽取時間"] = now_tw
                        excel_bytes = io.BytesIO()
                        combined.to_excel(excel_bytes, index=False)
                        excel_bytes.seek(0)
                        zipf.writestr(f"{sid}.xlsx", excel_bytes.read())

            zip_buffer.seek(0)
            st.download_button(
                "📦 下載每位學生合併紀錄 (ZIP)",
                data=zip_buffer,
                file_name="所有學生抽卡紀錄.zip",
                mime="application/zip"
            )
        else:
            st.info("目前尚無任何 Excel 紀錄可下載。")
    else:
        st.info("尚未建立抽卡紀錄資料夾。請先執行一次抽卡。")
