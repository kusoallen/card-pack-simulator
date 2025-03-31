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

# 載入卡牌資料
cards_df = pd.read_excel("優等卡牌 的副本.xlsx", sheet_name="工作表4")
card_folder = "card_images"

# 過濾主卡（學生、知識、武器）
cards_df = cards_df[cards_df["類型"].isin(["學生卡", "知識卡", "武器卡"])]
cards_df = cards_df.sort_values(by=["稀有度", "名稱"])

# 🔍 搜尋與篩選功能
with st.sidebar:
    st.header("🔎 搜尋與篩選")
    name_query = st.text_input("卡名關鍵字：")
    rarities = sorted([r for r in cards_df["稀有度"].dropna().unique() if isinstance(r, str)])
    rarity_choice = st.selectbox("選擇稀有度：", ["全部"] + rarities)
    types = sorted(cards_df["類型"].unique())
    type_choice = st.multiselect("卡牌類型：", options=types, default=types)

# 根據篩選條件過濾卡牌
if name_query:
    cards_df = cards_df[cards_df["名稱"].str.contains(name_query, case=False, na=False)]
if rarity_choice != "全部":
    cards_df = cards_df[cards_df["稀有度"] == rarity_choice]
cards_df = cards_df[cards_df["類型"].isin(type_choice)]

# 顯示卡片區塊
st.markdown("""
<style>
.card-gallery {
    display: grid;
    grid-template-columns: repeat(3, 1fr); /* 三欄排版 */
    gap: 24px;
    justify-items: center;
    padding-top: 30px;
}
.card-block {
    text-align: center;
    background: rgba(255,255,255,0.05);
    padding: 12px;
    border-radius: 16px;
    box-shadow: 0 0 10px rgba(255,255,255,0.2);
    transition: transform 0.3s ease;
    width: 100%;        /* 撐滿欄位 */
    max-width: 100px;   /* 限制每張卡片最大寬度 */
}
.card-block:hover {
    transform: scale(1.03);
}
.card-block img {
    border-radius: 12px;
    width: 100%;
    height: auto;
    object-fit: contain;
}
.card-block .label {
    margin-top: 10px;
    font-weight: bold;
    color: gold;
    font-size: 14px;
}
</style>
""", unsafe_allow_html=True)

html = "<div class='card-gallery'>"

for _, row in cards_df.iterrows():
    name = row["名稱"]
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
st.components.v1.html(html, height=1300, scrolling=True)
