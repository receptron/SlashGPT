import json
import os
import re
from typing import Optional

from lib.chat_config import ChatConfig

"""
ChatSlashConfig is a singleton, which holds global states, including various secret keys and the list of manifests for SlashGPT app.
"""


class ChatSlashConfig(ChatConfig):
    def __init__(self, pathManifests: str):
        super().__init__()
        self.audio: Optional[str] = None
        self.load_manifests(pathManifests)

    """
    Load a set of manifests.
    It's called initially, but it's called also when the user makes a request to switch the set (such as roles1).
    """

    def load_manifests(self, path: str):
        self.manifests = {}
        files = os.listdir(path)
        for file in files:
            if re.search(r"\.json$", file):
                with open(f"{path}/{file}", "r", encoding="utf-8") as f:  # encoding add for Win
                    self.manifests[file.split(".")[0]] = json.load(f)

    def __get_manifests_keys(self):
        return sorted(self.manifests.keys())

    def help_list(self):
        return (f"/{(key+'         ')[:12]} {self.manifests.get(key).get('title')}" for key in self.__get_manifests_keys())

    def has_manifest(self, key: str):
        return key in self.manifests
