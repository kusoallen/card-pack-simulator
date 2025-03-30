# 優等卡牌抽卡模擬器 - Streamlit 網頁版 + 封面Logo + 背景音樂控制 + 傳說特效 + 音效
import streamlit as st
import pandas as pd
import random
from datetime import datetime
import os
from PIL import Image
import time
import base64

# 載入卡牌資料
cards_df = pd.read_excel("優等卡牌 的副本.xlsx", sheet_name="工作表4")

# 過濾主牌卡（加入武器卡）
cards_df = cards_df[cards_df["類型"].isin(["學生卡", "知識卡", "武器卡"])]

# 定義稀有度權重
rarity_weights = {
    "普通": 75,
    "稀有": 20,
    "史詩": 4,
    "傳說": 1
}

# 建立抽卡池
card_pool = []
for _, row in cards_df.iterrows():
    weight = rarity_weights.get(row["稀有度"], 0)
    card_pool.append((row["名稱"], row["稀有度"], weight))

# 抽卡函數
def draw_pack():
    pool = [card for card in card_pool for _ in range(card[2])]
    drawn = random.sample(pool, 5)
    return pd.DataFrame(drawn, columns=["卡名", "稀有度", "_weight"]).drop(columns="_weight")

# 模擬多包抽卡
def simulate_draws(n_packs=10):
    all_packs = []
    for _ in range(n_packs):
        pack = draw_pack()
        all_packs.append(pack)
    return pd.concat(all_packs, ignore_index=True)

# 儲存抽卡紀錄
def save_draw_result(result_df):
    folder = "抽卡紀錄"
    os.makedirs(folder, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{folder}/抽卡紀錄_{timestamp}.xlsx"
    result_df.to_excel(filename, index=False)
    return filename

# 顯示背景音樂播放器（需使用者手動播放）
def show_background_music_player():
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

# 播放傳說音效

def play_sound(sound_file):
    if os.path.exists(sound_file):
        with open(sound_file, "rb") as f:
            data = f.read()
            b64 = base64.b64encode(data).decode()
            st.markdown(
                f"""
                <audio autoplay>
                    <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
                </audio>
                """,
                unsafe_allow_html=True
            )

# 顯示卡圖（逐張動畫模式）+ 傳說閃爍 + 音效

def show_card_images_with_animation(card_df):
    st.subheader("📦 開卡包動畫展示")
    img_folder = "card_images"
    sound_played = False
    cols = st.columns(5)
    for idx, row in card_df.iterrows():
        name = row["卡名"]
        rarity = row["稀有度"]
        img_path = None
        for ext in [".png", ".jpg", ".jpeg", ".webp"]:
            try_path = os.path.join(img_folder, f"{name}{ext}")
            if os.path.exists(try_path):
                img_path = try_path
                break
        with cols[idx % 5]:
            if img_path:
                if rarity == "傳說":
                    st.markdown(
                        f"""
                        <div style='border: 4px solid gold; padding: 5px; animation: flash 1s infinite;'>
                            <img src='data:image/png;base64,{base64.b64encode(open(img_path, "rb").read()).decode()}' width='100%'>
                            <p style='text-align:center; font-weight:bold; color:gold;'>{name} ({rarity})</p>
                        </div>
                        <style>
                        @keyframes flash {{
                            0% {{ box-shadow: 0 0 5px gold; }}
                            50% {{ box-shadow: 0 0 20px gold; }}
                            100% {{ box-shadow: 0 0 5px gold; }}
                        }}
                        </style>
                        """,
                        unsafe_allow_html=True
                    )
                    if not sound_played:
                        play_sound("sounds/legendary.mp3")
                        sound_played = True
                else:
                    st.image(Image.open(img_path), caption=f"{name} ({rarity})", use_container_width=True)
            else:
                st.text(f"{name}（無圖）")
        time.sleep(0.5)

# --- Streamlit 前端 ---# 封面 Logo
LOGO_PATH = "logo.png"
if os.path.exists(LOGO_PATH):
    st.image(LOGO_PATH, use_column_width=True)

st.set_page_config(page_title="優等卡牌 抽卡模擬器")
st.title("🎴 優等卡牌 抽卡模擬器")

show_background_music_player()

packs = st.number_input("請輸入要抽幾包卡（每包5張）", min_value=1, max_value=100, value=10)
animate = st.checkbox("啟用開包動畫模式", value=True)

if st.button("開始抽卡！"):
    result = simulate_draws(packs)
    st.success(f"已抽出 {packs} 包，共 {len(result)} 張卡！")
    st.dataframe(result.reset_index(drop=True))

    # 儲存抽卡紀錄
    saved_file = save_draw_result(result)
    st.info(f"抽卡紀錄已儲存至：{saved_file}")

    # 顯示卡圖
    if animate:
        show_card_images_with_animation(result)
    else:
        st.subheader("📷 抽卡圖像展示")
        img_folder = "card_images"
        cols = st.columns(5)
        for idx, name in enumerate(result["卡名"]):
            img_path = None
            for ext in [".png", ".jpg", ".jpeg", ".webp"]:
                try_path = os.path.join(img_folder, f"{name}{ext}")
                if os.path.exists(try_path):
                    img_path = try_path
                    break
            if img_path:
                with cols[idx % 5]:
                    st.image(Image.open(img_path), caption=name, use_container_width=True)
            else:
                with cols[idx % 5]:
                    st.text(name + "（無圖）")