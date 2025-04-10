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

# ✅ 預覽 Google Drive 中的 PDF
st.components.v1.html(
    '<iframe src="https://drive.google.com/file/d/18U4wOx611d2LAWGluWfuuWM01Wtsu7K3/preview" width="100%" height="800px" allow="autoplay"></iframe>',
    height=800,
)

# ✅ 提供下載按鈕（Google Drive 直接下載連結）
st.markdown(
    "[📥 下載 PDF 規則書](https://drive.google.com/uc?export=download&id=18U4wOx611d2LAWGluWfuuWM01Wtsu7K3)",
    unsafe_allow_html=True
)