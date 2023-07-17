import os
from dotenv import load_dotenv
import requests
import json

load_dotenv() # Load default environment variables (.env)
JUPYTER_TOKEN = os.getenv("OPENAI_API_KEY", "")

def create_notebook(name):
    response = requests.get("http://localhost:8888/")
    xsrf_token = response.cookies.get("_xsrf")
    print(xsrf_token)

    api_endpoint = "http://localhost:8888/api/contents"
    headers = {
        "Authorization": JUPYTER_TOKEN,
        "Content-Type": "application/json",
        "X-XSRFToken": xsrf_token
    }
    cookies = {"_xsrf": xsrf_token}

    # Create a new notebook
    new_notebook = {
        "type": "notebook",
        "name": name,
        "content": {
            "cells": [
                {
                    "cell_type": "code",
                    "metadata": {},
                    "execution_count": None,
                    "source": "a=1",
                    "outputs": []
                }
            ],
            "metadata": {
                "kernelspec": {
                    "name": "python3",
                    "display_name": "Python 3",
                    "language": "python"
                },
                "language_info": {
                    "name": "python"
                }
            }
        }
    }

    response = requests.post(api_endpoint, headers=headers, cookies=cookies, json=new_notebook)

    if response.status_code == 201:
        notebook_data = json.loads(response.content)
        notebook_path = notebook_data["content"]["path"]

        # Execute the notebook
        execute_endpoint = f"http://localhost:8888/api/notebooks/{notebook_path}/execute"
        response = requests.post(execute_endpoint, headers=headers)

        if response.status_code == 202:
            print("Notebook created and executed successfully.")
        else:
            print(f"Error executing notebook. Status code: {response.status_code}")

    else:
        print(f"Error creating notebook. Status code: {response.status_code}")
