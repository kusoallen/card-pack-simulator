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


# ✅ 檢查學生是否符合抽卡資格（根據 Google Sheet "進度表"）
def check_student_eligibility(student_id):
    try:
        progress_ws = sheet.worksheet("進度表")
        expected_headers = ["學號", "姓名", "完成作業", "作業最後抽卡日", "完成進度", "進度最後抽卡日"]
        records = progress_ws.get_all_records(expected_headers=expected_headers)
        today = datetime.now(pytz.timezone("Asia/Taipei")).strftime("%Y-%m-%d")

        for i, row in enumerate(records):
            if str(row.get("學號")).strip() == str(student_id).strip():
                header = list(row.keys())
                draw_opportunities = {"作業": False, "進度": False}
                if row.get("完成作業") == "是" and row.get("作業最後抽卡日") != today:
                    draw_opportunities["作業"] = True
                if row.get("完成進度") == "是" and row.get("進度最後抽卡日") != today:
                    draw_opportunities["進度"] = True

                st.session_state["draw_opportunities"] = draw_opportunities
                st.session_state["student_id"] = student_id
                return

        st.session_state["draw_opportunities"] = {"作業": False, "進度": False}
    except Exception as e:
        st.error(f"❌ 無法讀取進度表：{e}")
        st.session_state["draw_opportunities"] = {"作業": False, "進度": False}


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
                <p>🎵 優等學院對戰卡牌-卡牌為刃：</p>
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
    rarity_weights = {"普通": 55, "稀有": 20, "史詩": 20, "傳說": 5}

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
    sfx_hover = encode_audio("sounds/hover.mp3")  # 統一 hover 音效

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
        animation: float 3s ease-in-out infinite;
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
                rarity_class = "hover-glow-gold pulse-animation"
                sound_data = sfx_legendary
            else:
                sound_data = ""

            audio_tag = f"var a=new Audio('{sound_data}');a.play();" if sound_data else ""
            hover_audio = f"onmouseenter=\"if(!this.hovered){{this.hovered=true;this.sound=new Audio('{sfx_hover}');this.sound.loop=true;this.sound.volume=0.4;this.sound.play();}}\" onmouseleave=\"if(this.sound){{this.sound.pause();this.sound.currentTime=0;this.hovered=false;}}\""
            
            html_cards += f"""
            <div class="flip-card {rarity_class}" onclick="this.classList.add('flipped'); {audio_tag}" {hover_audio}>
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
    @keyframes pulse {{
        0%   {{ transform: scale(1); }}
        50%  {{ transform: scale(1.2); }}
        100% {{ transform: scale(1); }}
    }}
    @keyframes float {{
        0% {{ transform: translateY(0px); }}
        50% {{ transform: translateY(-10px); }}
        100% {{ transform: translateY(0px); }}
    }}
    .pulse-animation {{
        animation: pulse 1s ease-in-out infinite;
    }}
    </style>
    <div class="card-container">
    {html_cards}
    </div>
    """
    components.html(final_html, height=750, scrolling=True)


# --- Streamlit 前端 ---

st.title("優等學院對戰卡牌 抽卡紀錄器")

# 背景音樂函式（顯示播放器）
def show_background_music_player():
    music_path = "sounds/bgm.mp3"
    if os.path.exists(music_path):
        with open(music_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
            components.html(f"""
                <p>🎵 優等學院對戰卡牌-卡牌為刃：</p>
                <audio id="bgm" controls autoplay loop>
                    <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
                    Your browser does not support the audio element.
                </audio>
                <script>
                    var audio = document.getElementById("bgm");
                    audio.volume = 0.05;  // 設定音量為 20%
                </script>
            """, height=100)

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
       


# ✅ 保留輸入學號欄位並每次都檢查最新狀態
student_id = st.text_input("請輸入學號：", value=st.session_state.get("student_id", ""), key="student_id_input")
if student_id and student_id != st.session_state.get("student_id", ""):
    st.session_state.pop("draw_opportunities", None)  # 清除舊抽卡機會
    check_student_eligibility(student_id)


#student_id = st.text_input("請輸入學號：", key="student_id_input")

#if student_id and "draw_opportunities" not in st.session_state:
    #check_student_eligibility(student_id)


# ✅ 玩家選擇要抽的卡池
available_pools = ["基礎包"] #available_pools = ["基礎包", "羅馬戰士體驗營"]
selected_pool = st.selectbox("請選擇想抽的卡包：(史詩、傳說機率6/4-6/6提升五倍)", available_pools)

# ✅ 根據卡池分類篩選卡片
all_cards_df = pd.read_excel("優等卡牌 的副本.xlsx", sheet_name="遊戲卡片")
cards_df = all_cards_df[
    (all_cards_df["類型"].isin(["學生卡", "知識卡", "武器卡"])) &
    (all_cards_df["卡池分類"] == selected_pool)
]
# ✅ 顯示抽卡機會與按鈕
if "draw_opportunities" in st.session_state:
    opp = st.session_state["draw_opportunities"]
    total = sum(1 for v in opp.values() if v)
    if total > 0:
        st.success(f"🎉 你今天有 {total} 次抽卡機會！")
        if opp["作業"]:
            if st.button("🎯 抽卡（完成作業）", key="draw_homework"):
                result = draw_single(student_id)
                st.success("你抽到了 1 張卡片！（作業）")
                saved_file = save_draw_result(result, student_id)
                show_card_images_with_animation(result)

                try:
                    progress_ws = sheet.worksheet("進度表")
                    cell = progress_ws.find(student_id)
                    col_idx = progress_ws.row_values(1).index("作業最後抽卡日") + 1
                    progress_ws.update_cell(cell.row, col_idx, datetime.now(pytz.timezone("Asia/Taipei")).strftime("%Y-%m-%d"))
                    # ✅ 移除當次抽卡機會並立即刷新
                    st.session_state["draw_opportunities"]["作業"] = False
                    st.rerun()
                except:
                    st.warning("⚠️ 無法更新作業抽卡日期。")

        if opp["進度"]:
            if st.button("🎯 抽卡（完成進度）", key="draw_progress"):
                result = draw_single(student_id)
                st.success("你抽到了 1 張卡片！（進度）")
                saved_file = save_draw_result(result, student_id)
                show_card_images_with_animation(result)

                try:
                    progress_ws = sheet.worksheet("進度表")
                    cell = progress_ws.find(student_id)
                    col_idx = progress_ws.row_values(1).index("進度最後抽卡日") + 1
                    progress_ws.update_cell(cell.row, col_idx, datetime.now(pytz.timezone("Asia/Taipei")).strftime("%Y-%m-%d"))
                    # ✅ 移除當次抽卡機會並立即刷新
                    st.session_state["draw_opportunities"]["進度"] = False
                    st.rerun()
                except:
                    st.warning("⚠️ 無法更新進度抽卡日期。")
    else:
        st.info("✅ 尚無可用抽卡次數，請先完成作業或進度！")