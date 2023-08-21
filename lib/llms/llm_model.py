class LlmModel:
    def __init__(self, llm_model_data):
        self.llm_model_data = llm_model_data

    def get(self, key):
        return self.llm_model_data.get(key)

    def max_token(self):
        return self.get("max_token") or 4096

