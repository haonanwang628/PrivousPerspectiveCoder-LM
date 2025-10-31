import argparse
from utils.Agent_debate import DebateModel, SingleModel
from utils.Function import import_json, save_json, roles_identity_generate


def experiment_debate(texts, model_name, debate_config, rq=None):
    roles = ["Role1", "Role2", "Role3", "Facilitator"]

    if isinstance(model_name, list):
        models_name = dict(zip(roles, args.model_name))
    elif isinstance(model_name, str):
        models_name = {role: model_name for role in roles}
    else:
        return

    roles_identity = roles_identity_generate(len(models_name) - 1)  # 固定随机数种子生成
    # roles_identity = roles_identity_generate(1)
    # roles_identity = [roles_identity[0] for _ in range(3)]

    codebook = []
    num_token = 0
    roles_positionality_cached = None

    for i, text in enumerate(texts):
        if i > 15:
            break

        print(f"------------Current Target Text {i + args.start_step}------------")

        debate = DebateModel(debate_config, models_name)
        debate.target_text = text["data_chunk"]
        code_gt = text["code"]

        roles, Facilitator = debate.agents_init()
        if roles_positionality_cached is None and args.start_step == 0:
            roles_positionality_cached, roles_annotate = debate.role_stage(roles, roles_identity, rq=rq,
                                                                           roles_positionality=None)
            save_json(f"{args.output_dir}\debate_process\\role_positionality.json", roles_positionality_cached)
        else:
            if args.start_step > 0:
                roles_positionality_cached = import_json(
                    f"{args.output_dir}\debate_process\\role_positionality.json")
            _, roles_annotate = debate.role_stage(roles, roles_identity, rq=rq,
                                                  roles_positionality=roles_positionality_cached)
        # roles_positionality_cached = import_json(f"{args.output_dir}\debate_process\json\\roles_positionality.json")
        # _, roles_annotate = debate.role_stage(roles, roles_identity, rq=rq,
        #                                       roles_positionality=roles_positionality_cached)

        for role_id, positionality in zip(roles_identity, roles_positionality_cached):
            role_id["positionality"] = positionality

        agree_disagree, disagree_explain = debate.agree_disagree(Facilitator, roles_annotate)
        debate_process, disagree_to_agree = [], []
        for disagree in agree_disagree["Disagreed"]:
            print(f"Disagree [{disagree['code']}] Debating")
            debate_responses, close_response = debate.single_disagree_debate(roles, roles_identity, Facilitator,
                                                                             disagree)

            for role in roles:
                role.memory_lst = role.memory_lst[:-4]

            debate_process.append({
                "Disagreed": disagree["code"],
                "Process": debate_responses,
                "Closing": close_response
            })
            if close_response["Resolution"].strip().lower() == "retain":
                disagree_to_agree.append({
                    "*code": close_response["final_code"],
                    "*definition": close_response["definition"]
                })

        current_token = sum(role.num_token for role in roles)
        current_token += Facilitator.num_token
        print(f"Current tokens spent: {current_token}")
        print(f"Debate Finish !!!")

        result = {
            "target_text": text["data_chunk"],
            "Role_Team": roles_identity,
            "Role_init_codebook": roles_annotate,
            "Consolidating_results": agree_disagree,
            "disagree_explain": disagree_explain,
            "Debate": debate_process,
            "Codebook": agree_disagree["Agreed"] + disagree_to_agree,
        }
        codebook.append({"target_text": text["data_chunk"],
                         "Code_GroundTruth": code_gt,
                         "Codebook_Pre": roles_annotate,
                         "Codebook": agree_disagree["Agreed"]})
        # save every target debate process
        save_json(f"{args.output_dir}\debate_process\json\debate_{args.start_step + i}.json", result)
        num_token += current_token

    print(f"Total tokens spent: {num_token}")
    # save data codebook
    save_json(f"{args.output_dir}\debate_process\codebook.json", codebook)


def experiment_baseline1(texts, model_name, SingleLLM_config):
    SingleLLM = SingleModel(SingleLLM_config, model_name)
    agent = SingleLLM.agent_init()

    for i, text in enumerate(texts):
        if i > 15:
            break
        print(f"------------Current Target Text {i + args.start_step}------------")
        SingleLLM.target_text = text["data_chunk"]
        annotate = SingleLLM.baseline1_codebook_generate(agent)
        codebook = {"target_text": text["data_chunk"],
                    "Codebook": annotate}
        save_json(f"{args.output_dir}\\baseline1\\json\\baseline1_{i}.json", codebook)
        print(f"Finish !")


