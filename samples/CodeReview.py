#!/usr/bin/env python3
#  git diff -U9999 | python -m samples.CodeReview
#  git show -U9999 {commits} | python -m samples.CodeReview

import os
import sys

import yaml

sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))

from slashgpt import ChatConfigWithManifests, ChatSession  # noqa: E402


class Main:
    def __init__(self, config: ChatConfigWithManifests):
        with open("./manifests/main/codereview.yml", "r") as f:
            self.sessionA = ChatSession(config, manifest=yaml.safe_load(f), agent_name="codereview")

    def start(self, theme):
        self.talk_with_input(theme, self.sessionA)

    def talk_with_input(self, question, session):
        session.append_user_question(question)
        (message, _, _) = session.call_llm()

        if message:
            print(f"\033[92m\033[1m{session.botname()}\033[95m\033[0m: {message}")


if __name__ == "__main__":
    message = ""
    for line in iter(sys.stdin.readline, ""):
        message += line
    # print(message)

    current_dir = os.path.join(os.path.dirname(__file__), "../")

    config = ChatConfigWithManifests(current_dir, current_dir + "/manifests/main")
    main = Main(config)
    main.start(message)
