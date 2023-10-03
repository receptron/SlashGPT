from typing import Optional

from slashgpt.llms.default_config import default_llm_engine_configs, default_llm_models
from slashgpt.llms.engine_factory import LLMEngineFactory


class ChatConfig:
    """Configuration object (singleton), which holds global states across the app"""

    def __init__(self, base_path: str, llm_models: Optional[dict] = None, llm_engine_configs: Optional[dict] = None):
        """
        Args:

            base_path (str): path to the "base" folder.
            llm_models (dict, optional): collection of custom LLM model definitions
            llm_engine_configs (dict, optional): collection of custom LLM engine definitions
        """
        self.base_path = base_path
        """path to the "base" folder."""
        self.verbose = False
        """boolean flag indicating the verbose mode"""
        self.llm_models = (
            {
                **default_llm_models,
                **llm_models,
            }
            if llm_models
            else default_llm_models
        )
        """collection of LLM model definitions"""
        self.llm_engine_configs = {**default_llm_engine_configs, **llm_engine_configs} if llm_engine_configs else default_llm_engine_configs
        """collection of LLM engine definitions"""
        if self.llm_engine_configs:
            # WARNING: This is a global state
            LLMEngineFactory.llm_engine_configs = self.llm_engine_configs
