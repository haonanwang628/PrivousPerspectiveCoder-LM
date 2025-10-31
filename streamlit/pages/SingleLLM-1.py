import json

import streamlit as st

import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if project_root not in sys.path:
    sys.path.append(project_root)
from utils import Agent
from utils.Function import import_json
from config.model_menu import *


class SingleLLM:
    def __init__(self, model_name):
        self.title = "Single LLM (no roles, no perspective)"
        self.model_name = model_name
        self.user_avatar = "🧑‍💻"
        self.assistant_avatar = "🤖"
        st.set_page_config(page_title=self.title, layout="wide")
        self.init_session()

    def init_session(self):
        if "messages" not in st.session_state:
            st.session_state.messages = []
        if "agent" not in st.session_state:
            st.session_state.agent = Agent.Agent(
                model_name=model_name,
                name="Chat",
                api_key=api_key[self.model_name],
                base_url=base_url[self.model_name],
            )
            st.session_state.agent.set_meta_prompt("You are a helpful, concise assistant.")
        if "system_prompt" not in st.session_state:
            st.session_state.system_prompt = "You are a helpful, concise assistant."

    def render_user_message(self, text):
        st.markdown(f"""
         <div style='display: flex; justify-content: flex-end; align-items: center; margin: 6px 0;'>
            <div style='background-color: #DCF8C6; padding: 10px 14px; border-radius: 10px; max-width: 70%; text-align: left;'>
                {text}
            </div>
            <div style='font-size: 24px; margin-left: 8px;'>{self.user_avatar}</div>
        </div>
        """, unsafe_allow_html=True)

    def render_agent_message(self, name, content):
        st.markdown(f"""
        <div style='display: flex; justify-content: flex-start; align-items: flex-start; margin: 6px 0;'>
            <div style='font-size: 24px; margin-right: 8px;'>{self.assistant_avatar}</div>
            <div style='background-color: #F1F0F0; padding: 10px 14px; border-radius: 10px; max-width: 75%; text-align: left;'>
            <b>{name}</b>
            </div>
            
        """, unsafe_allow_html=True)
        try:
            parsed = json.loads(content) if isinstance(content, str) else content
            st.json(parsed)
        except Exception:
            placeholder = st.empty()
            full = ""
            for ch in str(content):
                full += ch
                placeholder.markdown(f"<div style='font-family: monospace;'>{full}</div>", unsafe_allow_html=True)

        st.markdown("</div></div>", unsafe_allow_html=True)

    def render_chat(self):
        st.title(self.title)
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                self.render_user_message(msg["content"])
            else:
                self.render_agent_message(msg["content"])

    def handle_input(self):
        user_input = st.chat_input("Input your target text here...")
        if user_input:
            st.session_state.messages.append({"role": "user", "content": user_input})
            self.render_user_message(user_input)

            agent = st.session_state.agent
            agent.event(
                config["Setting_1"]["Inductive_coding"].replace("[Target Text]", user_input))
            reply = agent.ask()
            agent.memory(reply, False)
            reply = json.loads(reply.replace('```', "").replace('json', '').strip())
            self.render_agent_message("Final Codebook", reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})

            # agent.event(
            #     config["Setting_1"]["Deductive_coding"].replace("[Target Text]", user_input))
            # reply = agent.ask()
            # reply = json.loads(reply.replace('```', "").replace('json', '').strip())
            # agent.memory(reply)
            # self.render_agent_message("Deductive Coding", reply)
            # st.session_state.messages.append({"role": "assistant", "content": reply})

    def run(self):
        st.title(self.title)
        self.handle_input()


if __name__ == "__main__":
    model_name = "gpt-4o-mini"
    config = import_json("config/SingleLLM_config.json")
    app = SingleLLM(model_name)
    app.run()
