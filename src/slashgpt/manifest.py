import json
import random
import re
from datetime import datetime
from typing import List

from slashgpt.utils.print import print_info


class Manifest:
    def __init__(self, manifest: dict = {}, base_dir: str = "", agent_name=None):
        self.base_dir = base_dir
        self.__manifest = manifest
        self.__agent_name = agent_name
        self.module = self.__read_module()

    def get(self, key: str):
        return self.__manifest.get(key)

    def username(self):
        return self.get("you") or f"You({self.__agent_name})"

    def botname(self):
        return self.get("bot") or "GPT"

    def actions(self):
        return self.get("actions") or {}

    def title(self):
        return self.get("title") or ""

    def temperature(self):
        if "temperature" in self.__manifest:
            return float(self.get("temperature"))
        return 0.7

    def model(self):
        return self.get("model") or "gpt-3.5-turbo-0613"

    def history_type(self):
        return self.get("history_type") or "all"

    def functions(self):
        value = self.__functions()
        agents = self.get("agents")

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
        return self.module and self.module.get(function_name) or None

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

    def prompt_data(self, manifests: dict = {}):
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
            return prompt

    def __apply_agent(self, prompt: str, agents: List[str], manifests: dict = {}):
        descriptions = [f"{agent}: {manifests[agent].get('description')}" for agent in agents]
        return re.sub("\\{agents\\}", "\n".join(descriptions), prompt, 1)

    def format_question(self, question: str):
        if question[:1] == "`":
            print_info("skipping form")
            return question[1:]
        else:
            form = self.get("form")
            if form:
                return form.format(question=question)
        return question

    def skip_function_result(self):
        return self.get("skip_function_result")

    def samples(self):
        return list(filter(lambda x: x.strip()[:6] == "sample", self.__manifest.keys()))

    # return self.__manifest.keys()
