from lib.chat_config import ChatConfig

class LlmModel:
    def __init__(self, llm_model_data):
        self.llm_model_data = llm_model_data

    def get(self, key):
        return self.llm_model_data.get(key)

    def name(self):
        return self.get('model_name')
    
    def max_token(self):
        return self.get("max_token") or 4096

    def check_api_key(self, config: ChatConfig):
        if self.get("api_key"):
            return config.has_value_for_key(self.get("api_key"));
        return True
        
    def replicate_model(self):
        if self.get("replicate_model"):
            return self.get("replicate_model")

        # TODO default replicate model
        return "a16z-infra/llama7b-v2-chat:a845a72bb3fa3ae298143d13efa8873a2987dbf3d49c293513cd8abf4b845a83"
        
