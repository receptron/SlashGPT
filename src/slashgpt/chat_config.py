from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from slashgpt.llms.default_config import default_llm_engine_configs, default_llm_models
from slashgpt.llms.model import LlmModel
from slashgpt.utils.print import print_warning

if TYPE_CHECKING:
    from slashgpt.manifest import Manifest


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

    @classmethod
    def __get_default_llm_model_name(cls, llm_models: dict):
        default_key = next(filter(lambda key: llm_models[key].get("default"), llm_models.keys()), None)
        return llm_models.get(default_key)

    @classmethod
    def __search_llm_model(cls, llm_model_name: str, llm_models: dict = {}):
        llm_model_list = list(map(lambda x: x.get("model_name"), llm_models.values()))
        index = llm_model_list.index(llm_model_name) if llm_model_name in llm_model_list else -1

        if index > -1:
            llm_model = list(llm_models.values())[index]
            return llm_model
        else:
            print_warning(f"ChatConfig: Failed to find the model {llm_model_name}")
            return cls.__get_default_llm_model_name(llm_models)

    def get_default_llm_model(self):
        """Returns the LLM model specified as the default LLM in the llm_models"""
        return LlmModel(ChatConfig.__get_default_llm_model_name(self.llm_models), self.llm_engine_configs)

    def get_llm_model_from_manifest(self, manifest: Manifest):
        """Returns the LLM model specified in the manifest"""
        model = manifest.model()
        if isinstance(model, dict):
            # This code enables llm model definition embedded in the manifest file
            llm_model = model
            llm_model_name = model.get("model_name")
        else:
            llm_model_name = model
            llm_model = ChatConfig.__search_llm_model(llm_model_name, self.llm_models)

        return LlmModel(llm_model, self.llm_engine_configs)

    def get_llm_model_from_key(self, key: str):
        """Returns a specific LLM model"""
        llm_model = self.llm_models.get(key)
        if llm_model:
            return LlmModel(llm_model, self.llm_engine_configs)
        return self.get_default_llm_model()
