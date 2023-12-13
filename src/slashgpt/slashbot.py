#!/usr/bin/env python3
#  git diff -U9999 | python -m samples.CodeReview
#  git show -U9999 {commits} | python -m samples.CodeReview

import argparse
import json
import os
import sys

import yaml

from slashgpt import ChatConfigWithManifests, ChatSession  # noqa: E402


def run_bot(base_dir: str = ""):
    parser = argparse.ArgumentParser(description="SlashBot: SlashGPT bot")
    if "--list" in sys.argv or "-l" in sys.argv:
        parser.add_argument("agentname", nargs="?")
    else:
        parser.add_argument("agentname")
    parser.add_argument("--manifests", default="main")
    parser.add_argument("--dir", "-d", default="")
    parser.add_argument("--list", "-l", action="store_true")
    args = parser.parse_args()
    manifests = args.manifests
    directory = args.dir

    current_dir = directory if directory else base_dir if base_dir != "" else os.path.dirname(__file__)
    manifests_dir = current_dir + "/manifests/" + manifests

    config = ChatConfigWithManifests(current_dir, manifests_dir)
    if args.list:
        print("Manifest list")
        for manifest_key in config.manifests.keys():
            manifest = config.manifests[manifest_key]
            print(manifest_key + ": " + manifest.get("title", "") + " - " + manifest.get("description", ""))
        return

    agent = args.agentname
    agent_file = manifests_dir + "/" + agent

    if os.path.isfile(agent_file + ".yml"):
        agent_file = agent_file + ".yml"
        with open(agent_file, "r") as f:
            session = ChatSession(config, manifest=yaml.safe_load(f), agent_name=agent)
    elif os.path.isfile(agent_file + ".json"):
        agent_file = agent_file + ".json"
        with open(agent_file, "r") as f:
            session = ChatSession(config, manifest=json.load(f), agent_name=agent)
    else:
        print(agent_file + " (json or yml) file not exists")
        return

    question = ""
    for line in iter(sys.stdin.readline, ""):
        question += line

    session.append_user_question(question)
    (message, _, _) = session.call_llm()

    if message:
        print(f"\033[92m\033[1m{session.botname()}\033[95m\033[0m: {message}")
