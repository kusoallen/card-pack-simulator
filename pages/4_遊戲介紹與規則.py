# 📘 優等卡牌遊戲介紹頁面
import streamlit as st
import base64
import os

st.set_page_config(page_title="遊戲介紹與規則")
st.title("🃏 優等卡牌遊戲介紹")

# ✅ 遊戲簡介
st.subheader("🔰 遊戲簡介")
st.markdown("""
優等卡牌是一款結合教學與娛樂的策略對戰遊戲。玩家可以透過抽卡收集各科學生卡與知識卡，
組建自己的牌組，並與其他玩家進行 1v1 對戰。

- 📚 **卡片類型**：學生卡、知識卡、事件卡、武器卡、英雄卡
- 🎯 **勝利條件**：打倒對手英雄老師，或讓對手牌庫用盡
- 🧠 **主題特色**：結合補習班課程內容與角色設定，融入國英數自社學科

歡迎所有學生挑戰策略與運氣，打造最強牌組！
""")

# ✅ PDF 規則書下載與嵌入
st.subheader("📜 遊戲規則書")
PDF_PATH = "game_rules.pdf"  # 請將你的 PDF 檔命名為這個名稱放在同資料夾中

if os.path.exists(PDF_PATH):
    with open(PDF_PATH, "rb") as f:
        pdf_data = f.read()
        b64_pdf = base64.b64encode(pdf_data).decode()
    
    # 嵌入替代方案：提供點擊連結開啟 PDF
    st.markdown(
        f"📖 [點我線上查看規則書](data:application/pdf;base64,{b64_pdf})",
        unsafe_allow_html=True
    )

    # 提供下載按鈕
    st.download_button(
        label="📥 下載完整規則書 PDF",
        data=pdf_data,
        file_name="優等卡牌_遊戲規則.pdf",
        mime="application/pdf"
    )