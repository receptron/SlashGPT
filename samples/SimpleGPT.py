#!/usr/bin/env python3
# python -m samples.SimpleGPT
import json
import platform

from termcolor import colored

from lib.chat_config_base import ChatConfigBase
from lib.chat_session import ChatSession

if platform.system() == "Darwin":
    # So that input can handle Kanji & delete
    import readline  # noqa: F401


with open("./manifests/main/names.json", "r") as f:
    manifest = json.load(f)


class Main:
    def __init__(self, config: ChatConfigBase, manifest_key: str):
        self.config = config
        manifest = config.get_manifest()
        self.session = ChatSession(self.config, manifest=manifest, manifest_key=manifest_key)
        print(colored(f"Activating: {self.session.title}", "blue"))

        self.session.set_intro()
        if self.session.intro_message:
            self.print_bot(self.session.intro_message)

    def process_llm(self, session):
        try:
            (res, function_call) = session.call_llm()

            if res:
                self.print_bot(res)

            if function_call:
                (
                    function_message,
                    function_name,
                    should_call_llm,
                ) = function_call.process_function_call(
                    session.manifest,
                    session.history,
                    None,
                )
                if function_message:
                    self.print_function(function_name, function_message)

                if should_call_llm:
                    self.process_llm()

        except Exception as e:
            print(colored(f"Exception: Restarting the chat :{e}", "red"))

    """
    the main loop
    """

    def start(self):
        while True:
            self.talk_with_input()

    def talk_with_input(self):
        question = input(f"\033[95m\033[1m{self.session.userName}: \033[95m\033[0m").strip()

        if question:
            self.session.append_user_question(self.session.manifest.format_question(question))
            self.process_llm(self.session)

    def print_bot(self, message):
        print(f"\033[92m\033[1m{self.session.botName}\033[95m\033[0m: {message}")

    def print_function(self, function_name, message):
        print(f"\033[95m\033[1mfunction({function_name}): \033[95m\033[0m{message}")


if __name__ == "__main__":
    config = ChatConfigBase()
    config.set_manifest(manifest)
    main = Main(config, "names")
    main.start()
