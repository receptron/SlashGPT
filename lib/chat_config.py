import json
import os
import re

import google.generativeai as palm

from lib.chat_config_base import ChatConfigBase

"""
ChatConfig is a singleton, which holds global states, including various secret keys and the list of manifests.
"""


class ChatConfig(ChatConfigBase):
    def __init__(self, pathManifests):
        super().__init__()
        self.load_manifests(pathManifests)  # for main

    """
    Load a set of manifests.
    It's called initially, but it's called also when the user makes a request to switch the set (such as roles1).
    """

    def load_manifests(self, path):
        self.manifests = {}
        files = os.listdir(path)
        for file in files:
            if re.search(r"\.json$", file):
                with open(f"{path}/{file}", "r", encoding="utf-8") as f:  # encoding add for Win
                    self.manifests[file.split(".")[0]] = json.load(f)

    def exist_manifest(self, key):
        return key in self.manifests

    def __get_manifests_keys(self):
        return sorted(self.manifests.keys())

    def help_list(self):
        return (f"/{(key+'         ')[:12]} {self.manifests.get(key).get('title')}" for key in self.__get_manifests_keys())

    def has_manifest(self, key):
        return key in self.manifests
