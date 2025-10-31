import streamlit as st
import json
import sys
import os

sys.path.append(os.path.dirname(__file__))
from LLMsTeamDiscussion import MultiAgentsDiscussion

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__)))
print(project_root)
if project_root not in sys.path:
    sys.path.append(project_root)
from config.discuss_menu import *
from utils.Function import import_json


class MultiAgentsHumanDiscussion(MultiAgentsDiscussion):
    def __init__(self, discuss_config, models_name):
        super().__init__(discuss_config, models_name)
        self.title = "LLM-Human Team discuss"
        st.session_state.discuss_models = models_name

    def render_model_selectors(self):
        with st.sidebar:
            st.subheader("⚖️ LLM-Human Team")
            st.session_state.roles_identity.clear()
            for i, role in enumerate(["Role1", "Role2"]):
                self.render_divider()
                role_selected = st.selectbox(f"{role}", roles_Id, index=i, key=f"{role}_name")
                Intended_Study_Level_selected = st.selectbox("Intended Study Level", Intended_Study_Level, index=i,
                                                             key=f"{role}_Intended_Study_Level")

                Subject_selected = st.selectbox("Subject", Subject, index=i,
                                                key=f"{role}_Subject1")

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
            self.render_human_selectors()

    def render_human_selectors(self):
        self.render_divider()
        st.markdown("Human")

        FIELDS = [
            ("role", "Your role Identity information"),
            ("Intended_Study_Level", "Your Intended Study Level"),
            ("Subject", "Your Subject"),
            ("Research_Interest", "Your Research Interest"),
            ("Dimensions_Source", "Your Dimensions Source")
        ]

        input_containers = [st.empty() for _ in FIELDS]

        values = {}
        for (k, label), container in zip(FIELDS, input_containers):
            with container:
                values[k] = st.text_input(label, key=f"human_{k}")
        if all(values.values()):
            st.session_state.roles_identity.append(values)

            for c in input_containers:
                c.empty()

            st.markdown(self.white_background_div(values["role"]), unsafe_allow_html=True)

            sections = [
                ("Intended Study Level", values["Intended_Study_Level"]),
                ("Subject", values["Subject"]),
                ("Research Interest", values["Research_Interest"]),
                ("Dimensions Source", values["Dimensions_Source"])
            ]
            for title, content in sections:
                st.markdown(title, unsafe_allow_html=True)
                st.markdown(self.white_background_div(content), unsafe_allow_html=True)
        st.markdown("Positionality Statement")
        st.markdown(st.session_state.roles_positionality[2])

    def white_background_div(self, content):
        return f"""
        <div style="
            background-color: white;
            padding: 8px;
            border-radius: 8px;
            margin-bottom: 10px;
        ">
            {content}
        </div>
        """

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

    def discuss_single(self, target_text, code, definition):
        # ----------- Central Issue ------------
        if "discuss_started" not in st.session_state:
            st.session_state.chat_history.append({
                "role": "divider",
                "content": "Central Issue"
            })
            self.render_divider("Central Issue")
            issue = self.config["Facilitator"]["Central Issue"]
            self.render_chat_history("Agree-Disagree", "Facilitator(Issue)", "📃", issue)

            # role system setting
            st.session_state.roles = self.roles_init()
            meta_prompt = self.config["role_discussant"]["system"] \
                .replace("[Target Text]", target_text) \
                .replace("[code and justification]", str([{"code": code, "definition": definition}]))
            for role in st.session_state.roles:
                role.set_meta_prompt(meta_prompt)

            # init identity & discuss vars
            st.session_state.current_round = 0
            st.session_state.current_role = 0
            st.session_state.input_finished = False
            st.session_state.setdefault("human_input", "")
            st.session_state.discuss_response = []
            st.session_state.discuss_started = True
            st.session_state.discuss_text = ""

        # ----------- Prepare Round Info ------------
        round_keys = list(self.config["role_discussant"]["discuss_round"].keys())
        round_content = list(self.config["role_discussant"]["discuss_round"].values())
        roles = [
            {"name": f"{r.name}({st.session_state.roles_identity[i]['role']})", "color": color_circle[i], "obj": r}
            for i, r in enumerate(st.session_state.roles)
        ]

        i = st.session_state.current_round
        j = st.session_state.current_role

        # ----------- Discuss in Progress ------------
        if i < len(round_keys):
            discuss_key = round_keys[i]
            if not st.session_state.discuss_text:
                st.session_state.discuss_text = self.config["role_discussant"]["discuss_round"][discuss_key]

            if j == 0:
                st.session_state.chat_history.append({
                    "role": "Discuss Divider",
                    "content": round_theme[i]
                })
                self.render_divider(round_theme[i])
                self.render_chat_history("Introduce", "Facilitator", "📃",
                                         round_content[i].split("Output strictly in JSON\n\n")[0])
                self.render_chat_history("Introduce", None, None,
                                         round_content[i].split("Output strictly in JSON\n\n")[1])
                st.session_state[f"round_{i}_responses"] = []

            role_info = roles[j]
            role = role_info["obj"]

            # 插手人工输入
            if j == 2 and not st.session_state.input_finished:
                st.markdown(f"{role_info['color']} **{role_info['name']}** is waiting for your input:")
                st.text_input("Your Thinking", key="human_input", label_visibility="collapsed")
                if st.button("Input Finish", key=f"btn_round_{i}"):
                    st.session_state.input_finished = True
                    st.session_state.discuss_text = f"{st.session_state.human_input}"
                    # human_text = f"\n\nConsider the human response carefully. " \
                    #              f"Decide whether you agree or disagree with it, and " \
                    #              f"briefly explain your reasoning. Your explanation should " \
                    #              f"be based on logical analysis, relevance to the input, and " \
                    #              f"sound judgment.\n\nHuman Response: {st.session_state.human_input}\n\n" \
                    #              f"strictly in the following output format: \n\n" \
                    #              f"**Reasoning:** briefly explain(1~3 sentence)"
                    # st.session_state.discuss_text = f"{st.session_state.discuss_text}{human_text}"
                    if st.button("Click here to Continue"):
                        pass

                # if st.button("Skip Input", key=f"skip_btn_round_{i}"):
                #     st.session_state.input_finished = True
                #     st.session_state.discuss_text = ""
                #     if st.button("Click here to Continue"):
                #         pass

                st.stop()

            # 生成 prompt
            if i == 0 or i == 3:
                event_text = f"Round {i + 1}:\n{st.session_state.discuss_text}".replace("[code]", code).replace(
                    "[code]",
                    code)
            else:
                last_response = st.session_state.discuss_response[-1] if st.session_state.discuss_response else ""
                # event_text = f"Round {i + 1}:\n{st.session_state.discuss_text}".replace("[response]", str(last_response))
                event_text = f"Round {i + 1}:\n{st.session_state.discuss_text}"
            if j != 2:
                role.event(event_text)
                response = role.ask()
                response = response if f"Round {i + 1}" in response else f"Round {i + 1}\n{response}"
                role.memory(response)
            else:
                response = st.session_state.discuss_text

            self.render_chat_history("Discuss Agent", role_info["name"], role_info["color"],
                                     response.replace(f"Round {i + 1}", ""))
            st.session_state[f"round_{i}_responses"].append(f"{role_info['name']}: {response}")

            # 前进一位角色
            st.session_state.current_role += 1
            if st.session_state.current_role >= len(roles):
                # 本轮结束
                st.session_state.discuss_response.append(
                    f"Round {i + 1}: {st.session_state[f'round_{i}_responses']}"
                )
                del st.session_state[f'round_{i}_responses']
                st.session_state.current_round += 1
                st.session_state.current_role = 0
                st.session_state.input_finished = False
                st.session_state.discuss_text = ""
                st.session_state.human_input = ""

            st.rerun()

        # ----------- Facilitator Summary ------------
        else:
            # Closing (F4)
            st.session_state.discuss_responses.append(st.session_state.discuss_response)
            close_prompt = self.config["Facilitator"]["task4"].replace(
                "[discuss_responses]", str(st.session_state.discuss_response)
            ).replace("[code]", code)
            st.session_state.Facilitator.event(close_prompt)
            close = st.session_state.Facilitator.ask()
            st.session_state.Facilitator.memory(close, False)
            close_response = json.loads(close.replace('```', '').replace('json', '').strip())
            self.render_chat_history("Discuss Agent", "Facilitator(Final conclusion)", "⚖️",
                                     json.dumps(close_response, ensure_ascii=False, indent=2))

            # Process Final Result
            st.session_state.close_resolution = close_response["Resolution"]
            if close_response["Resolution"].strip().lower() == "retain":
                st.session_state.final_code = close_response["final_code"]
                st.session_state.final_justification = close_response["definition"]

            # 清除起始标记，允许重复运行
            del st.session_state.discuss_started


if __name__ == "__main__":
    discuss_config = import_json("config/discuss_config.json")
    models_name = {
        "Role1": "gpt-4o-mini",
        "Role2": "gpt-4o-mini",
        "Human": "gpt-4o-mini",
        "Facilitator": "gpt-4o-mini",
    }
    app = MultiAgentsHumanDiscussion(discuss_config, models_name)
    app.init_session()
    app.run("LLMs-HumanOutput")
