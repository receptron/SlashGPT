#!/usr/bin/env python3
import platform
import re
if platform.system() == "Darwin":
    import readline # So that input can handle Kanji & delete
import json
from enum import Enum
from termcolor import colored
from gtts import gTTS
from playsound import playsound

from lib.jupyter_runtime import PythonRuntime
from lib.chat_session import ChatSession
from lib.chat_config import ChatConfig
from lib.common import llms

class InputStyle(Enum):
  HELP = 1
  TALK = 2
  SLASH = 3
  SAMPLE = 4

"""
utility functions for Main class
"""

def play_text(text, lang):
    audio_obj = gTTS(text=text, lang=lang, slow=False)
    audio_obj.save("./output/audio.mp3")
    playsound("./output/audio.mp3")

manifests = {
    "root": {
        "manifests_dir": "manifests/manifests",
        "default_manifest_key": "dispatcher",
    },
    "rpg1": {
        "manifests_dir": "manifests/rpg1",
        "default_manifest_key": "bartender",
    },
    "zoo": {
        "manifests_dir": "manifests/zoo",
        "default_manifest_key": "monkey",
    },
    "roles1": {
        "manifests_dir": "manifests/prompts",
        "default_manifest_key": None,
    },
    "roles2": {
        "manifests_dir": "manifests/roles2",
        "default_manifest_key": None,
    },
};

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
                print(colored(f"Activating: {self.context.title} (model={self.context.model}, temperature={self.context.temperature}, max_token={self.context.max_token})", "blue"))
            else:
                print(colored(f"Activating: {self.context.title}", "blue"))
            if self.context.get_manifest_attr("notebook"):
                (result, _) = self.runtime.create_notebook(self.context.model)
                print(colored(f"Created a notebook: {result.get('notebook_name')}", "blue"))

            if intro:
                self.context.set_intro()
        else:            
            print(colored(f"Invalid slash command: {manifest_key}", "red"))

    def parse_question(self, question: str):
        key = question[1:].strip()
        commands = re.split('\s+', key)
        return (key, commands);
            
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
        print(self.config.ONELINE_HELP)

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
        if question[0] == "/": # TODO remove
            if commands[0] == "help":
                if (len(commands) == 1):
                    print(self.config.LONG_HELP)
                    list = "\n".join(self.config.help_list())
                    print(f"Agents:\n{list}")
                if (len(commands) == 2):
                    manifest_data = self.config.get_manifest_data(commands[1])
                    if (manifest_data):
                       print(json.dumps(manifest_data, indent=2))
            elif key == "bye":
                self.runtime.stop()
                self.exit = True;
            elif key == "verbose":
                self.config.verbose = self.config.verbose == False
                print(f"Verbose Mode: {self.config.verbose}")
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
                if len(self.context.messages) >= 1:
                    print(self.context.messages[0].get("content"))
                if self.config.verbose and self.context.functions:
                    print(self.context.functions)
            elif key == "history":
                print(json.dumps(self.context.messages, indent=2))
            elif key == "functions":
                if self.context.functions:
                    print(json.dumps(self.context.functions, indent=2))
            elif commands[0] == "llm":
                if len(commands) > 1 and llms.get(commands[1]):
                    llm = llms[commands[1]]
                    if llm.get("api_key"):
                        if not self.config.has_value_for_key(llm["api_key"]):
                            print(colored("You need to set " + llm["api_key"] + " to use this model","red"))
                            return
                    if llm.get("max_token"):
                        self.context.set_model(llm.get("model_name"), llm.get("max_token"))
                    else:
                        self.context.set_model(llm.get("model_name"))
                else:
                    print("/llm: " + ",".join(llms.keys()))
            elif key == "new":
                self.switch_context(self.context.manifest_key, intro = False)
            elif commands[0] == "switch":
                if len(commands) > 1 and manifests.get(commands[1]):
                    m = manifests[commands[1]]
                    self.config.load_manifests("./" + m["manifests_dir"])
                    self.switch_context(m["default_manifest_key"])
                else:
                    print("/switch {manifest}: " +  ",".join(manifests.keys()))
            elif self.config.has_manifest(key):
                    self.switch_context(key)
            else:
                print(colored(f"Invalid slash command: {key}", "red"))


    def process_llm(self, role, question, function_name, form = ""):
        skip_input = False
        if form:
            question = form.format(question = question)
        try:
            self.context.append_message(role, question, function_name)
            # Ask LLM to generate a response.
            (responseRole, res, function_call) = self.context.generate_response()

            if responseRole and res:
                print(f"\033[92m\033[1m{self.context.botName}\033[95m\033[0m: {res}")

                if self.config.audio:
                    play_text(res, self.config.audio)

                self.context.append_message(responseRole, res)
                self.context.save_log()

            if function_call:
                (question, function_name) = self.process_function_call(function_call)
                if question:
                    skip_input = True
        except Exception as e:
            print(colored(f"Exception: Restarting the chat :{e}","red"))
            self.switch_context(self.context.manifest_key)
            if self.config.verbose:
                raise
        return (question, function_name, skip_input)

    """
    the main loop
    """    
    def start(self):
        skip_input = False
        while not self.exit:
            form = None
            if skip_input:
                print(f"\033[95m\033[1mfunction({function_name}): \033[95m\033[0m{question}")
                role = "function" if function_name else "user"
                (question, function_name, skip_input) = self.process_llm(role, question, function_name)
            else:
                # Otherwise, retrieve the input from the user.
                question = input(f"\033[95m\033[1m{self.context.userName}: \033[95m\033[0m")
                function_name = None
                if question[:1] == "`":
                    print(colored("skipping form", "blue"))
                    question = question[1:]
                else:
                    form = self.context.get_manifest_attr("form")

                mode = self.detect_input_style(question)
                if mode == InputStyle.HELP:
                    self.display_oneline_help()
                elif mode == InputStyle.SLASH:
                    self.process_slash(question)
                else:
                    if mode == InputStyle.SAMPLE:
                        question = self.process_sample(question)
                    if question:
                        (question, function_name, skip_input) = self.process_llm("user", question, function_name, form)
                    
    def process_function_call(self, function_call):
        function_message = None
        function_name = function_call.get("name")
        arguments = function_call.get("arguments") 
        if arguments and isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)      
                function_call["arguments"] = arguments
            except Exception as e:
                print(colored(f"Function {function_name}: Failed to load arguments as json","yellow"))
                
        print(colored(json.dumps(function_call, indent=2), "blue"))
        '''
        if isinstance(arguments, str):
            params = arguments
        else:
            params = ','.join(f"{key}={function_call["arguments"][key]}" for key in function_call.arguments.keys())
        print(colored(f"Function: {function_name}({params})", "blue"))
        '''
        if function_name:
            action = self.context.get_action(function_name)
            if action:
                if action.is_switch_context():
                    self.switch_context(action.get_manifest_key(arguments),  intro = False)
                    function_name = None # Without name, this message will be treated as user prompt.
                    
                function_message = action.call_api(arguments, self.config.verbose)
            else:
                if self.context.get_manifest_attr("notebook"):
                    if function_name == "python" and isinstance(arguments, str):
                        print(colored("python function was called", "yellow"))
                        arguments = {
                            "code": arguments,
                            "query": self.context.messages[-1]["content"]
                        }
                    function = getattr(self.runtime, function_name)
                else:
                    function = self.context.module and self.context.module.get(function_name) or None
                if function:
                    if isinstance(arguments, str):
                        (result, message) = function(arguments)
                    else:
                        (result, message) = function(**arguments)
                    if message:
                        # Embed code for the context
                        self.context.append_message("assistant", message)
                    if isinstance(result, dict):
                        result = json.dumps(result)
                    result_form = self.context.get_manifest_attr("result_form")
                    if result_form:
                        function_message = result_form.format(result = result)
                    else:
                        function_message = result
                    if self.context.get_manifest_attr("skip_function_result"):
                        print(f"\033[95m\033[1mfunction({function_name}): \033[95m\033[0m{function_message}")
                        self.context.append_message("function", function_message, function_name)
                        function_message = None
                else:
                    print(colored(f"No function {function_name} in the module", "red"))
        return (function_message, function_name)


        
if __name__ == '__main__':
    config = ChatConfig("./manifests/manifests")
    print(config.ONELINE_HELP)
    main = Main(config, 'dispatcher')
    main.start()
