import os
from dotenv import load_dotenv
import requests
import json

load_dotenv() # Load default environment variables (.env)
JUPYTER_TOKEN = os.getenv("JUPYTER_TOKEN", "")
print(f"jupyter token: {JUPYTER_TOKEN}")
token_response = requests.get("http://localhost:8888/")
xsrf_token = token_response.cookies.get("_xsrf")
headers = {
    "Authorization": f"Token {JUPYTER_TOKEN}",
    "Content-Type": "application/json",
    "X-XSRFToken": xsrf_token
}
cookies = {"_xsrf": xsrf_token}
api_endpoint = "http://localhost:8888/api/contents"

def create_notebook(name):
    # Create a new notebook
    new_notebook = {
        "type": "notebook",
        "content": {}
    }

    response = requests.post(api_endpoint, headers=headers, cookies=cookies, json=new_notebook)

    if response.ok:
        notebook_data = json.loads(response.content)
        return notebook_data    
    else:
        print(f"Error creating notebook. Status code: {response.status_code}")
        return "Failed"

def create_code_cell(path, code):
    url = f"{api_endpoint}/{path}"
    response = requests.get(url, headers=headers, cookies=cookies)
    notebook_data = json.loads(response.content)

    cell = {
        "cell_type": "code",
        "metadata": {},
        "execution_count": None,
        "source": code,
        "outputs": []
    }
    if notebook_data["content"].get("cells") == None:
        notebook_data["content"]["cells"] = []
    notebook_data["content"]["cells"].append(cell)

    response = requests.put(url, headers=headers, cookies=cookies, json=notebook_data)
    print(response)
    if response.ok:
        notebook_data = json.loads(response.content)
        return notebook_data    
    else:
        print(f"Error creating code cell. Status code: {response.status_code}")
        return "Failed"
