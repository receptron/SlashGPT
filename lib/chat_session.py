from datetime import datetime
import re
import json
import openai
import random
import google.generativeai as palm
import google.generativeai.types as safety_types
from termcolor import colored
import replicate

from lib.chat_config import ChatConfig
from lib.common import llms

from lib.log import create_log_dir, save_log
from lib.manifest import Manifest
from lib.function_call import FunctionCall
from lib.function_action import FunctionAction
from lib.dbs.pinecone import DBPinecone

"""
ChatSession represents a chat session with a particular AI agent.
The key is the identifier of the agent.
The manifest specifies behaviors of the agent.
"""
class ChatSession:
    def __init__(self, config: ChatConfig, manifest_key: str = "GPT"):
        self.config = config
        self.manifest_key = manifest_key

        self.set_manifest()

        self.time = datetime.now()
        self.userName = self.manifest.username()
        self.botName = self.manifest.botname()
        self.title = self.manifest.title()
        self.intro = self.manifest.get("intro")
        self.actions = self.manifest.actions()
        self.temperature = self.manifest.temperature()
        
        self.messages = []
        # init log dir
        create_log_dir(manifest_key)

        # Load the model name and make it sure that we have required keys
        (self.model, self.max_token) = get_model_and_max_token(config, self.manifest)

        agents = self.manifest.get("agents")

        # Load the prompt, fill variables and append it as the system message
        self.prompt = self.manifest.prompt_data()
        if self.prompt:
            if agents:
                self.prompt = apply_agent(self.prompt, agents, self.config)
            self.messages = [{"role":"system", "content":self.prompt}]

        # Prepare embedded database index
        self.vector_db = None
        embeddings = self.manifest.get("embeddings")
        if embeddings:
            table_name = embeddings.get("name")
            try:
                self.vector_db = DBPinecone.factory(table_name, self.config)
            except Exception as e:
                print(colored(f"Pinecone Error: {e}", "yellow"))

        # Load agent specific python modules (for external function calls) if necessary
        self.module = self.manifest.read_module()
        
        # Load functions file if it is specified
        self.functions = self.manifest.functions()
        if self.functions and self.config.verbose:
            print(self.functions)

    def set_manifest(self):
        manifest_data = self.config.get_manifest_data(self.manifest_key)
        self.manifest = Manifest(manifest_data if manifest_data else {}, self.manifest_key)

    def set_model(self, model, max_token = 4096):
        self.model = model
        self.max_token = max_token
        print(f"Model = {self.model}")

    def get_manifest_attr(self, key):
        return self.manifest.get(key)


    def get_module(self, function_name):
        return self.module and self.module.get(function_name) or None

    def get_action(self, function_name):
        action = self.actions.get(function_name)
        return FunctionAction.factory(action)

    def skip_function_result(self):
        return self.get_manifest_attr("skip_function_result")
    

    """
    Append a message to the chat session, specifying the role ("user", "system" or "function").
    In case of a function message, the name specifies the function name.
    """
    def append_message(self, role: str, message: str, name = None):
        if name:
            self.messages.append({"role":role, "content":message, "name":name })
        else:
            self.messages.append({"role":role, "content":message })
        if self.vector_db and role == "user":
            articles = self.vector_db.fetch_related_articles(self.max_token - 500)
            assert self.messages[0]["role"] == "system", "Missing system message"
            self.messages[0] = {
                "role":"system", 
                "content":re.sub("\\{articles\\}", articles, self.prompt, 1)
            }

    def save_log(self):
        save_log(self.manifest_key, self.messages, self.time)

    def set_intro(self):
        if self.intro:
            intro = self.intro[random.randrange(0, len(self.intro))]
            self.append_message("assistant", intro)
            print(f"\033[92m\033[1m{self.botName}\033[95m\033[0m: {intro}")

    """
    Extract the Python code from the string if the agent is a code interpreter.
    Returns it in the "function call" format. 
    """
    def _extract_function_call(self, res:str):
        if self.manifest.get("notebook"):
            lines = res.splitlines()
            codes = None
            for line in lines:
                if line[:3] == "```":
                    if codes is None:
                        codes = []
                    else:
                        break
                elif codes is not None:
                    codes.append(line)
            if codes:
                return (FunctionCall({
                    "name": "run_python_code",
                    "arguments": {
                        "code": codes,
                        "query": self.messages[-1]["content"]
                    }
                }), None) 
            
            print(colored("Debug Message: no code in this reply", "yellow"))
        return (None, res)

    """
    Let the LLM generate a responce based on the messasges in this session.
    Return values:
        role: "assistent"
        res: message
        function_call: json representing the function call (optional)
    """
    def generate_response(self):
        role = None
        res = None
        function_call = None
        role = "assistant"

        if self.model == "palm":
            defaults = {
                'model': 'models/chat-bison-001',
                'temperature': self.temperature,
                'candidate_count': 1,
                'top_k': 40,
                'top_p': 0.95,
            }
            system = ""
            examples = []
            messages = []
            for message in self.messages:
                role = message["role"]
                content = message["content"]
                if content:
                    if role == "system":
                        system = message["content"]
                    elif len(messages)>0 or role != "assistant":
                        messages.append(message["content"])

            response = palm.chat(
                **defaults,
                context=system,
                examples=examples,
                messages=messages
            )
            res = response.last
            if res:
                if self.config.verbose:
                    print(colored(res, "magenta"))
                (function_call, res) = self._extract_function_call(res)
            else:
                # Error: Typically some restrictions
                print(colored(response.filters, "red"))

        elif self.model[:6] == "llama2" or self.model == "vicuna":
            prompts = []
            for message in self.messages:
                role = message["role"]
                content = message["content"]
                if content:
                    prompts.append(f"{role}:{message['content']}")
            if self.functions:
                last = prompts.pop()
                prompts.append(f"system: Here is the definition of functions available to you to call.\n{self.functions}\nYou need to generate a json file with 'name' for function name and 'arguments' for argument.")
                prompts.append(last)
            prompts.append("assistant:")

            replicate_model = "a16z-infra/llama7b-v2-chat:a845a72bb3fa3ae298143d13efa8873a2987dbf3d49c293513cd8abf4b845a83"
            if llms.get(self.model):
                llm = llms.get(self.model)
                if llm.get("replicate_model"):
                    replicate_model = llm.get("replicate_model")
                
            output = replicate.run(
                replicate_model,
                input={"prompt": '\n'.join(prompts)},
                temperature = self.temperature
            )
            (function_call, res) = self._extract_function_call(''.join(output))

        else:
            if self.functions:
                response = openai.ChatCompletion.create(
                    model=self.model,
                    messages=self.messages,
                    functions=self.functions,
                    temperature=self.temperature)
            else:
                response = openai.ChatCompletion.create(
                    model=self.model,
                    messages=self.messages,
                    temperature=self.temperature)
            if self.config.verbose:
                print(colored(f"model={response['model']}", "yellow"))
                print(colored(f"usage={response['usage']}", "yellow"))
            answer = response['choices'][0]['message']
            res = answer['content']
            role = answer['role']
            function_call = FunctionCall.factory(answer.get('function_call'))
        return (role, res, function_call)


"""
Get module name from manifest and set max_token.
"""
def get_model_and_max_token(config: ChatConfig, manifest = {}): 
    max_token = 4096
    model = manifest.model()
    if model == "gpt-3.5-turbo-16k-0613":
        return (model, max_token * 4)
    elif model == "palm":
        if config.GOOGLE_PALM_KEY is not None:
            return (model, max_token)
        print(colored("Please set GOOGLE_PALM_KEY in .env file","red"))
    elif model[:6] == "llama2":
        if config.REPLICATE_API_TOKEN is not None:
            return (model, max_token)
        print(colored("Please set REPLICATE_API_TOKEN in .env file","red"))
    return ("gpt-3.5-turbo-0613", max_token)

def apply_agent(prompt, agents, config):    
    descriptions = [f"{agent}: {config.manifests[agent].get('description')}" for agent in agents]
    return re.sub("\\{agents\\}", "\n".join(descriptions), prompt, 1)

