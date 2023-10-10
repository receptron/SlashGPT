#!/usr/bin/env python3
# python -m samples.SimpleGPT2
import json
import os
import platform
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))

from slashgpt.chat_config import ChatConfig  # noqa: E402
from slashgpt.chat_session import ChatSession  # noqa: E402
from slashgpt.utils.print import print_bot, print_info  # noqa: E402

if platform.system() == "Darwin":
    # So that input can handle Kanji & delete
    import readline  # noqa: F401


with open("./manifests/main/names.json", "r") as f:
    manifest = json.load(f)


class SimpleGPT2:
    def __init__(self, config: ChatConfig, agent_name: str):
        self.session = ChatSession(config, manifest=manifest, agent_name=agent_name)
        print_info(f"Activating: {self.session.title()}")

        if self.session.intro_message:
            print_bot(self.session.botname(), self.session.intro_message)

    def callback(self, callback_type, data):
        if callback_type == "bot":
            print_bot(self.session.botname(), data)

    def process_llm(self, session):
        self.session.call_loop(self.callback)

    def start(self):
        while True:
            question = input(f"\033[95m\033[1m{self.session.username()}: \033[95m\033[0m").strip()
            if question:
                self.session.append_user_question(self.session.manifest.format_question(question))
                self.process_llm(self.session)


if __name__ == "__main__":
    path = os.path.join(os.path.dirname(__file__), "../")
    config = ChatConfig(path)
    main = SimpleGPT2(config, "names")
    if len(sys.argv) == 2 and sys.argv[1] == "test":
        sys.exit()
    main.start()
