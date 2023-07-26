import os
import json
import IPython
import io
import contextlib
import matplotlib.pyplot as plt
from termcolor import colored
from dotenv import load_dotenv
import codeboxapi as cb
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import base64

folder_path = "./output/notebooks"
if not os.path.isdir(folder_path):
    os.makedirs(folder_path)

load_dotenv() # Load default environment variables (.env)
CODEBOX_API_KEY = os.getenv("CODEBOX_API_KEY")
if CODEBOX_API_KEY and CODEBOX_API_KEY != "local":
    cb.set_api_key(CODEBOX_API_KEY)


class PythonRuntime:
    def __init__(self):
        self.ipython = None
        self.notebook = {}
        self.file_path = ""
        self.codebox = None

    def create_notebook(self, module:str):
        # Create a new notebook
        counter = 0
        notebook_name = "notebook"
        self.file_path = os.path.join(folder_path, f"{notebook_name}.ipynb")

        while os.path.exists(self.file_path):
            counter += 1
            notebook_name = f"notebook{counter}"
            self.file_path = os.path.join(folder_path, f"{notebook_name}.ipynb")

        self.notebook = {
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
        with open(self.file_path, 'w') as file:
            json.dump(self.notebook, file)

        if CODEBOX_API_KEY:
            if self.codebox:
                self.codebox.astop()
            self.codebox = cb.CodeBox()
            self.codebox.start()
        else:
            self.ipython = IPython.InteractiveShell()
        return ({'result':'created a notebook', 'notebook_name':notebook_name}, None)

    def stop(self):
        if self.codebox:
            self.codebox.stop()
            self.codebox = None

    def run_python_code(self, code:list, query:str):
        if query:
            cell = {
                "cell_type": "markdown",
                "metadata": {},
                "source": [f"**User**: {query}"]
            }
            self.notebook["cells"].append(cell)

        for i in range(len(code)):
            if not code[i].endswith('\n'):
                code[i] += '\n'
        cell = {
            "cell_type": "code",
            "metadata": {},
            "execution_count": 1,
            "source": ''.join(code),
            "outputs": []
        }

        if self.codebox:
            output: cb.CodeBoxOutput = self.codebox.run(''.join(code))
            print("***", output.type)
            if output.type == "text":
                cell["outputs"].append({
                    "output_type": "execute_result",
                    "data": {
                        "text/plain": str(output)
                    },
                    "execution_count": 1,
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
                cell["outputs"].append({
                    "data": {
                        "image/png": output.content
                    },
                    "output_type": "display_data",
                    "metadata": {}
                })
                result = "Image was successfully generated and presented."

                # Present it in a pop up window
                image_data = base64.b64decode(output.content)
                image_stream = io.BytesIO(image_data)
                image_array = mpimg.imread(image_stream, format='png')
                plt.imshow(image_array)
                plt.axis('off')
                plt.show(block=False)
            else:
                result = f"Something went wrong ({output.type})"
        else:
            stdout = io.StringIO()
            stderr = io.StringIO()

            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                exec_result = self.ipython.run_cell("".join(code) if isinstance(code, list) else code)

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
                    "execution_count": 1,
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

        self.notebook["cells"].append(cell)
        with open(self.file_path, 'w') as file:
            json.dump(self.notebook, file, indent=2)

        return (str(result), f"```Python\n{''.join(code)}\n```")

    # GPT sometimes call this function
    def python(self, code):
        if isinstance(code,str):
            code = [code]
        return self.run_python_code(code, None)

    def draw_diagram(self, code:str, query:str):
        codes = [
            "from graphviz import Source\n",
            "from IPython.display import Image, display\n",
            'diagram = """\n',
            code,
            '"""\n',
            "graph = Source(diagram)",
            #"display(Image(graph.pipe(format='png')))",
            'print("Here is the diagram")',
            "display(graph)"
        ]

        (res, message) = self.run_python_code(codes, query)
        return (res, message)
