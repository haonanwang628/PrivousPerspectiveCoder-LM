# model menu
MODEL_TOKENIZER_MAP = {
    "deepseek-chat": "cl100k_base",
    "deepseek-reasoner": "cl100k_base",
}

llm_MaxToken = {
    "deepseek-chat": 8000,
    "deepseek-reasoner": 10000,
    "gpt-4o-mini": 16384
}

available_models = ["deepseek-chat", "gpt-4o-mini", "Claude"]

api_key = {
    "gpt-4o-mini": "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",
    "deepseek-chat": "sk-9bc06d1289704b05b7b52db5285dba67",
    "deepseek-reasoner": "sk-9bc06d1289704b05b7b52db5285dba67"
}

base_url = {
    "gpt-4o-mini": "",
    "deepseek-chat": "https://api.deepseek.com/v1",
    "deepseek-reasoner": "https://api.deepseek.com/v1",
}
