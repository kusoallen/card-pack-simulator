import streamlit as st
import pandas as pd
import os
from PIL import Image
from io import BytesIO
import base64
import zipfile

st.set_page_config(page_title="優等卡牌圖鑑")

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

st.title("🃏 優等卡牌圖鑑")


# 載入卡牌資料
cards_df = pd.read_excel("優等卡牌 的副本.xlsx", sheet_name="遊戲卡片")
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

# ✅ 新增：卡池分類
    pool_options = sorted(cards_df["卡池分類"].dropna().unique()) if "卡池分類" in cards_df.columns else []
    pool_choice = st.selectbox("選擇卡池：", ["全部"] + pool_options) if pool_options else "全部"


    st.divider()
    st.subheader("📊 進階搜尋")

    min_kn = st.number_input("KN 最小值", min_value=0, value=0)
    max_kn = st.number_input("KN 最大值", min_value=0, value=10)

    kn_sort = st.selectbox("KN 排序方式", ["無排序", "由小到大", "由大到小"])

    subjects = sorted(cards_df["科目"].dropna().unique())
    subject_choice = st.multiselect("科目篩選", options=subjects, default=subjects)
    subject_sort = st.selectbox("科目排序方式", ["不排序", "A → Z", "Z → A"])

# 篩選與排序
filter_changed = False

if name_query:
    cards_df = cards_df[cards_df["名稱"].str.contains(name_query, case=False, na=False)]
    filter_changed = True
if rarity_choice != "全部":
    cards_df = cards_df[cards_df["稀有度"] == rarity_choice]
    filter_changed = True
if pool_choice != "全部" and "卡池分類" in cards_df.columns:
    cards_df = cards_df[cards_df["卡池分類"] == pool_choice]
    filter_changed = True


cards_df = cards_df[cards_df["類型"].isin(type_choice)]
cards_df = cards_df[(cards_df["KN"] >= min_kn) & (cards_df["KN"] <= max_kn)]
cards_df = cards_df[cards_df["科目"].isin(subject_choice)]

if kn_sort == "由小到大":
    cards_df = cards_df.sort_values(by="KN", ascending=True)
elif kn_sort == "由大到小":
    cards_df = cards_df.sort_values(by="KN", ascending=False)

if subject_sort == "A → Z":
    cards_df = cards_df.sort_values(by="科目", ascending=True)
elif subject_sort == "Z → A":
    cards_df = cards_df.sort_values(by="科目", ascending=False)

if "page" not in st.session_state:
    st.session_state.page = 1
if filter_changed:
    st.session_state.page = 1

# 分頁設定
cards_per_page = 9
total_cards = len(cards_df)
total_pages = (total_cards - 1) // cards_per_page + 1

# 分頁按鈕與跳頁功能
col1, col2, col3 = st.columns([1, 2, 1])
with col1:
    if st.button("⬅ 上一頁") and st.session_state.page > 1:
        st.session_state.page -= 1
with col3:
    if st.button("下一頁 ➡") and st.session_state.page < total_pages:
        st.session_state.page += 1
with col2:
    selected_page = st.selectbox(
        "📄 選擇頁碼",
        options=list(range(1, total_pages + 1)),
        index=st.session_state.page - 1,
        key="page_select"
    )
    if selected_page != st.session_state.page:
        st.session_state.page = selected_page

start_idx = (st.session_state.page - 1) * cards_per_page
end_idx = start_idx + cards_per_page
cards_page_df = cards_df.iloc[start_idx:end_idx]

# 樣式
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

# 顯示卡片
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
