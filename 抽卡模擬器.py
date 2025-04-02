# ✅ 優等卡牌抽卡模擬器（含學生抽卡限制版）
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
import gspread
from google.oauth2.service_account import Credentials

SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(st.secrets["gspread_json"], scopes=SCOPE)
client = gspread.authorize(creds)

SHEET_URL = "https://docs.google.com/spreadsheets/d/1-uKCq-8w_c3EUItPKV9NnEVkRAQiC5I5vW2BZr8NFfg/edit"
sheet = client.open_by_url(SHEET_URL)

st.set_page_config(page_title="優等學院對戰卡牌 抽卡紀錄器", layout="wide")

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

cards_df = pd.read_excel("優等卡牌 的副本.xlsx", sheet_name="工作表4")
cards_df = cards_df[cards_df["類型"].isin(["學生卡", "知識卡", "武器卡"])]

# ✅ 檢查學生是否符合抽卡資格（根據 Google Sheet "進度表"）
def check_student_eligibility(student_id):
    try:
        progress_ws = sheet.worksheet("進度表")  # 這裡請確認你的工作表名稱
        records = progress_ws.get_all_records()
        for row in records:
            if str(row.get("學號")).strip() == str(student_id).strip():
                return row.get("可抽卡") == "是"
    except:
        st.error("讀取進度表失敗，請確認工作表名稱與權限")
    return False

# 用來記錄密碼是否正確（Session State）
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False



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




# 🔍 抓取該學生已抽過的卡片數量
def get_student_drawn_counts(student_id):
    try:
        worksheet = sheet.worksheet(student_id)
        records = worksheet.get_all_records()
    except:
        return {}

    counts = {}
    for record in records:
        key = (record["卡名"], record["稀有度"])
        counts[key] = counts.get(key, 0) + 1
    return counts

# 🧮 建立符合該學生限制 + 稀有度權重的卡池
def build_limited_card_pool(student_id):
    drawn_counts = get_student_drawn_counts(student_id)
    max_allowed = {"普通": 2, "稀有": 2, "史詩": 2, "傳說": 1}
    rarity_weights = {"普通": 75, "稀有": 20, "史詩": 4, "傳說": 1}

    limited_pool = []
    for _, row in cards_df.iterrows():
        name = row["名稱"]
        rarity = row["稀有度"]
        key = (name, rarity)
        current_count = drawn_counts.get(key, 0)
        remaining = max(0, max_allowed.get(rarity, 0) - current_count)
        weight = rarity_weights.get(rarity, 0)
        for _ in range(remaining * weight):
            limited_pool.append((name, rarity))
    return limited_pool


# 🎴 抽卡邏輯（含限制）
def draw_single(student_id):
    pool = build_limited_card_pool(student_id)
    if not pool:
        st.warning("你已經抽滿所有卡片了！")
        return pd.DataFrame(columns=["卡名", "稀有度"])
    drawn = random.sample(pool, 1)
    return pd.DataFrame(drawn, columns=["卡名", "稀有度"])

def draw_pack(student_id):
    pool = build_limited_card_pool(student_id)
    if len(pool) < 5:
        drawn = random.choices(pool, k=5)
    else:
        drawn = random.sample(pool, 5)
    return pd.DataFrame(drawn, columns=["卡名", "稀有度"])

def simulate_draws(student_id, n_packs=10):
    all_packs = []
    for _ in range(n_packs):
        pack = draw_pack(student_id)
        all_packs.append(pack)
    return pd.concat(all_packs, ignore_index=True)

# ✅ 儲存抽卡紀錄（含 Google Sheet）
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

    write_to_google_sheet(result_df, student_id)
    return filename

def write_to_google_sheet(result_df, student_id):
    taipei = pytz.timezone("Asia/Taipei")
    now = datetime.now(taipei).strftime("%Y-%m-%d %H:%M:%S")
    sheet_titles = [ws.title for ws in sheet.worksheets()]

    if student_id not in sheet_titles:
        worksheet = sheet.add_worksheet(title=student_id, rows=1000, cols=10)
        worksheet.append_row(["學號", "卡名", "稀有度", "抽取時間"])
    else:
        worksheet = sheet.worksheet(student_id)

    for _, row in result_df.iterrows():
        worksheet.append_row([
            student_id,
            row["卡名"],
            row["稀有度"],
            now
        ])


