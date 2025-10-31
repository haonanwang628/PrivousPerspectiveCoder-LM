import json

import streamlit as st

import os
import sys

sys.path.append(os.path.dirname(__file__))
from streamlit.pages.LLMsTeamDiscussion import MultiAgentsDiscussion

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if project_root not in sys.path:
    sys.path.append(project_root)
from utils import Agent
from utils.Function import import_json
from config.discuss_menu import *
from config.model_menu import *


class SingleLLM(MultiAgentsDiscussion):
    def __init__(self, discuss_config, model_name):
        super().__init__(discuss_config, model_name)
        self.title = "Single LLM"
        self.models_name = model_name
        self.config = discuss_config

    def init_session(self):
        st.title(self.title)
        if "user_response" not in st.session_state:
            st.session_state.user_response = ""
        if os.path.exists("config/session_cache.json"):
            with open("config/session_cache.json", "r") as f:
                if os.path.getsize("config/session_cache.json") != 0:
                    st.session_state.user_response = json.load(f)
                    st.success(f"User Response from Home: {st.session_state.user_response}")
        if "chat_history" not in st.session_state:
            # introduce (F1)
            st.session_state.chat_history = []
        if "roles_identity" not in st.session_state:
            st.session_state.roles_identity = []
            st.session_state.roles_positionality = ["#########"] * 100
        if "roles" not in st.session_state:
            st.session_state.roles = None
        if "discuss_models" not in st.session_state:
            st.session_state.discuss_models = self.models_name

    def render_sidebar_results(self):
        with st.sidebar:
            st.markdown("""
                <style>
                div.stButton > button:first-child {
                    color: red;              /* 文字颜色 */
                    padding: 10px;          /* 内边距 */
                    border-radius: 10px;       /* 圆角 */
                    font-size: 10px;         /* 字体大小 */
                    transition: 1s;        /* 平滑过渡 */
                }
                div.stButton > button:first-child:hover {
                    background-color: #45a049; /* 悬停时颜色 */
                    transform: scale(1.1);   /* 悬停放大 */
                }
                </style>
            """, unsafe_allow_html=True)

            self.render_divider()
            if st.button("Generate Positionality"):
                self.roles_stage(pos=True)
                st.markdown("Generate Finish")
            self.render_divider()

            # target_text show
            st.markdown("### Target Text")
            if st.session_state.get("target_text"):
                st.markdown(f"{st.session_state.target_text}")
            else:
                st.markdown("#########")

            self.render_divider()
            if st.button("Update WebPage/Positionality"):
                pass
            self.render_divider()

    def render_model_selectors(self):
        with st.sidebar:
            st.subheader("⚖️ LLM Team")
            st.session_state.roles_identity.clear()
            for i, role in enumerate(["Role1"]):
                self.render_divider()
                role_selected = st.selectbox(f"{role}", roles_Id, index=i, key=f"{role}_name")
                Intended_Study_Level_selected = st.selectbox("Intended Study Level", Intended_Study_Level, index=i,
                                                             key=f"{role}_Intended_Study_Level")

                Subject_selected = st.selectbox("Subject", Subject, index=i,
                                                key=f"{role}_Subject")

                Research_Interest_selected = st.selectbox("Research Interest", Research_Interest, index=i,
                                                          key=f"{role}_Research_Interest")

                Dimensions_Source_selected = st.selectbox("Dimensions Source", Dimensions_Source, index=i,
                                                          key=f"{role}_Dimensions_Source")

                st.markdown("Positionality Statement")

                st.markdown(st.session_state.roles_positionality[i])
                st.session_state.roles_identity.append({"role": role_selected,
                                                        "Intended_Study_Level": Intended_Study_Level_selected,
                                                        "Subject": Subject_selected,
                                                        "Research_Interest": Research_Interest_selected,
                                                        "Dimensions_Source": Dimensions_Source_selected,
                                                        })

    def roles_init(self):
        roles = [
            Agent.Agent(
                model_name=mdl,
                name=role,
                api_key=api_key[mdl],
                base_url=base_url[mdl]
            )
            for mdl, role in
            zip([st.session_state.discuss_models[r] for r in st.session_state.discuss_models],
                [r for r in st.session_state.discuss_models])
        ]
        # roles system
        for role in roles:
            role.set_meta_prompt(self.config["role_prompt"]["system"])
        return roles

    def roles_stage(self, target_text="", pos=False, code_gen=False):
        # llm team (each role define)
        st.session_state.roles = self.roles_init()
        # positionality statement
        if pos:
            pos_prompts, positionality = [], []
            for role, meta in zip(st.session_state.roles, st.session_state.roles_identity):
                if st.session_state.user_response != "":
                    pos_prompt = self.config["role_prompt"]["positionality_rq"] \
                        .replace("[user response]", st.session_state.user_response)
                else:
                    pos_prompt = self.config["role_prompt"]["positionality"]
                pos_prompt = pos_prompt \
                    .replace("[insert]", meta["role"], 1) \
                    .replace("[insert]", meta["Intended_Study_Level"], 1) \
                    .replace("[insert]", meta["Subject"], 1) \
                    .replace("[insert]", meta["Research_Interest"], 1) \
                    .replace("[insert]", meta["Dimensions_Source"], 1)
                pos_prompts.append(pos_prompt)
                role.event(pos_prompt)
                role_response = role.ask()
                positionality.append(role_response)
                role.memory(role_response)
            st.session_state.pos_prompts = pos_prompts
            st.session_state.roles_positionality = positionality

        # roles codebook generate
        if code_gen:
            roles_annotate = []
            for i, role in enumerate(st.session_state.roles):
                role.memory_lst.append({"role": "system", "content": f"{st.session_state.pos_prompts[i]}"})
                role.memory_lst.append({"role": "assistant", "content": f"{st.session_state.roles_positionality[i]}"})

                role.event(self.config["role_prompt"]["task"].replace("[Target Text]", target_text))
                role_response = role.ask()
                role.memory(role_response, False)
                roles_annotate.append(
                    json.loads(role_response.replace('```', "").replace('json', '').strip()))
            st.session_state.roles_annotate = roles_annotate  # Roles Annotate list

    def handle_input(self):
        user_input = st.chat_input("Input your target text here...")
        if user_input:
            st.session_state.target_text = user_input
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            self.render_user_message(user_input)

            self.roles_stage(st.session_state.target_text, pos=False, code_gen=True)
            self.render_chat_history("Role1 Generation agent", "Role1 Codebook", "🔴",
                                     st.session_state.roles_annotate)

    def run(self, output_file):
        self.render_chat()
        self.render_model_selectors()
        self.handle_input()
        self.render_sidebar_results()


if __name__ == "__main__":
    model_name = {"Role1": "gpt-4o-mini"}
    config = import_json("config/discuss_config.json")
    app = SingleLLM(config, model_name)
    app.init_session()
    app.run("SingleLLMOutput")
