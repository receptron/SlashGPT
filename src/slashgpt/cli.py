#!/usr/bin/env python3
import argparse
import json

from config.llm_config import llm_engine_configs, llm_models
from lib.chat_slash_config import ChatSlashConfig
from lib.SlashGPT import SlashGPT
from lib.utils.help import ONELINE_HELP


def cli():
    parser = argparse.ArgumentParser(description="SlashGPT: LLM Playgroud")
    parser.add_argument("--autotest", action="store_true")
    parser.add_argument("--agent", default="dispatcher")
    parser.add_argument("--run")

    args = parser.parse_args()

    with open("./manifests/manifests.json", "r") as f:
        manifests_manager = json.load(f)

    dir = manifests_manager["main"]["manifests_dir"]
    config = ChatSlashConfig("./" + dir, llm_models, llm_engine_configs)
    print(ONELINE_HELP)
    main = SlashGPT(config, manifests_manager, args.agent)
    if args.autotest:
        main.talk("/autotest")
        main.talk("/bye")
    if args.run:
        commands = args.run.split(",")
        for command in commands:
            main.talk(command)

    main.start()
