import os
from termcolor import colored
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
import json
import requests
import urllib.parse

class FunctionAction:
    @classmethod
    def factory(cls, function_action_data):
        if function_action_data == None:
            return None
        return FunctionAction(function_action_data)


    def __init__(self, function_action_data):
        self.__function_action_data = function_action_data

    def __get(self, key):
        return self.__function_action_data.get(key)        

    def is_switch_context(self):
        return "metafile" in self.__function_action_data

    def get_manifest_key(self, arguments):
        metafile = self.__get("metafile")
        return metafile.format(**arguments)

    def call_api(self, arguments, verbose):
        appkey = self.__get("appkey")

        if appkey:
            appkey_value = os.getenv(appkey, "")
            if appkey_value:
                arguments["appkey"] = appkey_value
            else:
                print(colored(f"Missing {appkey} in .env file.", "red"))

        url = self.__get("url")
        if url:
            if self.__get("graphQL"):
                return self.graphQLRequest(url, arguments)
            else:
                return self.http_request(url, self.__get("method"), self.__function_action_data.get("headers",{}), arguments, verbose)
        template = self.__get("template")
        message_template = self.__get("message")
        if template:
            return self.read_dataURL_template(template, self.__get("mime_type"), message_template, arguments, verbose)

        if message_template:
            return message_template.format(**arguments)
        return "Success"
        

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

    def http_request(self, url, method, headers, arguments, verbose):
        headers = {key:value.format(**arguments) for key,value in headers.items()}
        if method == "POST":
            headers['Content-Type'] = 'application/json';
            if verbose:
                print(colored(f"Posting to {url} {headers}", "yellow"))
            response = requests.post(url, headers=headers, json=arguments)
        else:
            print(arguments.items())
            url = url.format(**{key:urllib.parse.quote(value) for key, value in arguments.items()})
            if verbose:
                print(colored(f"Fetching from {url}", "yellow"))
            response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.text
        else:
            print(colored(f"Got {response.status_code}:{response.text} from {url}", "red"))

    def read_dataURL_template(self, template, mime_type, message_template, arguments, verbose):
        _mime_type = mime_type or ""
        message_template = message_template or self.__get("url")
        with open(f"{template}", 'r') as f:
            template = f.read()
            if verbose:
                print(template)
            data = template.format(**arguments)
            dataURL = f"data:{_mime_type};charset=utf-8,{urllib.parse.quote_plus(data)}"
            return message_template.format(url = dataURL)
