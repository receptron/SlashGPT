import os
import json
import IPython
import io
import contextlib
import matplotlib.pyplot as plt
from termcolor import colored

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

    '''
    # Handle matplotlib figures
    for fig_num in plt.get_fignums():
        fig = plt.figure(fig_num)
        buf = io.BytesIO()
        fig.savefig(buf, format='png')
        buf.seek(0)
        img_str = base64.b64encode(buf.read()).decode('utf-8')
        cell["outputs"].append({
            "output_type": "display_data",
            "data": {
                "image/png": img_str
            },
            "metadata": {}
        })
    '''

    notebook["cells"].append(cell)
    global file_path
    with open(file_path, 'w') as file:
        json.dump(notebook, file)

    if exec_result.result is None:
        exec_result.result = stdout.getvalue()
        if exec_result.result is None:
            exec_result.result = stderr.getvalue()
            if exec_result.result is None:
                exec_result.result = "Done"

    return (str(exec_result.result), f"```Python\n{code}\n```")

# GPT sometimes call this function
def python(code):
    if isinstance(code,str):
        code = [code]
    run_python_code(code, None)
