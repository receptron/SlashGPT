#!/usr/bin/env python3
# python -m samples.AgentGPT
import json
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))

from slashgpt import ChatConfigWithManifests, ChatSession  # noqa: E402


class Main:
    def __init__(self, config: ChatConfigWithManifests):
        with open("./manifests/agents/chomsky.json", "r") as f:
            self.sessionA = ChatSession(config, manifest=json.load(f), agent_name="chomsky")
        with open("./manifests/agents/tawara.json", "r") as f:
            self.sessionB = ChatSession(config, manifest=json.load(f), agent_name="tawara")

    def start(self, theme):
        print(f"\033[92m\033[1mテーマ\033[95m\033[0m: {theme}")
        self.sessionB.append_user_question(theme)

        if len(sys.argv) == 2 and sys.argv[1] == "test":
            sys.exit()

        self.talk_with_input(theme, self.sessionA)
        while True:
            last_message_a = self.sessionA.history.last()
            self.talk_with_input(last_message_a["content"], self.sessionB)
            last_message_b = self.sessionB.history.last()
            self.talk_with_input(last_message_b["content"], self.sessionA)

    def talk_with_input(self, question, session):
        session.append_user_question(question)
        (message, _, _) = session.call_llm()

        if message:
            print(f"\033[92m\033[1m{session.botname()}\033[95m\033[0m: {message}")


if __name__ == "__main__":
    current_dir = os.path.join(os.path.dirname(__file__), "../")

    config = ChatConfigWithManifests(current_dir, current_dir + "/manifests/agents")
    main = Main(config)
    main.start("自由と国家について")
