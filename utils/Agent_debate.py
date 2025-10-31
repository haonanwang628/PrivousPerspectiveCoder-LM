import json
from utils.Agent import Agent
from config.model_menu import *
import random

random.seed(3)


class DebateModel:
    def __init__(self, debate_config, models_name):
        self.config = debate_config
        self.models_name = models_name
        self.target_text = ""

    def agents_init(self, Fac=True):
        roles = []
        for i, role in enumerate(self.models_name):
            roles.append(
                Agent(
                    model_name=self.models_name[role],
                    name=role,
                    api_key=api_key[self.models_name[role]],
                    base_url=base_url[self.models_name[role]]
                ))

        return roles, roles.pop() if Fac else None

    def role_stage(self, roles, roles_identity, rq=None, one_role=False, roles_positionality=None):
        roles_annotate, roles_positionality_cached, role_prompt = [], [], []
        for i, role in enumerate(roles):
            if rq is not None:
                pos_prompt = self.config["role_prompt"]["positionality_rq"] \
                    .replace("[user response]", rq)
            else:
                pos_prompt = self.config["role_prompt"]["positionality"]
            pos_prompt = pos_prompt \
                .replace("[insert]", roles_identity[i]["role"], 1) \
                .replace("[insert]", roles_identity[i]["Intended_Study_Level"], 1) \
                .replace("[insert]", roles_identity[i]["Subject"], 1) \
                .replace("[insert]", roles_identity[i]["Research_Interest"], 1) \
                .replace("[insert]", roles_identity[i]["Dimensions_Source"], 1)
            # roles system
            role.set_meta_prompt(self.config["role_prompt"]["system"])

            # roles positionality statement
            role.event(pos_prompt)
            if roles_positionality is None:
                role_response = role.ask()
                roles_positionality_cached.append(role_response)
                role.memory(role_response, True)
            else:
                role.memory(roles_positionality[i], False)

            # roles codebook generate
            if not one_role:
                role.event(self.config["role_prompt"]["task"].replace("[Target Text]", self.target_text))
            else:
                role.event(self.config["role_prompt"]["task"].replace("[Target Text]", self.target_text))
            role_response = role.ask()
            role.memory(role_response, False)
            try:
                parsed = json.loads(role_response)
            except Exception:
                parsed = json.loads(eval(role_response.replace('```', "'''").replace('json', '').strip()))
            roles_annotate.append(parsed)
        return None if None else roles_positionality_cached, roles_annotate

    # def positionality_generate(self, roles):
    #     roles_positionality = []
    #     for role in roles:
    #         # roles positionality statement
    #         role.event(self.config["role_prompt"]["positionality"])
    #         role_response = role.ask()
    #         roles_positionality.append(role_response)
    #         role.memory(role_response, True)
    #
    #     return roles_positionality
    #
    # def init_codebook_generate(self, roles):
    #     roles_annotate = []
    #     for role in roles:
    #         # roles codebook generate
    #         role.event(self.config["role_prompt"]["task"].replace("[Target Text]", self.target_text))
    #         role_response = role.ask()
    #         role.memory(role_response, False)
    #         roles_annotate.append(
    #             json.loads(role_response.replace('```', "").replace('json', '').strip()))
    #
    #     return roles_annotate

    def agree_disagree(self, Facilitator, roles_annotate):
        # Agree_Disagree_stage (F2)
        agree_agent_infer = self.config["Facilitator"]["system"]
        Facilitator.set_meta_prompt(agree_agent_infer)
        Facilitator.event(self.config["Facilitator"]["task2"]
                          .replace("[codes and justifications]", str(roles_annotate))
                          .replace("[Target Text]", self.target_text))
        view = Facilitator.ask()
        Facilitator.memory(view, False)
        agree_disagree = json.loads(eval(view.replace('```', "'''").replace('json', '').strip()))

        # Debate Ready (F3)
        Facilitator.event(self.config["Facilitator"]["task3"]
                          .replace("[Target Text]", self.target_text)
                          .replace("[ROLE_CODEBOOKS]", str(roles_annotate))
                          .replace("[Disagreed]", str(agree_disagree["Disagreed"])))
        disagree_explain = Facilitator.ask()
        Facilitator.memory(disagree_explain, False)
        return agree_disagree, disagree_explain

    def single_disagree_debate(self, roles, roles_identity, Facilitator, disagree):
        meta_prompt = self.config["role_discussant"]["system"].replace("[Target Text]", self.target_text).replace(
            "[code and justification]", str([{"code": disagree["code"], "definition": disagree["definition"]}]))
        for role, meta in zip(roles, roles_identity):
            role.memory_lst.clear()
            role.set_meta_prompt(meta_prompt)

        roles_update = [
            {"name": f"Role1({roles_identity[0]['role']})", "obj": roles[0]},
            {"name": f"Role2({roles_identity[1]['role']})", "obj": roles[1]},
            {"name": f"Role3({roles_identity[2]['role']})", "obj": roles[2]}
        ]

        # Debating
        debate_responses = []
        for i, debate in enumerate(self.config["role_discussant"]["discuss_round"].items()):
            roles_responses = []
            for role_info in roles_update:
                role = role_info["obj"]
                if i == 0 or i == 3:
                    role.event(f"Round {i + 1}:\n{debate}".replace("[code]", disagree["code"]).replace("[code]",
                                                                                                       disagree[
                                                                                                           "code"]))
                else:
                    # role.event(f"Round {i + 1}:\n{debate}".replace("[response]", str(debate_responses[-1])))
                    role.event(f"Round {i + 1}:\n{debate}")
                response = role.ask()
                response = response if f"Round {i + 1}" in response else f"Round {i + 1}\n{response}"
                roles_responses.append(f"{role_info['name']}: {response}")
                role.memory(response)
            # include roles_responses of every round
            debate_responses.append({"response": f"{roles_responses}"})

        # Closing (F4)
        close_prompt = self.config["Facilitator"]["task4"] \
            .replace("[discuss_responses]", str(debate_responses)).replace("[code]", disagree["code"])
        Facilitator.event(close_prompt)
        close = Facilitator.ask()
        Facilitator.memory(close, False)
        close_response = json.loads(close.replace('```', '').replace('json', '').strip())

        return debate_responses, close_response


