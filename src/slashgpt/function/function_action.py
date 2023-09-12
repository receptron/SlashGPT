import os
import urllib.parse
from urllib.parse import urlparse

from slashgpt.function.network import graphQLRequest, http_request
from slashgpt.utils.print import print_debug, print_error
from slashgpt.utils.utils import CallType


class FunctionAction:
    @classmethod
    def factory(cls, function_action_data):
        if function_action_data is None:
            return None
        return FunctionAction(function_action_data)

    def __init__(self, function_action_data: dict):
        self.__function_action_data = function_action_data

    def __get(self, key: str):
        return self.__function_action_data.get(key)

    def has_emit(self):
        return self.__get("type") == "emit"

    def emit_method(self):
        return self.__get("emit_method")

    def emit_data(self, arguments: dict):
        data = self.__get("emit_data")
        return {x: data.get(x).format(**arguments) for x in data}

    def call_api(self, arguments: dict, base_dir: str, verbose: bool):
        type = self.__call_type()
        if type == CallType.REST:
            appkey_value = self.__get_appkey_value() or ""

            return http_request(
                self.__get("url"),
                self.__get("method"),
                self.__function_action_data.get("headers", {}),
                appkey_value,
                arguments,
                verbose,
            )
        if type == CallType.GRAPHQL:
            appkey_value = self.__get_appkey_value() or ""
            return graphQLRequest(
                url=self.__get("url"),
                headers=self.__function_action_data.get("headers", {}),
                appkey_value=appkey_value,
                arguments=arguments,
                verbose=verbose,
            )

        if type == CallType.DATA_URL:
            return self.read_dataURL_template(
                base_dir,
                self.__get("template"),
                self.__get("mime_type"),
                self.__get("message"),
                arguments,
                verbose,
            )

        if type == CallType.MESSAGE_TEMPLATE:
            return self.__get("message").format(**arguments)
        return "Success"

    def __call_type(self):
        type = self.__get("type")
        if type:
            if type == "rest":
                return CallType.REST
            if type == "graphQL":
                return CallType.GRAPHQL
            if type == "data_url":
                return CallType.DATA_URL
            if type == "message_template":
                return CallType.MESSAGE_TEMPLATE

        # for backward compatibility.
        # TODO: remove later
        if "url" in self.__function_action_data:
            if "graphQL" in self.__function_action_data:
                return CallType.GRAPHQL
            return CallType.REST
        if "template" in self.__function_action_data:
            return CallType.DATA_URL
        if "message" in self.__function_action_data:
            return CallType.MESSAGE_TEMPLATE

    def read_dataURL_template(self, base_dir: str, template_file_name: str, mime_type: str, message_template: str, arguments: dict, verbose: bool):
        _mime_type = mime_type or ""
        with open(f"{base_dir}/{template_file_name}", "r") as f:
            template = f.read()
            if verbose:
                print_debug(template)
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
                    print_error(f"Invalid appkey domain {appkey} in .env file.")
                    return
                appkey_value = param[1]

            if not appkey_value:
                print_error(f"Missing {appkey} in .env file.")
            return appkey_value
