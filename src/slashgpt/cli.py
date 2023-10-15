#!/usr/bin/env python3
import argparse
import importlib
import json
import os
import sys

from slashgpt.llms.engine.palm import LLMEnginePaLM
from slashgpt.SlashGPT import ChatSlashConfig, SlashGPT
from slashgpt.utils.help import ONELINE_HELP

my_llm_engine_configs = {
    "palm": LLMEnginePaLM,
}

my_llm_models = {
    "palm": {
        "engine_name": "palm",
        "model_name": "palm",
        "api_key": "GOOGLE_PALM_KEY",
    },
}


def cli(base_dir: str = ""):
    parser = argparse.ArgumentParser(description="SlashGPT: LLM Playgroud")
    parser.add_argument("--autotest", action="store_true")
    parser.add_argument("--agent", default="dispatcher")
    parser.add_argument("--llm-config")
    parser.add_argument("--run")

    args = parser.parse_args()

    current_dir = base_dir if base_dir != "" else os.path.dirname(__file__)

    with open(current_dir + "/manifests/manifests.json", "r") as f:
        manifests_manager = json.load(f)

    dir = manifests_manager["main"]["manifests_dir"]

    if args.llm_config:
        sys.path.append(os.getcwd())
        module = importlib.import_module(args.llm_config)
        llm_models = getattr(module, "llm_models")
        llm_engine_configs = getattr(module, "llm_engine_configs")
        config = ChatSlashConfig(current_dir, current_dir + "/" + dir, llm_models, llm_engine_configs)
    else:
        config = ChatSlashConfig(current_dir, current_dir + "/" + dir, my_llm_models, my_llm_engine_configs)

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
