from utils.Function import import_json, save_json
from utils.Agent import Agent
import json

meta_promt = '''
**#Introduce**

You are given two code snippets. The goal is to determine whether they are semantically consistent with each other.

**#Task description**

Your task is to compare the two provided codes and generate two results:

1. **Semantic match — assign 1 when two codes represent equivalent or highly similar meanings (semantic consistency in concept or intent), and 0 when they diverge semantically or refer to distinct concepts.
2. **Confidence score** — provide a decimal number between 0 and 1 that indicates your confidence in the semantic match judgment.

**# Requirements**

- Only consider semantic consistency, not formatting or stylistic differences.
- Confidence must always be between 0 and 1.
- The semantic match must be exactly 0 or 1 (no other values allowed).
- Be concise and objective, avoiding any explanation outside of the required outputs.

**#Output Format**

Strictly output in the following JSON structure:
{
  "semantic_match": 0 or 1,
  "confidence": 0.x
}
'''


def pr_code(code_deb, code_gt):
    # 全部转小写，避免大小写不一致
    deb_set = set([c.lower() for c in code_deb])
    gt_set = set([c.lower() for c in code_gt])

    TP = len(deb_set & gt_set)  # 交集
    FP = len(deb_set - gt_set)  # 多预测的
    FN = len(gt_set - deb_set)  # 漏掉的

    precision = TP / (TP + FP) if (TP + FP) > 0 else 0.0
    recall = TP / (TP + FN) if (TP + FN) > 0 else 0.0

    return precision, recall


def judge_pr_code(code_deb, code_gt):
    judge_eval = Agent(
        model_name="gpt-4o-mini",
        name="judge eval",
        api_key="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",
    )
    judge_eval.set_meta_prompt(meta_promt)
    sem_matrix, conf_matrix = [], []
    for code1 in code_deb:
        row_sem, row_conf = [], []
        for code2 in code_gt:
            judge_eval.event(f"The two codes are {code1} and {code2}")
            pr0 = judge_eval.ask()
            pr = json.loads(pr0)
            judge_eval.memory(pr0, False, False)
            # 规范化
            sem = int(pr.get("semantic_match", 0) in (1, "1", True))
            conf = float(pr.get("confidence", 0.0))

            row_sem.append(sem)
            row_conf.append(conf)
        sem_matrix.append(row_sem)
        conf_matrix.append(row_conf)

    TP_pred = sum(1 if sum(row) >= 1 else 0 for row in sem_matrix)
    precision = TP_pred / len(code_deb) if TP_pred <= len(code_deb) else 1

    col_sums = [sum(sem_matrix[i][j] for i in range(len(code_deb))) for j in range(len(code_gt))]
    col_hits = [1 if s >= 1 else 0 for s in col_sums]
    TP_gt = sum(col_hits)
    recall = TP_gt / len(code_gt) if TP_gt <= len(code_gt) else 1

    return precision, recall, conf_matrix


if __name__ == '__main__':
    Codebook = import_json(r"F:\Work\Debate\MultiAgentDabateDataAnnotation\Data\Scrum-interviews\output\codebook0.json")
    for i, codebook in enumerate(Codebook):
        code_deb = [code["code"].lower() for code in codebook["Codebook"]]
        code_gt = [code.lower() for code in codebook["Code_GroundTruth"]]
        print(f"---------------- evaluate {i} ----------------")
        p, r = pr_code(set(code_deb), set(code_gt))
        print(f"Precision: {p:.4f}, Recall: {r:.4f}")

        p, r, conf_matrix = judge_pr_code(code_deb, code_gt)
        print(f"Precision: {p:.4f}, Recall: {r:.4f},"
              f"llm_judge_conf: {sum(sum(row) for row in conf_matrix) / sum(len(row) for row in conf_matrix):.4f}")
