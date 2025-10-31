import streamlit as st
import json
import os

st.set_page_config(page_title="LLM App Hub", page_icon="🏠", layout="wide")
st.markdown("""
<style>
.card {
  border: 1px solid #e6e9ef; border-radius: 12px; padding: 14px 14px 8px 14px;
  background: #ffffff; box-shadow: 0 1px 2px rgba(16,24,40,0.04);
}
.card h4 {
  margin: 0 0 6px 0; font-size: 0.95rem; font-weight: 600;
}
.suggestion-row { display: flex; gap: 8px; flex-wrap: wrap; margin: 6px 0 4px 0; }
.help {
  margin-top: 4px; border-radius: 8px; padding: 10px;
  background: #edf4ff; color: #0b3a82; font-size: 0.85rem;
}
.icon-bar { position: absolute; right: 18px; top: 12px; display: flex; gap: 8px; }
.icon-dot {
  width: 22px; height: 22px; border-radius: 50%; background:#eaf3ff; color:#1b64da;
  display: grid; place-items: center; font-size: 12px; font-weight: 600;
  border: 1px solid #d5e6ff;
}
/* 让 text_area 更贴近卡片风格 */
section[data-testid="stTextArea"] textarea {
  border-radius: 10px !important;
}
</style>
""", unsafe_allow_html=True)
st.title("Multi Perspective Discussion Agents")
st.markdown('<div class="icon-bar"><div class="icon-dot">R</div><div class="icon-dot">Q</div></div>',
            unsafe_allow_html=True)
st.markdown("""
<h3 style="
    background: linear-gradient(to right, #4A90E2, #50C9CE);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight:700;
    font-size:20px;
    margin-bottom:4px;">
    Research Question
</h3>
""", unsafe_allow_html=True)
st.session_state.setdefault("user_response", "")
st.text_area(
    "Your Research Question",
    key="user_response",
    label_visibility="collapsed",
    height=150,
    placeholder="Input your research question here..."
)
st.markdown("""
<h3 style="
    background: linear-gradient(to right, #4A90E2, #50C9CE);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight:700;
    font-size:20px;
    margin-bottom:4px;">
    Suggestions:   1.What?   2.What?   3.What?
</h3>
""", unsafe_allow_html=True)
st.info("Your research question guide the qualitative coding process.")
with open("config/session_cache.json", "w") as f:
    json.dump(st.session_state.user_response, f)