def experiment_baseline2(texts, model_name, debate_config, rq=None):
    debate = DebateModel(debate_config, {"role1": model_name})
    roles_identitys = roles_identity_generate(3)

    for j, roles_identity in enumerate(roles_identitys):
        roles_positionality_cached = None
        roles_identity = [roles_identity]
        for i, text in enumerate(texts):
            if i > 15:
                break
            print(f"------------Current Target Text {i + args.start_step}------------")
            debate.target_text = text["data_chunk"]

            roles, _ = debate.agents_init(False)
            if roles_positionality_cached is None and args.start_step == 0:
                roles_positionality_cached, roles_annotate = debate.role_stage(roles, roles_identity, rq=rq,
                                                                               one_role=True,
                                                                               roles_positionality=None)
                save_json(f"{args.output_dir}\\baseline2\\role_positionality.json", roles_positionality_cached)
            else:
                if args.start_step > 0:
                    roles_positionality_cached = import_json(
                        f"{args.output_dir}\\baseline2\\role_positionality.json")
                _, roles_annotate = debate.role_stage(roles, roles_identity, rq=rq, one_role=True,
                                                      roles_positionality=roles_positionality_cached)
            # roles_positionality_cached = import_json(f"{args.output_dir}\debate_process\json\\roles_positionality.json")
            # _, roles_annotate = debate.role_stage(roles, roles_identity, rq=rq, one_role=True,
            #                                       roles_positionality=roles_positionality_cached)
            for role_id, positionality in zip(roles_identity, roles_positionality_cached):
                role_id["positionality"] = positionality
            codebook = {"target_text": text["data_chunk"],
                        "Role": roles_identity,
                        "Codebook": roles_annotate}
            save_json(f"{args.output_dir}\\baseline2\\json\\baseline2_role{j + 1}_{i}.json", codebook)
            print(f"Finish !")


# def experiment_baseline3(texts, model_name, SingleLLM_config):
#     SingleLLM = SingleModel(SingleLLM_config, model_name)
#     agent = SingleLLM.agent_init()
#     codebook = []
#     roles_identity = roles_identity_generate(3)  # 固定随机数种子生成
#     for i, text in enumerate(texts):
#         print(f"------------Current Target Text {i + args.start_step}------------")
#         SingleLLM.target_text = text["data_chunk"]
#         annotate = SingleLLM.baseline23_codebook_generate(agent, roles_identity)
#         codebook.append({"target_text": text["data_chunk"],
#                          "Role_Team": roles_identity,
#                          "Codebook": annotate})
#         print(f"Finish !")
#     save_json(f"{args.output_dir}\\baseline3\codebook.json", codebook)


def parse_args():
    parser = argparse.ArgumentParser("", formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("-i", "--input-file", type=str,
                        default=r"F:\Work\Debate\MultiAgentDabateDataAnnotation\Data\Scrum-interviews\processed\Scrum.json",
                        help="raw_text Input file path")
    parser.add_argument("-o", "--output-dir", type=str,
                        default=r"F:\Work\Debate\MultiAgentDabateDataAnnotation\Data\Scrum-interviews\output",
                        help="Codebook and debate output file dir")
    parser.add_argument("-c", "--config-dir", type=str,
                        default=r"F:\Work\Debate\MultiAgentDabateDataAnnotation\config\discuss_config.json",
                        help="config file dir")
    parser.add_argument("-m", "--model-name", type=str, default="gpt-4o-mini", help="Model name")
    # parser.add_argument("-t", "--temperature", type=float, default=0, hewlp="Sampling temperature")

    parser.add_argument("-s", "--start-step", type=float, default=0, help="Data iteration starting step")
    parser.add_argument("-exp", "--experiment-name", type=float, default=2,
                        help="0: debate, 1: baseline1, 2: baseline2")

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    target_texts = import_json(args.input_file)
    target_texts = target_texts[args.start_step:]
    config = import_json(args.config_dir)

    if args.experiment_name == 0:
        experiment_debate(target_texts, args.model_name, config)
    elif args.experiment_name == 1:
        experiment_baseline1(target_texts, args.model_name, config)
    elif args.experiment_name == 2:
        experiment_baseline2(target_texts, args.model_name, config)