# ✅ 捲動畫面到底部（動畫區使用）
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
    import mimetypes
    img_folder = "card_images"
    back_path = os.path.join(img_folder, "card_back.png")
    if not os.path.exists(back_path):
        st.warning("請提供統一卡背圖 card_back.png 放在 card_images 資料夾內")
        return

    # Base64 讀入音效
    def encode_audio(file_path):
        if not os.path.exists(file_path):
            return ""
        mime_type, _ = mimetypes.guess_type(file_path)
        with open(file_path, "rb") as f:
            return f"data:{mime_type};base64," + base64.b64encode(f.read()).decode()

    sfx_legendary = encode_audio("sounds/legendary.mp3")
    sfx_epic = encode_audio("sounds/epic.mp3")
    sfx_rare = encode_audio("sounds/rare.mp3")

    card_width = 200
    card_height = 290
    if len(card_df) == 1:
        card_width = 260
        card_height = 370

    container_css = f"""
    .card-container {{
        {'display: flex; justify-content: center; align-items: center; height: 100%; padding: 30px;' if len(card_df) == 1 else 'display: grid; grid-template-columns: repeat(5, 1fr); gap: 20px; justify-items: center; padding: 20px; max-width: 1100px; margin: 0 auto;'}
    }}
    .flip-card {{
        background-color: transparent;
        width: {card_width}px;
        height: {card_height}px;
        perspective: 1000px;
        position: relative;
        transition: box-shadow 0.5s ease-in-out;
    }}
    """

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
                sound_data = sfx_rare
            elif rarity == "史詩":
                rarity_class = "hover-glow-purple"
                sound_data = sfx_epic
            elif rarity == "傳說":
                rarity_class = "hover-glow-gold"
                sound_data = sfx_legendary
            else:
                sound_data = ""

            audio_tag = f"var a=new Audio('{sound_data}');a.play();" if sound_data else ""

            html_cards += f"""
            <div class="flip-card {rarity_class}" onclick="this.classList.add('flipped'); {audio_tag}">
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

        if (idx + 1) % 5 == 0:
            html_cards += "<div style='flex-basis: 100%; height: 10px;'></div>"
            scroll_to_bottom()
        time.sleep(0.2)

    final_html = f"""
    <style>
    {container_css}
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

# --- Streamlit 前端 ---

st.title("優等學院對戰卡牌 抽卡紀錄器")

# 狀態管理
if "show_draw_page" not in st.session_state:
    st.session_state["show_draw_page"] = False
if "start_transition" not in st.session_state:
    st.session_state["start_transition"] = False
if "transition_start_time" not in st.session_state:
    st.session_state["transition_start_time"] = 0.0

# 如果還沒進入抽卡畫面且有按下按鈕，顯示動畫然後等候 2 秒自動轉換狀態
if st.session_state["start_transition"] and not st.session_state["show_draw_page"]:
    # 顯示動畫畫面
    st.markdown("""
    <style>
    .loading-text {
        font-size: 32px;
        font-weight: bold;
        color: #ffd700;
        text-align: center;
        animation: blink 1s infinite;
    }
    @keyframes blink {
        0%   { opacity: 0.2; }
        50%  { opacity: 1; }
        100% { opacity: 0.2; }
    }
    </style>
    <div class="loading-text">進入抽卡世界中...</div>
    """, unsafe_allow_html=True)

    # 等候 2 秒後自動切換畫面（此時畫面會 refresh，進入抽卡頁）
    if time.time() - st.session_state["transition_start_time"] > 2:
        st.session_state["show_draw_page"] = True
        st.session_state["start_transition"] = False
        st.session_state["transition_start_time"] = 0.0
    else:
        st.stop()

