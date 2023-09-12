import json
import urllib.parse

import requests
from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport

from slashgpt.utils.print import print_debug, print_error


def graphQLRequest(url: str, headers: dict, appkey_value: str, arguments: dict, verbose: bool):
    try:
        appkey = {"appkey": appkey_value}
        headers = {key: value.format(**arguments, **appkey) for key, value in headers.items()}
        if verbose:
            print_debug(f"Posting to {url} {headers}")
        transport = RequestsHTTPTransport(url=url, headers=headers, use_json=True)
        client = Client(transport=transport)
        query = arguments.get("query")
        graphQuery = gql(f"query {query}")
        response = client.execute(graphQuery)
        return json.dumps(response)
    except Exception as e:
        return str(e)


def http_request(url: str, method: str, headers: dict, appkey_value: str, arguments: dict, verbose: bool):
    appkey = {"appkey": appkey_value}
    headers = {key: value.format(**arguments, **appkey) for key, value in headers.items()}
    if method == "POST":
        headers["Content-Type"] = "application/json"
        if verbose:
            print_debug(f"Posting to {url} {headers}")
        response = requests.post(url, headers=headers, json=arguments)
    else:
        if verbose:
            print_debug(str(arguments.items()))
        url = url.format(
            **{key: urllib.parse.quote(value) for key, value in arguments.items()},
            **appkey,
        )
        if verbose:
            print_debug(f"Fetching from {url}")
        response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.text
    else:
        print_error(f"Got {response.status_code}:{response.text} from {url}")
