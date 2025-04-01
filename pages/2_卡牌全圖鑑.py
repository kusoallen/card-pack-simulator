import streamlit as st
import pandas as pd
import os
from PIL import Image
from io import BytesIO
import base64
import zipfile

st.set_page_config(page_title="卡牌全圖鑑")

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
    st.divider()
    st.subheader("📊 進階搜尋")

# KN 篩選
    min_kn = st.number_input("KN 最小值", min_value=0, value=0)
    max_kn = st.number_input("KN 最大值", min_value=0, value=10)

# KN 排序
    kn_sort = st.selectbox("KN 排序方式", ["無排序", "由小到大", "由大到小"])

# 科目篩選與排序
    subjects = sorted(cards_df["科目"].dropna().unique())
    subject_choice = st.multiselect("科目篩選", options=subjects, default=subjects)
    subject_sort = st.selectbox("科目排序方式", ["不排序", "A → Z", "Z → A"]) 

# 根據篩選條件過濾卡牌
if name_query:
    cards_df = cards_df[cards_df["名稱"].str.contains(name_query, case=False, na=False)]
if rarity_choice != "全部":
    cards_df = cards_df[cards_df["稀有度"] == rarity_choice]
cards_df = cards_df[cards_df["類型"].isin(type_choice)]
# KN 篩選
cards_df = cards_df[(cards_df["KN"] >= min_kn) & (cards_df["KN"] <= max_kn)]

# 科目篩選
cards_df = cards_df[cards_df["科目"].isin(subject_choice)]

# KN 排序
if kn_sort == "由小到大":
    cards_df = cards_df.sort_values(by="KN", ascending=True)
elif kn_sort == "由大到小":
    cards_df = cards_df.sort_values(by="KN", ascending=False)

# 科目排序
if subject_sort == "A → Z":
    cards_df = cards_df.sort_values(by="科目", ascending=True)
elif subject_sort == "Z → A":
    cards_df = cards_df.sort_values(by="科目", ascending=False)

# ✅ 分頁功能設定
cards_per_page = 9
total_cards = len(cards_df)
total_pages = (total_cards - 1) // cards_per_page + 1

# 頁碼輸入（可以改成 slider）
page = st.number_input("📄 頁碼選擇", min_value=1, max_value=total_pages, value=1, step=1)

# 取得目前頁數要顯示的卡牌
start_idx = (page - 1) * cards_per_page
end_idx = start_idx + cards_per_page
cards_page_df = cards_df.iloc[start_idx:end_idx]

# ✅ 樣式設定（3 欄顯示）
st.markdown("""
<style>
.card-gallery {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 30px;
    justify-items: center;
    padding: 30px;
}
.card-block {
    text-align: center;
    background: rgba(255,255,255,0.08);
    padding: 12px;
    border-radius: 16px;
    box-shadow: 0 0 12px rgba(255,255,255,0.2);
    max-width: 320px;
    width: 100%;
}
.card-block:hover {
    transform: scale(1.03);
}
.card-block img {
    width: 100%;
    max-width: 100%;
    max-height: 420px;
    height: auto;
    object-fit: contain;
    border-radius: 12px;
    box-shadow: 0 0 6px rgba(0,0,0,0.3);
}
.card-block .label {
    margin-top: 10px;
    font-weight: bold;
    color: gold;
    font-size: 14px;
}
main > div:has(.card-gallery) {
    max-width: 1400px !important;
    margin: 0 auto;
}
</style>
""", unsafe_allow_html=True)

# ✅ 顯示卡片內容（3 欄排版）
cols = st.columns(3)

for idx, (_, row) in enumerate(cards_page_df.iterrows()):
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

        with cols[idx % 3]:
            st.image(f"data:image/png;base64,{img_b64}", use_container_width=True)
            st.markdown(
                f"""
                <div style='text-align: center; color: gold; font-weight: bold;'>{name}（{rarity}）</div>
                <div style='text-align: center; color: white; font-size: 13px;'>KN 消耗：{row["KN"]}</div>
                """,
                unsafe_allow_html=True
            )