# 如果還沒進入抽卡頁面，先顯示介紹畫面
if not st.session_state["show_draw_page"]:
    # 顯示遊戲介紹與開始按鈕
    st.markdown("""
    ## 遊戲介紹

    你是優等學院的老師，帶領學生學習、比賽、挑戰課程。  
    透過學生卡、知識卡、事件卡與英雄老師的技能，  
    在學科戰場上擊敗對手的英雄，取得勝利！

    ---

    ### 選擇你的英雄導師！

    以下是四位英雄導師，請選擇你喜歡的導師組成卡組：  
    每副牌由 **1 張英雄卡 + 30 張主牌** 組成。  
    主牌包括學生卡、知識卡。  
    - 每張卡最多放入 2 張  
    - 傳說卡最多放入 1 張

    ---

    **完成功課、達成進度，開啟你的抽卡之旅吧！**
    """)
    
    if st.button("開始抽卡！"):
        st.session_state["start_transition"] = True
        st.session_state["transition_start_time"] = time.time()
    st.stop()
else:
    # 進入抽卡頁面時播放背景音樂
    show_background_music_player()



# 顯示 4 張英雄卡封面（含 hover 特效）
st.markdown("""
<style>
.hero-card-container {
    position: relative;
    text-align: center;
    transition: transform 0.3s ease-in-out, box-shadow 0.3s;
    border-radius: 12px;
}
.hero-card-container:hover {
    transform: scale(1.07);
    box-shadow: 0 0 20px gold;
}
.hero-hover {
    width: 100%;
    border-radius: 12px;
}
.hero-caption {
    font-weight: bold;
    margin-top: 5px;
    color: #f0e68c;
    font-size: 18px;
}
</style>
""", unsafe_allow_html=True)
hero_folder = "card_images"
hero_names = ["Annie老師", "紀老師", "黃老師", "Allen老師"]
hero_cols = st.columns(4)
for i, name in enumerate(hero_names):
    img_path = None
    for ext in [".png", ".jpg", ".jpeg", ".webp"]:
        try_path = os.path.join(hero_folder, f"{name}{ext}")
        if os.path.exists(try_path):
            img_path = try_path
            break

    if img_path:
        with open(img_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode()
        hero_cols[i].markdown(f"""
        <div class='hero-card-container'>
            <img src='data:image/png;base64,{img_b64}' class='hero-hover'>
            <div class='hero-caption'>{name}</div>
        </div>
        """, unsafe_allow_html=True)
       

if not st.session_state.authenticated:
    st.subheader("🔐 請先輸入密碼進入抽卡區")
    password = st.text_input("密碼：", type="password", key="card_draw_pwd")
    correct_password = "8341"
    if password == correct_password:
        st.session_state.authenticated = True
        st.rerun()
    else:
        st.warning("請輸入正確密碼以開始抽卡。")
        st.stop()

# 🧑‍🎓 輸入學號
student_id = st.text_input("請輸入學號：")

# ✅ 檢查是否有資格抽卡
if student_id and not check_student_eligibility(student_id):
    st.error("❌ 尚未達成抽卡資格，請完成指定進度後再試！")
    st.stop()



# 🔄 模式選擇
mode = st.radio("請選擇抽卡模式：", ["抽幾包卡（每包5張）", "單抽（1張卡）"])
animate = st.checkbox("啟用開包動畫模式", value=True)
if student_id:
    if mode == "抽幾包卡（每包5張）":
        packs = st.number_input("請輸入要抽幾包卡（每包5張）", min_value=1, max_value=5, value=1)
        if st.button("開始抽卡！"):
            result = simulate_draws(student_id, packs)
            st.success(f"已抽出 {packs} 包，共 {len(result)} 張卡！")
            saved_file = save_draw_result(result, student_id)
            st.info(f"抽卡紀錄已儲存至：{saved_file}")
            if animate:
                show_card_images_with_animation(result)
            else:
                st.dataframe(result)

    else:
        if st.button("立即單抽！🎯"):
            result = draw_single(student_id)
            st.success("你抽到了 1 張卡片！")
            saved_file = save_draw_result(result, student_id)
            st.info(f"抽卡紀錄已儲存至：{saved_file}")
            if animate:
                show_card_images_with_animation(result)
            else:
                st.dataframe(result)
else:
    st.warning("請先輸入學號才能進行抽卡。")