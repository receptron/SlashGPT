#!/usr/bin/env python3
import json
import platform
import re

from gtts import gTTS
from playsound import playsound
from termcolor import colored

from lib.chat_config import ChatConfig
from lib.chat_session import ChatSession
from lib.function.jupyter_runtime import PythonRuntime
from lib.llms.models import get_llm_model_from_key, llm_models
from lib.utils.help import LONG_HELP, ONELINE_HELP
from lib.utils.utils import InputStyle

if platform.system() == "Darwin":
    # So that input can handle Kanji & delete
    import readline  # noqa: F401


"""
utility functions for Main class
"""


def play_text(text, lang):
    audio_obj = gTTS(text=text, lang=lang, slow=False)
    audio_obj.save("./output/audio.mp3")
    playsound("./output/audio.mp3")


with open("./manifests/manifests.json", "r") as f:
    manifests = json.load(f)

"""
Main is a singleton, which process the input from the user and manage chat sessions.
"""


class Main:
    def __init__(self, config: ChatConfig, manifest_key: str):
        self.config = config

        self.exit = False
        self.runtime = PythonRuntime("./output/notebooks")
        self.switch_context(manifest_key)

    """
    switchContext terminate the current chat session and start a new.
    The key specifies the AI agent.
    """

    def switch_context(self, manifest_key: str, intro: bool = True):
        if manifest_key is None:
            self.context = ChatSession(self.config)
            return
        if self.config.exist_manifest(manifest_key):
            self.context = ChatSession(self.config, manifest_key=manifest_key)
            if self.config.verbose:
                print(
                    colored(
                        f"Activating: {self.context.title} (model={self.context.llm_model.name()}, temperature={self.context.temperature}, max_token={self.context.llm_model.max_token()})",
                        "blue",
                    )
                )
            else:
                print(colored(f"Activating: {self.context.title}", "blue"))
            if self.context.get_manifest_attr("notebook"):
                (result, _) = self.runtime.create_notebook(
                    self.context.llm_model.name()
                )
                print(
                    colored(
                        f"Created a notebook: {result.get('notebook_name')}", "blue"
                    )
                )

            if intro:
                self.context.set_intro()
            if self.context.intro_message:
                self.print_bot(self.context.intro_message)
        else:
            print(colored(f"Invalid slash command: {manifest_key}", "red"))

    def parse_question(self, question: str):
        key = question[1:].strip()
        commands = re.split(r"\s+", key)
        return (key, commands)

    def detect_input_style(self, question: str):
        (key, commands) = self.parse_question(question)
        if len(question) == 0:
            return InputStyle.HELP
        elif key[:6] == "sample":
            return InputStyle.SAMPLE
        elif question[0] == "/":
            return InputStyle.SLASH
        else:
            return InputStyle.TALK

    def display_oneline_help(self):
        print(ONELINE_HELP)

    def process_sample(self, question: str):
        (key, commands) = self.parse_question(question)
        if commands[0] == "sample" and len(commands) > 1:
            sub_key = commands[1]
            sub_manifest_data = self.config.get_manifest_data(sub_key)
            if sub_manifest_data:
                sample = sub_manifest_data.get("sample")
                if sample:
                    print(sample)
                    return sample
            else:
                agents = self.context.get_manifest_attr("agents")
                if agents:
                    print("/sample {agent}: " + ", ".join(agents))
                else:
                    print(colored(f"Error: No manifest named '{sub_key}'", "red"))
        elif key[:6] == "sample":
            sample = self.context.get_manifest_attr(key)
            if sample:
                print(sample)
                return sample
            print(colored(f"Error: No {key} in the manifest file", "red"))
        return None

    """
    If the question start with "/", process it as a Slash command.
    Otherwise, return (roleInput, question) as is.
    Notice that some Slash commands returns (role, question) as well.
    """

    def process_slash(self, question: str):
        (key, commands) = self.parse_question(question)
        if commands[0] == "help":
            if len(commands) == 1:
                print(LONG_HELP)
                list = "\n".join(self.config.help_list())
                print(f"Agents:\n{list}")
            if len(commands) == 2:
                manifest_data = self.config.get_manifest_data(commands[1])
                if manifest_data:
                    print(json.dumps(manifest_data, indent=2))
        elif key == "bye":
            self.runtime.stop()
            self.exit = True
        elif key == "verbose" or key == "v":
            self.config.verbose = not self.config.verbose
            print(colored(f"Verbose Mode: {self.config.verbose}", "cyan"))
        elif commands[0] == "audio":
            if len(commands) == 1:
                if self.config.audio:
                    self.config.audio = None
                else:
                    self.config.audio = "en"
            elif commands[1] == "off":
                self.config.audio = None
            else:
                self.config.audio = commands[1]
            print(f"Audio mode: {self.config.audio}")
        elif key == "prompt":
            if self.context.history.len() >= 1:
                print(self.context.history.get_data(0, "content"))
            if self.config.verbose and self.context.functions:
                print(colored(self.context.functions, "cyan"))
        elif key == "history":
            print(json.dumps(self.context.history.messages(), indent=2))
        elif key == "functions":
            if self.context.functions:
                print(json.dumps(self.context.functions, indent=2))
        elif commands[0] == "llm" or commands[0] == "llms":
            if len(commands) > 1 and llm_models.get(commands[1]):
                llm_model = get_llm_model_from_key(commands[1])
                self.context.set_llm_model(llm_model)
            else:
                print("/llm: " + ",".join(llm_models.keys()))
        elif key == "new":
            self.switch_context(self.context.manifest_key, intro=False)
        elif key == "autotest":
            self.config.verbose = True
            self.test("dispatcher", "/sample currency")
            self.test("dispatcher", "/sample weather")
            self.test("spacex", "/sample")
            self.test("cal", "/sample")
            self.test("jupyter", "/sample_stock")
            self.config.verbose = False
        elif commands[0] == "switch":
            if len(commands) > 1 and manifests.get(commands[1]):
                m = manifests[commands[1]]
                self.config.load_manifests("./" + m["manifests_dir"])
                self.switch_context(m["default_manifest_key"])
            else:
                print("/switch {manifest}: " + ", ".join(manifests.keys()))
        elif self.config.has_manifest(key):
            self.switch_context(key)
        else:
            print(colored(f"Invalid slash command: {key}", "red"))

    def test(self, key, sample):
        self.switch_context(key)
        question = self.process_sample(sample)
        self.context.append_user_question(question)
        self.process_llm()

    def process_llm(self):
        try:
            # Ask LLM to generate a response.
            # (responseRole, res, function_call) = self.context.generate_response()
            (role, res, function_call) = self.context.call_llm()

            if role and res:
                self.print_bot(res)

                if self.config.audio:
                    play_text(res, self.config.audio)

            if function_call and function_call.function_action and function_call.function_action.has_emit():
                arguments = function_call.arguments()
                action = function_call.function_action

                if action.emit_method() == "switch_session":
                    data = action.emit_data(arguments)
                    self.switch_context(data.get("manifest"), intro=False)
                    self.context.history.append(
                        {"role": "user", "content": data.get("message")}
                    )
                    self.process_llm()
                    return

            if function_call is not None and function_call.should_call():
                (
                    function_message,
                    function_name,
                    role,
                ) = self.context.process_function_call(
                    self.runtime, self.config.verbose
                )
                if function_message:
                    if role == "function":
                        self.print_function(function_name, function_message)
                    else:
                        self.print_user(function_message)
            if self.context.next_llm_call:
                self.process_llm()

        except Exception as e:
            print(colored(f"Exception: Restarting the chat :{e}", "red"))
            self.switch_context(self.context.manifest_key)
            if self.config.verbose:
                raise

    """
    the main loop
    """

    def start(self):
        while not self.exit:
            self.talk_with_input()

    def talk_with_input(self):
        question = input(
            f"\033[95m\033[1m{self.context.userName}: \033[95m\033[0m"
        ).strip()
        mode = self.detect_input_style(question)
        if mode == InputStyle.HELP:
            self.display_oneline_help()
        elif mode == InputStyle.SLASH:
            self.process_slash(question)
        else:
            if mode == InputStyle.SAMPLE:
                question = self.process_sample(question)

            if question:
                self.context.append_user_question(
                    self.context.manifest.format_question(question)
                )
                self.process_llm()

    def print_bot(self, message):
        print(f"\033[92m\033[1m{self.context.botName}\033[95m\033[0m: {message}")

    def print_user(self, message):
        print(f"\033[95m\033[1m{self.context.userName}: \033[95m\033[0m{message}")

    def print_function(self, function_name, message):
        print(f"\033[95m\033[1mfunction({function_name}): \033[95m\033[0m{message}")


if __name__ == "__main__":
    config = ChatConfig("./manifests/main")
    print(ONELINE_HELP)
    main = Main(config, "dispatcher")
    main.start()
