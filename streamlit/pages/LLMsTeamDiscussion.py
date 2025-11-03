import streamlit as st

import sys
import time
from datetime import datetime
import json
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.append(project_root)
from pathlib import Path
from utils import Agent
from utils.Function import save_codebook_excel, save_discuss_excel, import_json, save_json, zip_folder_to_bytes
from config.discuss_menu import *
from config.model_menu import *


class MultiAgentsDiscussion:
    def __init__(self, discuss_config, models_name):
        self.user_avatar = "🧑‍💻"
        self.title = "LLM Team Discuss"
        self.models_name = models_name
        self.config = discuss_config
        st.set_page_config(page_title=self.title, layout="wide")

    def init_session(self):
        st.title(self.title)
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
                section[data-testid="stTextArea"] textarea {
                  border-radius: 10px !important;
                }
                </style>
                """, unsafe_allow_html=True)
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
                    Suggestions:   1.What are the most valuable insights?   2.What perspectives or dimensions would 
                    you like to explore through a multi-agent system?  3.What are the main topics and relevant factors?
                </h3>
                """, unsafe_allow_html=True)
        st.info("Your research question guide the qualitative coding process.")
        if "user_response" in st.session_state:
            st.success(f"User Response from Home: {st.session_state.user_response}")
        # if os.path.exists("config/session_cache.json"):
        #     with open("config/session_cache.json", "r") as f:
        #         if os.path.getsize("config/session_cache.json") != 0:
        #             st.session_state.user_response = json.load(f)
        #             st.success(f"User Response from Home: {st.session_state.user_response}")
        if "chat_history" not in st.session_state:
            # introduce (F1)
            prologue = self.config["Facilitator"]["task1"]
            st.session_state.chat_history = [{
                "role": "Introduce-Prologue",
                "name": "Facilitator(Introduce)",
                "avatar": "📃",
                "content": prologue
            }]
        if "roles_identity" not in st.session_state:
            st.session_state.roles_identity = []
            st.session_state.roles_positionality = ["#########"] * 100
        if "discuss_models" not in st.session_state:
            st.session_state.discuss_models = self.models_name
            st.session_state.discuss_responses = []
            st.session_state.closing = []
        if "agree_list" not in st.session_state:
            st.session_state.agree_list = []
        if "disagreed_list" not in st.session_state:
            st.session_state.disagreed_list = []
            st.session_state.disagreed_list_select = []
        if "Facilitator" not in st.session_state:
            st.session_state.Facilitator = None
        if "roles" not in st.session_state:
            st.session_state.roles = None

    def render_model_selectors(self):
        with st.sidebar:
            st.subheader("⚖️ LLM Team")
            st.session_state.roles_identity.clear()
            for i, role in enumerate(["Role1", "Role2", "Role3"]):
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

    def render_sidebar_results(self):
        with st.sidebar:
            st.markdown("""
                <style>
                div.stButton > button:first-child {
                    color: red;              
                    padding: 10px;          
                    border-radius: 10px;       
                    font-size: 10px;         
                    transition: 1s;       
                }
                div.stButton > button:first-child:hover {
                    background-color: #45a049; 
                    transform: scale(1.1);  
                }
                </style>
            """, unsafe_allow_html=True)

            # st.session_state.human_input = st.chat_input("Input your prompt...")

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
            if st.button("Update WebPage/Items/Positionality"):
                pass
            self.render_divider()

            st.markdown("### ✅ Agreed Items")
            for _, item in enumerate(st.session_state.agree_list):
                st.markdown(f"- {item['code']}")

            st.markdown("---")
            st.markdown("### ⚠️ Disagreed Items")
            for idx, item in enumerate(st.session_state.disagreed_list):
                if st.button(f"🔍 {item['code']}", key=f"discuss_{idx}"):
                    st.session_state.selected_disagree = item
                    st.session_state.chat_history = [chat for chat in st.session_state.chat_history if
                                                     chat.get("role") != "Discuss Agent" or chat.get(
                                                         "role") != "Discuss Divider"]

    def render_user_message(self, text):
        st.markdown(f"""
        <div style='display: flex; justify-content: flex-end; align-items: center; margin: 6px 0;'>
            <div style='background-color: #DCF8C6; padding: 10px 14px; border-radius: 10px; max-width: 70%; text-align: left;'>
                {text}
            </div>
            <div style='font-size: 24px; margin-left: 8px;'>{self.user_avatar}</div>
        </div>
        """, unsafe_allow_html=True)

    def render_agent_message(self, name, avatar, content, delay=False):
        if name and avatar:
            st.markdown(f"""
            <div style='display: flex; justify-content: flex-start; align-items: flex-start; margin: 6px 0;'>
                <div style='font-size: 24px; margin-right: 8px;'>{avatar}</div>
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
            if delay:
                for ch in str(content):
                    full += ch
                    placeholder.markdown(content, unsafe_allow_html=True)
                    time.sleep(0.01)
            else:
                placeholder.markdown(content, unsafe_allow_html=True)

        st.markdown("</div></div>", unsafe_allow_html=True)

    def render_divider(self, text=""):
        st.markdown(
            f"""
            <style>
            .custom-divider {{
                color: gray;
                text-align: center;
                border-top: 1px solid #aaa;
                padding: 10px;
                font-family: sans-serif;
            }}
            </style>
            <div class='custom-divider'>{text}</div>
            """,
            unsafe_allow_html=True
        )

    def render_chat_history(self, role, name, avatar, content):
        st.session_state.chat_history.append({
            "role": role,
            "name": name,
            "avatar": avatar,
            "content": content
        })
        self.render_agent_message(name, avatar, content, True)

    def render_chat(self):
        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                self.render_user_message(msg["content"])
            elif msg["role"] in {"divider", "Discuss Divider"}:
                self.render_divider(msg["content"])
            else:
                self.render_agent_message(msg["name"], msg["avatar"], msg["content"])

    def handle_input(self):
        user_input = st.chat_input("Input your target text here...")
        if user_input:
            st.session_state.target_text = user_input
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            self.render_user_message(user_input)

            st.session_state.role_reply = None
            st.session_state.agree_reply = None

            # Role_Inference_Stage
            st.session_state.chat_history.append({
                "role": "divider",
                "content": "Roles Init Codebook"
            })
            self.render_divider("Roles Init Codebook")
            self.roles_stage(st.session_state.target_text, pos=False, code_gen=True)
            self.render_chat_history("Roles Generation agent", "Role_Inference_Stage", "🔁",
                                     st.session_state.roles_annotate)
            st.session_state.role_reply = st.session_state.roles_annotate

            # Agree_Disagree_stage (F2)
            st.session_state.chat_history.append({
                "role": "divider",
                "content": "Agree/Disagree Codebook"
            })
            self.render_divider("Agree/Disagree Codebook")
            agree_disagree_reply = self.agree_disagree(user_input)
            self.render_chat_history("Agree-Disagree", "Facilitator(Agree vs Disagree)", "📃", agree_disagree_reply)
            st.session_state.agree_disagree_reply = agree_disagree_reply

            if st.session_state.role_reply and st.session_state.agree_disagree_reply:
                st.session_state.agree_list = st.session_state.agree_disagree_reply.get("Agreed", [])
                st.session_state.disagreed_list = st.session_state.agree_disagree_reply.get("Disagreed", [])
                if not st.session_state.disagreed_list:
                    save_codebook_excel("codebook.xlsx", st.session_state.target_text, st.session_state.agree_list)

            # Discuss Ready (F3)
            st.session_state.chat_history.append({
                "role": "divider",
                "content": "Start Discuss"
            })
            self.render_divider("Start Discuss")
            st.session_state.Facilitator.event(self.config["Facilitator"]["task3"]
                                               .replace("[Target Text]", user_input)
                                               .replace("[ROLE_CODEBOOKS]", str(st.session_state.roles_annotate))
                                               .replace("[Disagreed]", str(st.session_state.disagreed_list)))
            discuss_ready_reply = st.session_state.Facilitator.ask()
            st.session_state.Facilitator.memory(discuss_ready_reply, False)
            self.render_chat_history("Agree-Disagree", "Facilitator(Why Disagree)", "📃", discuss_ready_reply)
            st.session_state.discuss_ready_reply = discuss_ready_reply

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
        roles.pop()
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

    def agree_disagree(self, target_text):
        fac_model = st.session_state.discuss_models["Facilitator"]
        Facilitator = Agent.Agent(
            model_name=fac_model,
            name="Agree_Disagree",
            api_key=api_key[fac_model],
            base_url=base_url[fac_model]
        )
        agree_agent_infer = self.config["Facilitator"]["system"]
        Facilitator.set_meta_prompt(agree_agent_infer)

        Facilitator.event(self.config["Facilitator"]["task2"]
                          .replace("[codes and justifications]", str(st.session_state.roles_annotate))
                          .replace("[Target Text]", target_text))
        view = Facilitator.ask()
        Facilitator.memory(view, False)
        st.session_state.Facilitator = Facilitator
        return json.loads(eval(view.replace('```', "'''").replace('json', '').replace('\n', '')))

    def discuss_single(self, target_text, code, definition):
        # Central Issue
        st.session_state.chat_history.append({
            "role": "divider",
            "content": "Central Issue"
        })
        self.render_divider("Central Issue")
        issue = self.config["Facilitator"]["Central Issue"]
        self.render_chat_history("Agree-Disagree", "Facilitator(Issue)", "📃", issue)

        # role system setting
        # st.session_state.roles = self.roles_init()
        meta_prompt = self.config["role_discussant"]["system"].replace("[Target Text]", target_text).replace(
            "[code and justification]", str([{"code": code, "definition": definition}]))
        for role, meta in zip(st.session_state.roles, st.session_state.roles_identity):
            role.memory_lst.clear()
            role.set_meta_prompt(meta_prompt)

        # role setting
        roles = []
        for j in range(len(st.session_state.roles)):
            roles.append({"name": f"{st.session_state.roles[j].name}({st.session_state.roles_identity[j]['role']})",
                          "color": color_circle[j],
                          "obj": st.session_state.roles[j]})

        # Debating
        discuss_responses = []
        for i, discuss in enumerate(self.config["role_discussant"]["discuss_round"].items()):
            st.session_state.chat_history.append({
                "role": "discuss Divider",
                "content": round_theme[i]
            })
            self.render_divider(round_theme[i])
            roles_responses = []
            for role_info in roles:
                role = role_info["obj"]
                if i == 0 or i == 3:
                    role.event(f"Round {i + 1}:\n{discuss}".replace("[code]", code).replace("[code]", code))
                else:
                    # role.event(f"Round {i + 1}:\n{discuss}".replace("[response]", str(discuss_responses[-1])))
                    role.event(f"Round {i + 1}:\n{discuss}")

                response = role.ask()
                response = response if f"Round {i + 1}" in response else f"Round {i + 1}\n{response}"
                roles_responses.append(f"{role_info['name']}: {response}")
                role.memory(response)
                self.render_chat_history("Discuss Agent", role_info["name"], role_info["color"],
                                         response.replace(f"Round {i + 1}", ""))
            # include roles_responses of every round
            discuss_responses.append(f"Round {i + 1}: {roles_responses}")

        st.session_state.discuss_responses.append(discuss_responses)

        # Closing (F4)
        close_prompt = self.config["Facilitator"]["task4"] \
            .replace("[discuss_responses]", str(discuss_responses)) \
            .replace("[code]", code)
        st.session_state.Facilitator.event(close_prompt)
        close = st.session_state.Facilitator.ask()
        st.session_state.Facilitator.memory(close, False)
        close_response = json.loads(close.replace('```', '').replace('json', '').strip())
        self.render_chat_history("Discuss Agent", "Facilitator(Final Decision)", "⚖️",
                                 json.dumps(close_response, ensure_ascii=False, indent=2))
        st.session_state.closing.append(close)

        # discuss finish, And process close close_response
        st.session_state.close_resolution = close_response["Resolution"]
        if close_response["Resolution"].strip().lower() == "retain":
            st.session_state.final_code = close_response["final_code"]
            st.session_state.final_justification = close_response["definition"]

    def run(self, output_file):
        self.render_chat()
        self.render_model_selectors()
        self.handle_input()
        self.render_sidebar_results()

        if st.session_state.get("selected_disagree") in st.session_state.disagreed_list:
            # Single Disagreed discuss
            item = st.session_state.selected_disagree
            st.session_state.disagreed_list_select.append(item["code"])
            self.discuss_single(st.session_state.target_text, item["code"], item["definition"])
            st.session_state.disagreed_list = [i for i in st.session_state.disagreed_list if
                                               i.get("code") != item["code"]]
            resolution = st.session_state.close_resolution
            if isinstance(resolution, str) and resolution.strip().lower() == "retain":
                st.session_state.agree_list.append({"code": st.session_state.final_code,
                                                    "definition": st.session_state.final_justification})

            if not st.session_state.disagreed_list:
                outdir = Path(f"streamlit/{output_file}").resolve()
                outdir.mkdir(parents=True, exist_ok=True)

                # Save discuss Process
                save_discuss_excel(f"{outdir}/discuss.xlsx", st.session_state.target_text,
                                   st.session_state.disagreed_list_select,
                                   st.session_state.discuss_responses)

                # Save Final Codebook
                discuss_process = []
                save_codebook_excel(f"{outdir}/codebook.xlsx", st.session_state.target_text,
                                    st.session_state.agree_list)
                for disagree, discuss_responses, close_response in zip(st.session_state.disagreed_list_select,
                                                                       st.session_state.discuss_responses,
                                                                       st.session_state.closing):
                    discuss_process.append({
                        "Disagreed": disagree,
                        "Process": discuss_responses,
                        "Closing": close_response
                    })

                result = {
                    "target_text": st.session_state.target_text,
                    "Role_Team": st.session_state.roles_identity,
                    "Role_init_codebook": st.session_state.roles_annotate,
                    "Consolidating_results": st.session_state.agree_disagree_reply,
                    "disagree_explain": st.session_state.discuss_ready_reply,
                    "discuss": discuss_process,
                    "Codebook": st.session_state.agree_list,
                }

                save_json(f"{outdir}/discuss_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json", result)

                st.markdown("### After completing all data annotation, click to package and download all the results.")

                zip_bytes = zip_folder_to_bytes(output_file)
                st.download_button(
                    label=f"Download results",
                    data=zip_bytes,
                    file_name=f"{Path(output_file).name}.zip",
                    mime="application/zip"
                )

                st.session_state.disagreed_list_select.clear()
                st.session_state.discuss_responses.clear()
                st.session_state.closing.clear()


if __name__ == "__main__":
    discuss_config = import_json("config/discuss_config.json")

    models_name = {
        "Role1": "gpt-4o-mini",
        "Role2": "gpt-4o-mini",
        "Role3": "gpt-4o-mini",
        "Facilitator": "gpt-4o-mini",
    }
    app = MultiAgentsDiscussion(discuss_config, models_name)
    app.init_session()
    app.run("LLMsTeamOutput")
