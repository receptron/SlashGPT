import os
import urllib.parse
from urllib.parse import urlparse

from termcolor import colored

from lib.function.network import graphQLRequest, http_request
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

    def has_emit(self):
        return self.__get("type") == "emit"

    def emit_method(self):
        return self.__get("emit_method")

    def emit_data(self, arguments):
        data = self.__get("emit_data")
        return {x: data.get(x).format(**arguments) for x in data}

    def call_api(self, arguments, verbose):
        type = self.__call_type()
        if type == CALL_TYPE.REST:
            appkey_value = self.__get_appkey_value() or ""

            return http_request(
                self.__get("url"),
                self.__get("method"),
                self.__function_action_data.get("headers", {}),
                appkey_value,
                arguments,
                verbose,
            )
        if type == CALL_TYPE.GRAPHQL:
            return graphQLRequest(self.__get("url"), arguments)

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

    def __call_type(self):
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

    def read_dataURL_template(
        self, template, mime_type, message_template, arguments, verbose
    ):
        _mime_type = mime_type or ""
        with open(f"{template}", "r") as f:
            template = f.read()
            if verbose:
                print(colored(template, "cyan"))
            data = template.format(**arguments)
            dataURL = f"data:{_mime_type};charset=utf-8,{urllib.parse.quote_plus(data)}"
            return message_template.format(url=dataURL)

    def __get_appkey_value(self):
        appkey = self.__get("appkey")
        url = self.__get("url")

        if appkey:
            appkey_value = os.getenv("SLASH_GPT_ENV_" + appkey, "")

            # check domain
            param = appkey_value.split(",")
            if len(param) == 2:
                parsed_url = urlparse(url)
                if param[0] != parsed_url.netloc:
                    print(
                        colored(f"Invalid appkey domain {appkey} in .env file.", "red")
                    )
                    return
                appkey_value = param[1]

            if not appkey_value:
                print(colored(f"Missing {appkey} in .env file.", "red"))
            return appkey_value
