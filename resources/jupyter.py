import os
from dotenv import load_dotenv
import requests
import json

load_dotenv() # Load default environment variables (.env)
JUPYTER_TOKEN = os.getenv("JUPYTER_TOKEN", "")
print(f"jupyter token: {JUPYTER_TOKEN}")

def create_notebook(name):
    response = requests.get("http://localhost:8888/")
    xsrf_token = response.cookies.get("_xsrf")

    api_endpoint = "http://localhost:8888/api/contents"
    headers = {
        "Authorization": f"Token {JUPYTER_TOKEN}",
        "Content-Type": "application/json",
        "X-XSRFToken": xsrf_token
    }
    cookies = {"_xsrf": xsrf_token}
    print(headers)

    # Create a new notebook
    new_notebook = {
        "type": "notebook",
        "name": 'my_new_notebook.ipynb',
        "content": {}
    }

    response = requests.post(api_endpoint, headers=headers, cookies=cookies, json=new_notebook)

    if response.status_code == 201:
        notebook_data = json.loads(response.content)
        return notebook_data    
    else:
        print(f"Error creating notebook. Status code: {response.status_code}")