class SingleModel:
    def __init__(self, config, models_name):
        """Create a Debate Model
        Args:
            debate_config: debate prompt and debate progress design
            models_name: multi Agents(roles and Facilitator) models name,
        """
        self.config = config
        self.models_name = models_name

        self.target_text = ""

    def agent_init(self):
        """
            return: roles and Facilitator Agent.
        """
        agent = Agent(
            model_name=self.models_name,
            name="SingleLLM",
            api_key=api_key[self.models_name],
            base_url=base_url[self.models_name]
        )
        return agent

    def baseline1_codebook_generate(self, agent):
        agent.event(
            self.config["Setting_1"]["Inductive_coding"].replace("[Target Text]", self.target_text))
        reply = agent.ask()
        agent.memory(reply, False)
        reply = json.loads(reply.replace('```', "").replace('json', '').strip())

        return reply

    # def baseline2_codebook_generate(self, agent, roles_identity):
    #     roles = []
    #     for meta in roles_identity:
    #         role_prompt = self.config["Setting_2-3"]["system"] \
    #             .replace("[Role Id]", meta["role"]) \
    #             .replace("[Disciplinary Background]", meta["Disciplinary_Background"]) \
    #             .replace("[Area of Concern]", meta["Area_of_Concern"]) \
    #             .replace("[Scope & Values]", meta["Scope_Values"]) \
    #             .replace("[Methodology]", meta["Methodology"]) \
    #             .replace("[Personal Identity Influence]", meta["Personal_Identity_Influence"])
    #         roles.append(role_prompt)
    #
    #     agent.event(self.config["Setting_2-3"]["config"]
    #                 .replace("[Target Text]", self.target_text)
    #                 .replace("[Role A identity]", roles[0])
    #                 .replace("[Role B identity]", roles[1])
    #                 .replace("[Role C identity]", roles[2]))
    #     reply = agent.ask()
    #     reply = json.loads(reply.replace('```', "").replace('json', '').strip())
    #     agent.memory(reply, False)
    #
    #     return reply
