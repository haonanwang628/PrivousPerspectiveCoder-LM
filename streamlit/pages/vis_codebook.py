import streamlit as st
import json
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

json_file = f"{project_root}\Data\Scrum-interviews\output\codebook.json"

with open(json_file, "r", encoding="utf-8") as f:
    data = json.load(f)

st.title("Codebook Visualization")

target_texts = [item["target_text"] for item in data]
# display_texts = [t[:100] + "..." if len(t) > 100 else t for t in target_texts]
display_texts = [t for t in target_texts]
selected_display = st.sidebar.radio("Target Text List", display_texts)
selected_text = next(t for t in target_texts if t.startswith(selected_display[:-3]) or t == selected_display)

selected_item = next(item for item in data if item["target_text"] == selected_text)
st.subheader("Target Text")
st.write(selected_item["target_text"])


st.subheader("Codebook")
for c in selected_item["Codebook"]:
    if "*code" in c:
        code_str = "* " + c["*code"]
    else:
        code_str = c["code"]
    with st.expander(f"Code: {code_str}"):
        st.markdown(f"**Evidence:** {c.get('evidence', c.get('*evidence'))}")

st.markdown("---")

