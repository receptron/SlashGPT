import json
import os
import urllib.parse

import requests
from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport
from termcolor import colored

from lib.utils.utils import CALL_TYPE


class FunctionAction:
    @classmethod
    def factory(cls, function_action_data):
        if function_action_data is None:
            return None
        return FunctionAction(function_action_data)

    def __init__(self, function_action_data):
        self.__function_action_data = function_action_data

    def __get(self, key):
        return self.__function_action_data.get(key)

    def is_switch_context(self):
        return "manifest" in self.__function_action_data

    def get_manifest_key(self, arguments):
        manifest = self.__get("manifest")
        return manifest.format(**arguments)

    def get_appkey_value(self):
        appkey = self.__get("appkey")

        # TODO: check domain
        if appkey:
            appkey_value = os.getenv("SLASH_GPT_ENV_" + appkey, "")
            if not appkey_value:
                print(colored(f"Missing {appkey} in .env file.", "red"))
            return appkey_value

    def call_api(self, arguments, verbose):

        type = self.call_type()
        if type == CALL_TYPE.REST:
            appkey_value = self.get_appkey_value() or ""

            return self.http_request(
                self.__get("url"),
                self.__get("method"),
                self.__function_action_data.get("headers", {}),
                appkey_value,
                arguments,
                verbose,
            )
        if type == CALL_TYPE.GRAPHQL:
            return self.graphQLRequest(self.__get("url"), arguments)

        if type == CALL_TYPE.DATA_URL:
            return self.read_dataURL_template(
                self.__get("template"),
                self.__get("mime_type"),
                self.__get("message"),
                arguments,
                verbose,
            )

        if type == CALL_TYPE.MESSAGE_TEMPLATE:
            return self.__get("message").format(**arguments)
        return "Success"

    def call_type(self):
        type = self.__get("type")
        if type:
            if type == "rest":
                return CALL_TYPE.REST
            if type == "graphQL":
                return CALL_TYPE.GRAPHQL
            if type == "data_url":
                return CALL_TYPE.DATA_URL
            if type == "message_template":
                return CALL_TYPE.MESSAGE_TEMPLATE

        # for backward compatibility.
        # TODO: remove later
        if "url" in self.__function_action_data:
            if "graphQL" in self.__function_action_data:
                return CALL_TYPE.GRAPHQL
            return CALL_TYPE.REST
        if "template" in self.__function_action_data:
            return CALL_TYPE.DATA_URL
        if "message" in self.__function_action_data:
            return CALL_TYPE.MESSAGE_TEMPLATE

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

    def http_request(self, url, method, headers, appkey_value, arguments, verbose):
        headers = {key: value.format(**arguments).format("appkey", appkey_value) for key, value in headers.items()}
        if method == "POST":
            headers["Content-Type"] = "application/json"
            if verbose:
                print(colored(f"Posting to {url} {headers}", "cyan"))
            response = requests.post(url, headers=headers, json=arguments)
        else:
            if verbose:
                print(colored(arguments.items(), "cyan"))
            url = url.format(
                **{key: urllib.parse.quote(value) for key, value in arguments.items()}
            )
            if verbose:
                print(colored(f"Fetching from {url}", "cyan"))
            response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.text
        else:
            print(
                colored(f"Got {response.status_code}:{response.text} from {url}", "red")
            )

    def read_dataURL_template(
        self, template, mime_type, message_template, arguments, verbose
    ):
        _mime_type = mime_type or ""
        message_template = message_template or self.__get("url")
        with open(f"{template}", "r") as f:
            template = f.read()
            if verbose:
                print(colored(template, "cyan"))
            data = template.format(**arguments)
            dataURL = f"data:{_mime_type};charset=utf-8,{urllib.parse.quote_plus(data)}"
            return message_template.format(url=dataURL)
