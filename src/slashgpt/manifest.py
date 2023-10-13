import json
import random
import re
from datetime import datetime
from typing import List, Optional

from slashgpt.utils.print import print_info


class Manifest:
    """Manifest specifies the behavior of an LLM agent"""

    def __init__(self, manifest: dict = {}, base_dir: str = "", agent_name=None):
        """
        Args:
            manifest (dict): Manifest definition
            base_dir (str): The base folder location
            agent_name (str, optional): The display name of LLM agent
        """
        self.base_dir = base_dir
        """The base folder location"""
        self.__manifest = manifest
        self.__agent_name = agent_name
        self.__module = self.__read_module()

    def get(self, key: str):
        """Returns the specified property of the manifest definition (str, dict or list)"""
        return self.__manifest.get(key)

    def username(self):
        """Returns the user name to be displayed (str)"""
        return self.get("you") or f"You({self.__agent_name})"

    def botname(self):
        """Returns the bot (agent) name to be displayed (str)"""
        return self.get("bot") or f"Agent({self.__agent_name})"

    def actions(self):
        """Returns the action property of the manifest definition (dict)"""
        return self.get("actions") or {}

    def title(self):
        """Returns the title of the LLM agent (str)"""
        return self.get("title") or ""

    def temperature(self):
        """Returns the temperature of this LLM agent (float)"""
        if "temperature" in self.__manifest:
            return float(self.get("temperature"))
        return 0.7

    def stream(self):
        """Returns a boolean value indicating if the LLM should stream its output back to the user (bool)"""
        return self.get("stream") or False

    def logprobs(self):
        """Returns the number of tokens for whichthe LLM will display log probabilities, with a max of 5 (int)"""
        return self.get("logprobs") or None

    def num_completions(self):
        """Returns the number of desired LLM completions per prompt (int)"""
        return self.get("num_completions") or 1

    def model(self):
        """Returns the specified LLM model (str or dict)"""
        return self.get("model")

    # NOTE: Let's keep it hidden until we implement it.
    def __history_type(self):
        """Returns the history type, which controls the behavior of history"""
        return self.get("history_type") or "all"

    def manifest(self):
        """Returns the manifest definition (dict)"""
        return self.__manifest

    def functions(self):
        """Returns function definitions (list)"""
        value = self.__functions()
        agents = self.get("agents")

        # If agents are specified, inject their keys into the definition of categorize function.
        if value and agents:
            # WARNING: It assumes that categorize(category, ...) function
            for function in value:
                if function.get("name") == "categorize":
                    function["parameters"]["properties"]["category"]["enum"] = agents
        return value

    def __functions(self):
        value = self.get("functions")
        if value:
            if isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
                return value
            if isinstance(value, str):
                with open(self.base_dir + "/" + value, "r") as f:
                    return json.load(f)
        return None

    """
    Read Module
    Read Python file if module is in manifest.
    """

    def __read_module(self):
        module = self.get("module")
        if module:
            with open(f"{self.base_dir}/{module}", "r") as f:
                try:
                    code = f.read()
                    namespace = {}
                    exec(code, namespace)
                    print(f" {module}")
                    return namespace
                except ImportError:
                    print(f"Failed to import module: {module}")

        return None

    def get_module(self, function_name: str):
        """Returns the specified function of the dynamically loaded module (function)"""
        return self.__module and self.__module.get(function_name) or None

    def __read_prompt(self):
        prompt = self.get("prompt")
        if isinstance(prompt, list):
            prompt = "\n".join(prompt)
        if prompt:
            if re.search("\\{now\\}", prompt):
                time = datetime.now()
                prompt = re.sub("\\{now\\}", time.strftime("%Y%m%dT%H%M%SZ"), prompt, 1)
        return prompt

    """
    Read manifest data and shuffle data
    """

    def __get_random_manifest_data(self):
        list_data = self.get("list")
        if list_data:
            # Shuffle
            for i in range(len(list_data)):
                j = random.randrange(0, len(list_data))
                temp = list_data[i]
                list_data[i] = list_data[j]
                list_data[j] = temp
            return list_data

    def __replace_random(self, prompt, data):
        j = 0
        # TODO: fix array bounds bug
        while re.search("\\{random\\}", prompt):
            prompt = re.sub("\\{random\\}", data[j], prompt, 1)
            j += 1
        return prompt

    def __replace_from_resource_file(self, prompt, resource_file_name):
        with open(f"{self.base_dir}/{resource_file_name}", "r") as f:
            contents = f.read()
            return re.sub("\\{resource\\}", contents, prompt, 1)

    def prompt_data(self, manifests: dict = {}, memory: Optional[dict] = None):
        """Generate an appropriate prompt for a ChatSession (str)"""
        prompt = self.__read_prompt()
        agents = self.get("agents")
        if prompt:
            data = self.__get_random_manifest_data()
            if data:
                prompt = self.__replace_random(prompt, data)
            resource = self.get("resource")
            if resource:
                prompt = self.__replace_from_resource_file(prompt, resource)
            if agents:
                prompt = self.__apply_agent(prompt, agents, manifests)
            if memory is not None:
                prompt = re.sub("\\{memory\\}", json.dumps(memory), prompt, 1)
            return prompt

    def __apply_agent(self, prompt: str, agents: List[str], manifests: dict = {}):
        descriptions = [f"{agent}: {manifests[agent].get('description')}" for agent in agents]
        return re.sub("\\{agents\\}", "\n".join(descriptions), prompt, 1)

    def format_question(self, question: str):
        """Format the question if the "form" property is specified in the manifest (str)"""
        if question[:1] == "`":
            print_info("skipping form")
            return question[1:]
        else:
            form = self.get("form")
            if form:
                return form.format(question=question)
        return question

    def skip_function_result(self):
        """Returns the "skip_function_result" property in the manifest (bool)"""
        return self.get("skip_function_result")

    def samples(self):
        """Returns the sample questions specified in the manifest (list)"""
        return list(filter(lambda x: x.strip()[:6] == "sample", self.__manifest.keys()))
