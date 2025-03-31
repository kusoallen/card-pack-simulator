# 優等卡牌抽卡模擬器 - Streamlit 網頁版 + 封面Logo + 背景音樂控制 + 傳說特效 + 音效
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import random
from datetime import datetime
import os
from PIL import Image
import time
import base64
import zipfile
import io
import pytz

st.set_page_config(page_title="優等卡牌 抽卡模擬器", layout="wide")

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
def draw_single():
    pool = [card for card in card_pool for _ in range(card[2])]
    drawn = random.sample(pool, 1)
    return pd.DataFrame(drawn, columns=["卡名", "稀有度", "_weight"]).drop(columns="_weight")

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

# ✅ 加入學號欄位並儲存結果
def save_draw_result(result_df, student_id):
    taipei = pytz.timezone("Asia/Taipei")
    now_tw = datetime.now(taipei).strftime("%Y-%m-%d %H:%M:%S")
    result_df.insert(0, "學號", student_id)
    result_df["抽取時間"] = now_tw
    folder = "抽卡紀錄"
    os.makedirs(folder, exist_ok=True)
    timestamp = datetime.now(taipei).strftime("%Y%m%d_%H%M%S")
    filename = f"{folder}/抽卡紀錄_{student_id}_{timestamp}.xlsx"
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

# 每5張卡片捲動到底部（使用錨點）
def scroll_to_bottom():
    components.html("""
        <div id='bottom-marker'></div>
        <script>
            setTimeout(function() {
                var marker = document.getElementById("bottom-marker");
                if (marker) {
                    marker.scrollIntoView({ behavior: "smooth" });
                }
            }, 200);
        </script>
    """, height=0)

def show_card_images_with_animation(card_df):
    st.subheader("點擊卡片翻面展示")
    img_folder = "card_images"
    back_path = os.path.join(img_folder, "card_back.png")
    if not os.path.exists(back_path):
        st.warning("請提供統一卡背圖 card_back.png 放在 card_images 資料夾內")
        return

    sound_played = False
    back_b64 = base64.b64encode(open(back_path, "rb").read()).decode()
    html_cards = ""

    for idx, row in card_df.iterrows():
        name = row["卡名"]
        rarity = row["稀有度"]
        img_path = None
        for ext in [".png", ".jpg", ".jpeg", ".webp"]:
            try_path = os.path.join(img_folder, f"{name}{ext}")
            if os.path.exists(try_path):
                img_path = try_path
                break

        if img_path:
            front_b64 = base64.b64encode(open(img_path, "rb").read()).decode()
            rarity_class = ""
            if rarity == "稀有":
                rarity_class = "hover-glow-white"
            elif rarity == "史詩":
                rarity_class = "hover-glow-purple"
            elif rarity == "傳說":
                rarity_class = "hover-glow-gold"

            html_cards += f"""
            <div class="flip-card {rarity_class}" onclick="this.classList.add('flipped')">
              <div class="flip-card-inner">
                <div class="flip-card-front">
                  <img src="data:image/png;base64,{back_b64}" width="100%">
                </div>
                <div class="flip-card-back">
                  <img src="data:image/png;base64,{front_b64}" width="100%">
                  <p style='text-align:center;font-weight:bold;color:gold;margin:0;'>{name} ({rarity})</p>
                </div>
              </div>
            </div>
            """
            if rarity == "傳說" and not sound_played:
                play_sound("sounds/legendary.mp3")
                sound_played = True

        if (idx + 1) % 5 == 0:
            html_cards += "<div style='flex-basis: 100%; height: 10px;'></div>"
            scroll_to_bottom()
        time.sleep(0.2)

    final_html = f"""
    <style>
    .card-container {{
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 20px;
        justify-items: center;
        padding: 20px;
        max-width: 1100px;
        margin: 0 auto;
    }}
    .flip-card {{
        background-color: transparent;
        width: 200px;
        height: 290px;
        perspective: 1000px;
        position: relative;
        transition: box-shadow 0.5s ease-in-out;
    }}
    .flip-card-inner {{
        position: relative;
        width: 100%;
        height: 100%;
        text-align: center;
        transition: transform 0.8s;
        transform-style: preserve-3d;
    }}
    .flipped .flip-card-inner {{
        transform: rotateY(180deg);
    }}
    .flip-card-front, .flip-card-back {{
        position: absolute;
        width: 100%;
        height: 100%;
        backface-visibility: hidden;
        border-radius: 12px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.3);
    }}
    .flip-card-back {{
        transform: rotateY(180deg);
    }}
    .hover-glow-white:hover {{
        box-shadow: 0 0 20px 5px white !important;
        animation: glow-white 1.5s infinite alternate;
    }}
    .hover-glow-purple:hover {{
        box-shadow: 0 0 20px 5px purple !important;
        animation: glow-purple 1.5s infinite alternate;
    }}
    .hover-glow-gold:hover {{
        box-shadow: 0 0 20px 5px gold !important;
        animation: glow-gold 1.5s infinite alternate;
    }}
    @keyframes glow-white {{
        from {{ box-shadow: 0 0 5px white; }}
        to {{ box-shadow: 0 0 25px white; }}
    }}
    @keyframes glow-purple {{
        from {{ box-shadow: 0 0 5px purple; }}
        to {{ box-shadow: 0 0 25px violet; }}
    }}
    @keyframes glow-gold {{
        from {{ box-shadow: 0 0 5px gold; }}
        to {{ box-shadow: 0 0 25px orange; }}
    }}
    </style>
    <div class="card-container">
    {html_cards}
    </div>
    """
    components.html(final_html, height=750, scrolling=True)


# --- Streamlit 前端 ---# 封面 Logo
LOGO_PATH = "logo.png"
if os.path.exists(LOGO_PATH):
    st.image(LOGO_PATH, use_container_width=True)

st.title("優等卡牌 抽卡模擬器")

show_background_music_player()

# 🧑‍🎓 輸入學號
student_id = st.text_input("請輸入學號：")

# 🔄 模式選擇
mode = st.radio("請選擇抽卡模式：", ["抽幾包卡（每包5張）", "單抽（1張卡）"])
animate = st.checkbox("啟用開包動畫模式", value=True)
if student_id:
    if mode == "抽幾包卡（每包5張）":
        packs = st.number_input("請輸入要抽幾包卡（每包5張）", min_value=1, max_value=5, value=1)
        if st.button("開始抽卡！"):
            result = simulate_draws(packs)
            st.success(f"已抽出 {packs} 包，共 {len(result)} 張卡！")
            saved_file = save_draw_result(result, student_id)
            st.info(f"抽卡紀錄已儲存至：{saved_file}")
            if animate:
                show_card_images_with_animation(result)
            else:
                st.dataframe(result)

    else:
        if st.button("立即單抽！🎯"):
            result = draw_single()
            st.success("你抽到了 1 張卡片！")
            saved_file = save_draw_result(result, student_id)
            st.info(f"抽卡紀錄已儲存至：{saved_file}")
            if animate:
                show_card_images_with_animation(result)
            else:
                st.dataframe(result)
else:
    st.warning("請先輸入學號才能進行抽卡。")


# 📖 顯示某學生所有抽卡紀錄
with st.expander("📚 查詢學生抽卡紀錄"):
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
            st.dataframe(combined)
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
