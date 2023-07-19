import os
import requests
import json
import IPython

folder_path = "./output/notebooks"
if not os.path.isdir(folder_path):
    os.makedirs(folder_path)

ipython = None
notebook = {}
file_path = ""

def create_notebook():
    # Create a new notebook
    counter = 0
    notebook_name = "notebook"
    global file_path
    file_path = os.path.join(folder_path, f"{notebook_name}.ipynb")

    while os.path.exists(file_path):
        counter += 1
        notebook_name = f"notebook{counter}"
        file_path = os.path.join(folder_path, f"{notebook_name}.ipynb")

    global notebook
    notebook = {
        "cells": [],
        "metadata": {},
        "nbformat": 4,
        "nbformat_minor": 5
    }
    # Create the file
    with open(file_path, 'w') as file:
        json.dump(notebook, file)

    global ipython
    ipython = IPython.InteractiveShell()
    return ({'result':'created a notebook', 'notebook_name':notebook_name}, None)

def run_python_code(code, query:str):
    global notebook
    if query:
        cell = {
            "cell_type": "markdown",
            "metadata": {},
            "source": [f"**User**: {query}"]
        }
        notebook["cells"].append(cell)

    cell = {
        "cell_type": "code",
        "metadata": {},
        "execution_count": None,
        "source": code,
        "outputs": []
    }
    notebook["cells"].append(cell)

    global file_path
    with open(file_path, 'w') as file:
        json.dump(notebook, file)

    if isinstance(code, list):
        code = "\n".join(code)
    ipython.run_cell(code)
    ret = ipython.user_ns['_']
    # print(ret)
    return (str(ret), f"```Python\n{code}\n```")

# GPT sometimes call this function
def python(code):
    run_python_code(code, None)
