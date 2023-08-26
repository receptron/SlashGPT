import json
import urllib.parse

import requests
from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport
from termcolor import colored

from lib.utils.utils import COLOR_DEBUG, COLOR_ERROR


def graphQLRequest(url, arguments):
    transport = RequestsHTTPTransport(url=url, use_json=True)
    client = Client(transport=transport)
    query = arguments.get("query")
    graphQuery = gql(f"query {query}")
    try:
        response = client.execute(graphQuery)
        return json.dumps(response)
    except Exception as e:
        return str(e)


def http_request(url, method, headers, appkey_value, arguments, verbose):
    appkey = {"appkey": appkey_value}
    headers = {key: value.format(**arguments, **appkey) for key, value in headers.items()}
    if method == "POST":
        headers["Content-Type"] = "application/json"
        if verbose:
            print(colored(f"Posting to {url} {headers}", COLOR_DEBUG))
        response = requests.post(url, headers=headers, json=arguments)
    else:
        if verbose:
            print(colored(arguments.items(), COLOR_DEBUG))
        url = url.format(
            **{key: urllib.parse.quote(value) for key, value in arguments.items()},
            **appkey,
        )
        if verbose:
            print(colored(f"Fetching from {url}", COLOR_DEBUG))
        response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.text
    else:
        print(colored(f"Got {response.status_code}:{response.text} from {url}", COLOR_ERROR))
