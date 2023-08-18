#!/usr/bin/env python3
import os
import platform
if platform.system() == "Darwin":
    import readline # So that input can handle Kanji & delete
import json
import re
import random
from termcolor import colored
import requests
from gtts import gTTS
from playsound import playsound
import urllib.parse
from jupyter_runtime import PythonRuntime
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

from lib.chat_session import ChatSession
from lib.chat_config import ChatConfig
# Configuration

"""
utility functions for Main class
"""

def play_text(text, lang):
    audio_obj = gTTS(text=text, lang=lang, slow=False)
    audio_obj.save("./output/audio.mp3")
    playsound("./output/audio.mp3")

def save_log(manifest_key, messages, time):
    timeStr = time.strftime("%Y-%m-%d %H-%M-%S.%f")
    with open(f'output/{manifest_key}/{timeStr}.json', 'w') as f:   
        json.dump(messages, f)


manifests = {
    "root": {
        "manifests_dir": "manifests",
        "default_manifest_key": "dispatcher",
    },
    "rpg1": {
        "manifests_dir": "rpg1",
        "default_manifest_key": "bartender",
    },
    "zoo": {
        "manifests_dir": "zoo",
        "default_manifest_key": "monkey",
    },
    "roles1": {
        "manifests_dir": "prompts",
        "default_manifest_key": None,
    },
    "roles2": {
        "manifests_dir": "roles2",
        "default_manifest_key": None,
    },
};


