from lib.chat_config import ChatConfig

class LlmModel:
    def __init__(self, llm_model_data):
        self.llm_model_data = llm_model_data

    def get(self, key):
        return self.llm_model_data.get(key)

    def max_token(self):
        return self.get("max_token") or 4096

    def check_api_key(self, config: ChatConfig):
        if self.get("api_key"):
            return config.has_value_for_key(self.get("api_key"));
        return True
        
