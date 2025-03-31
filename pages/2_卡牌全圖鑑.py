import streamlit as st
import pandas as pd
import os
from PIL import Image
import base64

st.set_page_config(page_title="卡牌全圖鑑")
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

st.title("🃏 優等卡牌全圖鑑")

# 🔍 搜尋與篩選
col1, col2 = st.columns([2, 1])
with col1:
    search_name = st.text_input("🔍 搜尋卡名：")
with col2:
    rarity_filter = st.selectbox("🌟 篩選稀有度：", ["全部"] + sorted(cards_df["稀有度"].unique()))

# 套用搜尋與篩選
if search_name:
    cards_df = cards_df[cards_df["卡名"].str.contains(search_name, case=False, na=False)]
if rarity_filter != "全部":
    cards_df = cards_df[cards_df["稀有度"] == rarity_filter]

# 載入卡牌資料
cards_df = pd.read_excel("優等卡牌 的副本.xlsx", sheet_name="工作表4")
card_folder = "card_images"

# 過濾主卡（學生、知識、武器）
cards_df = cards_df[cards_df["類型"].isin(["學生卡", "知識卡", "武器卡"])]
cards_df = cards_df.sort_values(by=["稀有度", "名稱"])

# 顯示所有卡片
st.markdown("""
<style>
.card-gallery {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 20px;
    justify-items: center;
    padding-top: 20px;
}
.card-block {
    text-align: center;
    background: rgba(255,255,255,0.05);
    padding: 10px;
    border-radius: 12px;
    box-shadow: 0 0 6px rgba(255,255,255,0.1);
}
.card-block img {
    border-radius: 12px;
    width: 100%;
    max-height: 260px;
    object-fit: contain;
}
.card-block .label {
    margin-top: 5px;
    font-weight: bold;
    color: gold;
}
</style>
""", unsafe_allow_html=True)

html = "<div class='card-gallery'>"

for _, row in cards_df.iterrows():
    name = row["卡名"]
    rarity = row["稀有度"]
    img_path = None
    for ext in [".png", ".jpg", ".jpeg", ".webp"]:
        try_path = os.path.join(card_folder, f"{name}{ext}")
        if os.path.exists(try_path):
            img_path = try_path
            break

    if img_path:
        with open(img_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode()
        html += f"""
        <div class='card-block'>
            <img src='data:image/png;base64,{img_b64}'>
            <div class='label'>{name}（{rarity}）</div>
        </div>
        """

html += "</div>"
st.components.v1.html(html, height=1000, scrolling=True)