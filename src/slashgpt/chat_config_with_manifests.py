import json
import os
import re
from typing import Optional

import yaml

from slashgpt.chat_config import ChatConfig


class ChatConfigWithManifests(ChatConfig):
    """
    A subclass of ChatConfig, which maintains the set of manifests loaded from
    a specified folder.
    """

    def __init__(self, base_path: str, path_manifests: str, llm_models: Optional[dict] = None, llm_engine_configs: Optional[dict] = None):
        """
        Args:

            base_path (str): path to the "base" folder.
            path_manifests (str): path to the manifests folder (json or yaml)
            llm_models (dict, optional): collection of custom LLM model definitions
            llm_engine_configs (dict, optional): collection of custom LLM engine definitions
        """
        super().__init__(base_path, llm_models, llm_engine_configs)
        self.manifests: dict = self.__load_manifests(path_manifests)
        """Set of manifests loaded from the specified folder"""
        self.path_manifests: str = path_manifests
        """Location of the folder where manifests were loaded"""

    @classmethod
    def __load_manifests(cls, path: str):
        manifests = {}
        files = os.listdir(path)
        for file in files:
            if re.search(r"\.json$", file):
                with open(f"{path}/{file}", "r", encoding="utf-8") as f:  # encoding add for Win
                    manifests[file.split(".")[0]] = json.load(f)
            elif re.search(r"\.yml$", file):
                with open(f"{path}/{file}", "r", encoding="utf-8") as f:  # encoding add for Win
                    manifests[file.split(".")[0]] = yaml.safe_load(f)
        return manifests

    def switch_manifests(self, path: str):
        """Switch the set of manifests

        Args:

            path (str): path to the manifests folder (json or yaml)
        """
        self.path_manifests = path
        self.reload()

    def reload(self):
        """Reload manifest files"""
        self.manifests = self.__load_manifests(self.path_manifests)

    def has_manifest(self, key: str):
        """Check if a manifest file with a specified name exits
        Args:

            key (str): the name of manifest
        """
        return key in self.manifests
