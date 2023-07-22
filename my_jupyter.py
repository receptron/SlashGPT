import os
import json
import IPython
import io
import contextlib
import matplotlib.pyplot as plt
from termcolor import colored
from dotenv import load_dotenv
import codeboxapi as cb

folder_path = "./output/notebooks"
if not os.path.isdir(folder_path):
    os.makedirs(folder_path)

load_dotenv() # Load default environment variables (.env)
CODEBOX_API_KEY = os.getenv("CODEBOX_API_KEY")
'''
if CODEBOX_API_KEY and CODEBOX_API_KEY != "local":
    cb.set_api_key(CODEBOX_API_KEY)
'''

ipython = None
notebook = {}
file_path = ""
codebox = None

def create_notebook(module:str):
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
        "cells": [{
            "cell_type": "markdown",
            "metadata": {},
            "source": [f"# {module}"]
        }],
        "metadata": {},
        "nbformat": 4,
        "nbformat_minor": 5
    }
    # Create the file
    with open(file_path, 'w') as file:
        json.dump(notebook, file)

    global ipython, codebox
    if CODEBOX_API_KEY:
        if codebox:
            codebox.astop()
        codebox = cb.CodeBox()
        codebox.start()
    else:
        ipython = IPython.InteractiveShell()
    return ({'result':'created a notebook', 'notebook_name':notebook_name}, None)

def stop():
    global codebox
    if codebox:
        codebox.stop()
        codebox = None

def run_python_code(code, query:str):
    global notebook
    if query:
        cell = {
            "cell_type": "markdown",
            "metadata": {},
            "source": [f"**User**: {query}"]
        }
        notebook["cells"].append(cell)

    for i in range(len(code)):
        if not code[i].endswith('\n'):
            code[i] += '\n'
    cell = {
        "cell_type": "code",
        "metadata": {},
        "execution_count": None,
        "source": code,
        "outputs": []
    }

    if codebox:
        output: cb.CodeBoxOutput = codebox.run(''.join(code))
        if output.type == "text":
            cell["outputs"].append({
                "output_type": "execute_result",
                "execution_count": None,
                "data": {
                    "text/plain": str(output)
                },
                "metadata": {}
            })
            result = str(output)
        elif output.type == "error":
            cell["outputs"].append({
                "output_type": "stream",
                "name": "stderr",
                "text": str(output)
            })
            result = str(output)
        elif output.type == "image/png":
            # to be implemented
            result = "Image was successfully generated."
        else:
            result = f"Something went wrong ({output.type})"
    else:
        stdout = io.StringIO()
        stderr = io.StringIO()

        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            exec_result = ipython.run_cell("\n".join(code) if isinstance(code, list) else code)

        # Handle stdout
        if stdout.getvalue():
            cell["outputs"].append({
                "output_type": "stream",
                "name": "stdout",
                "text": stdout.getvalue()
            })

        # Handle stderr
        if stderr.getvalue():
            cell["outputs"].append({
                "output_type": "stream",
                "name": "stderr",
                "text": stderr.getvalue()
            })
            print(colored(stderr.getvalue(), "red"))

        # Handle execution result
        if exec_result.result is not None:
            cell["outputs"].append({
                "output_type": "execute_result",
                "execution_count": None,
                "data": {
                    "text/plain": str(exec_result.result)
                },
                "metadata": {}
            })
        result = exec_result.result
        if result is None:
            result = stdout.getvalue()
            if result is None:
                result = stderr.getvalue()
                if result is None:
                    result = "Done"

    notebook["cells"].append(cell)
    global file_path
    with open(file_path, 'w') as file:
        json.dump(notebook, file)

    return (str(result), f"```Python\n{code}\n```")

# GPT sometimes call this function
def python(code):
    if isinstance(code,str):
        code = [code]
    run_python_code(code, None)