"""
Main is a singleton, which process the input from the user and manage chat sessions.
"""
class Main:
    def __init__(self, config: ChatConfig):
        self.config = config

        # Prepare output folders
        if not os.path.isdir("output"):
            os.makedirs("output")
        if not os.path.isdir("output/GPT"):
            os.makedirs("output/GPT")

        self.context = ChatSession(self.config)
        self.exit = False
        self.runtime = PythonRuntime("./output/notebooks")

    """
    switchContext terminate the current chat session and start a new.
    The key specifies the AI agent.
    """
    def switchContext(self, manifest_key: str, intro: bool = True):
        if manifest_key is None:
            self.context = ChatSession(self.config)
            return
        manifest = self.config.manifests.get(manifest_key)
        if manifest:
            self.context = ChatSession(self.config, manifest_key=manifest_key, manifest=manifest)
            if not os.path.isdir(f"output/{self.context.manifest_key}"):
                os.makedirs(f"output/{self.context.manifest_key}")
            if self.config.verbose:
                print(colored(f"Activating: {self.context.title} (model={self.context.model}, temperature={self.context.temperature}, max_token={self.context.max_token})", "blue"))
            else:
                print(colored(f"Activating: {self.context.title}", "blue"))
            isNotebook = manifest.get("notebook")
            if isNotebook:
                (result, _) = self.runtime.create_notebook(self.context.model)
                print(colored(f"Created a notebook: {result.get('notebook_name')}", "blue"))

            if intro and self.context.intro:
                intro = self.context.intro[random.randrange(0, len(self.context.intro))]
                self.context.appendMessage("assistant", intro)
                print(f"\033[92m\033[1m{self.context.botName}\033[95m\033[0m: {intro}")
        else:            
            print(colored(f"Invalid slash command: {manifest_key}", "red"))


    def processMode(self, question: str):
        key = question[1:]
        commands = key.split(' ')
        if len(question) == 0:
            return "help"
        elif commands[0] == "sample" and len(commands) > 1:
            return "sample"
        elif key[:6] == "sample":
            return "sample"
        elif question[0] == "/":
            return "slash"
        else:
            return "talk"

    def processHelp(self):
        print(self.config.ONELINE_HELP)

    def processSample(self, question: str):
        key = question[1:]
        commands = key.split(' ')
        if commands[0] == "sample" and len(commands) > 1:
            sub_key = commands[1]
            sub_manifest = self.config.manifests.get(sub_key)
            if sub_manifest:
                sample = sub_manifest.get("sample")
                if sample:
                    print(sample)
                    return sample
        elif key[:6] == "sample":
            sample = self.context.manifest.get(key)
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
    def processSlash(self, question: str):
        if question[0] == "/": # TODO remove
            key = question[1:]
            commands = key.split(' ')
            if commands[0] == "help":
                if (len(commands) == 1):
                    print(self.config.LONG_HELP)
                    list = "\n".join(f"/{(key+'         ')[:12]} {self.config.manifests[key].get('title')}" for key in sorted(self.config.manifests.keys()))
                    print(f"Agents:\n{list}")
                if (len(commands) == 2):
                    manifest = self.config.manifests.get(commands[1])
                    if (manifest):
                       print(json.dumps(manifest, indent=2))
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
            elif key == "gpt3":
                self.context.set_model("gpt-3.5-turbo-0613")
            elif key == "gpt31":
                self.context.set_model("gpt-3.5-turbo-16k-0613", 4096 * 4)
            elif key == "gpt4":
                self.context.set_model("gpt-4-0613")
            elif key == "llama2" or key == "llama270" or key == "vicuna":
                if self.config.REPLICATE_API_TOKEN:
                    self.context.set_model(key)
                else:
                    print(colored("You need to set REPLICATE_API_TOKEN to use this model","red"))
            elif key == "palm":
                if self.config.GOOGLE_PALM_KEY:
                    self.context.set_model("palm")
                    if self.context.botName == "GPT":
                        self.context.botName = "PaLM"
                else:
                    print("Error: Missing GOOGLE_PALM_KEY")
            elif key == "new":
                self.switchContext(self.context.manifest_key, intro = False)
            elif commands[0] == "switch" and len(commands) > 1 and manifests.get(commands[1]):
                m = manifests[commands[1]]
                self.config.loadManifests("./" + m["manifests_dir"])
                self.switchContext(m["default_manifest_key"])
            else:
                self.switchContext(key)


    def processLlm(self, role, question, function_name, form = ""):
        skip_input = False
        if form:
            question = form.format(question = question)
        try:
            self.context.appendMessage(role, question, function_name)
            # Ask LLM to generate a response.
            (responseRole, res, function_call) = self.context.generateResponse()

            if responseRole and res:
                print(f"\033[92m\033[1m{self.context.botName}\033[95m\033[0m: {res}")

                if self.config.audio:
                    play_text(res, self.config.audio)

                self.context.appendMessage(responseRole, res)
                save_log(self.context.manifest_key, self.context.messages, self.context.time)

            if function_call:
                (question, function_name) = self.process_function_call(function_call)
                if question:
                    skip_input = True
        except Exception as e:
            print(colored(f"Exception: Restarting the chat :{e}","red"))
            self.switchContext(self.context.manifest_key)
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
                (question, function_name, skip_input) = self.processLlm(role, question, function_name)
            else:
                # Otherwise, retrieve the input from the user.
                question = input(f"\033[95m\033[1m{self.context.userName}: \033[95m\033[0m")
                function_name = None
                if question[:1] == "`":
                    print(colored("skipping form", "blue"))
                    question = question[1:]
                else:
                    form = self.context.manifest.get("form")

                mode = self.processMode(question)
                if mode == "help":
                    self.processHelp()
                elif mode == "slash":
                    self.processSlash(question)
                elif mode == "sample" or mode == "talk":
                    if mode == "sample":
                        question = self.processSample(question)
                    if question:
                        (question, function_name, skip_input) = self.processLlm("user", question, function_name, form)
                    
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
            action = self.context.actions.get(function_name)
            if action:
                url = action.get("url")
                template = action.get("template")
                message_template = action.get("message")
                metafile = action.get("metafile")
                appkey = action.get("appkey")
                if metafile:
                    metafile = metafile.format(**arguments)
                    self.switchContext(metafile, intro = False)
                    function_name = None # Withough name, this message will be treated as user prompt.

                if appkey:
                    appkey_value = os.getenv(appkey, "")
                    if appkey_value:
                        arguments["appkey"] = appkey_value
                    else:
                        print(colored(f"Missing {appkey} in .env file.", "red"))
                if url:
                    if action.get("graphQL"):
                        function_message = self.graphQLRequest(url, arguments)
                    else:
                        function_message = self.http_request(url, action.get("method"), action.get("headers",{}), arguments)
                elif template:
                    function_message = self.read_dataURL_template(template, action.get("mime_type"), message_template, arguments)
                elif message_template:
                    function_message = message_template.format(**arguments)
                else: 
                    function_message = "Success"
            else:
                if self.context.manifest.get("notebook"):
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
                        self.context.appendMessage("assistant", message)
                    if isinstance(result, dict):
                        result = json.dumps(result)
                    result_form = self.context.manifest.get("result_form")
                    if result_form:
                        function_message = result_form.format(result = result)
                    else:
                        function_message = result
                    if self.context.manifest.get("skip_function_result"):
                        print(f"\033[95m\033[1mfunction({function_name}): \033[95m\033[0m{function_message}")
                        self.context.appendMessage("function", function_message, function_name)
                        function_message = None
                else:
                    print(colored(f"No function {function_name} in the module", "red"))
        return (function_message, function_name)


    def graphQLRequest(self, url, arguments):
        transport = RequestsHTTPTransport(url=url, use_json=True)
        client = Client(transport=transport)
        query = arguments.get("query")
        graphQuery = gql(f"query {query}")
        try:
            response = client.execute(graphQuery)
            return json.dumps(response)
        except Exception as e:
            return str(e)

    def http_request(self, url, method, headers, arguments):
        headers = {key:value.format(**arguments) for key,value in headers.items()}
        if method == "POST":
            headers['Content-Type'] = 'application/json';
            if self.config.verbose:
                print(colored(f"Posting to {url} {headers}", "yellow"))
            response = requests.post(url, headers=headers, json=arguments)
        else:
            url = url.format(**{key:urllib.parse.quote(value) for key, value in arguments.items()})
            if self.config.verbose:
                print(colored(f"Fetching from {url}", "yellow"))
            response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.text
        else:
            print(colored(f"Got {response.status_code}:{response.text} from {url}", "red"))

    def read_dataURL_template(self, template, mime_type, message_template, arguments):
        _mime_type = mime_type or ""
        message_template = message_template or f"{url}"
        with open(f"{template}", 'r') as f:
            template = f.read()
            if self.config.verbose:
                print(template)
            data = template.format(**arguments)
            dataURL = f"data:{_mime_type};charset=utf-8,{urllib.parse.quote_plus(data)}"
            return message_template.format(url = dataURL)
        

                
config = ChatConfig("./manifests")
print(config.ONELINE_HELP)
main = Main(config)
main.switchContext('dispatcher')
main.start()
