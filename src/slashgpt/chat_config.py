from typing import Optional

from dotenv import load_dotenv

from slashgpt.llms.default_config import default_llm_engine_configs, default_llm_models
from slashgpt.llms.engine_factory import LLMEngineFactory

"""
ChatConfig is a singleton, which holds global states, including various secret keys
"""


class ChatConfig:
    def __init__(self, base_path: str, llm_models: Optional[dict] = None, llm_engine_configs: Optional[dict] = None):
        self.base_path = base_path
        # Load various keys from .env file
        load_dotenv()

        self.verbose = False

        self.llm_models = (
            {
                **default_llm_models,
                **llm_models,
            }
            if llm_models
            else default_llm_models
        )
        self.llm_engine_configs = {**default_llm_engine_configs, **llm_engine_configs} if llm_engine_configs else default_llm_engine_configs
        # engine
        if self.llm_engine_configs:
            LLMEngineFactory.llm_engine_configs = self.llm_engine_configs
