import base64
import contextlib
import io
import json
import os
from typing import Any, Dict, List, Optional, Union

from dotenv import load_dotenv

try:
    import codeboxapi as cb
    import IPython
    import matplotlib.image as mpimg
    import matplotlib.pyplot as plt

    isLoadedRuntime = True
except ImportError:
    print("no jupyter_runtime related module. pip install codeboxapi IPython matplotlib numpy pydantic==1.10")
    isLoadedRuntime = False


from slashgpt.utils.print import print_error

load_dotenv()  # Load default environment variables (.env)
CODEBOX_API_KEY = os.getenv("CODEBOX_API_KEY")
if CODEBOX_API_KEY and CODEBOX_API_KEY != "local":
    cb.set_api_key(CODEBOX_API_KEY)


class PythonRuntime:
    def __init__(self, path: str):
        self.ipython: Optional[IPython.InteractiveShell] = None
        self.notebook: Dict[str, Any] = {}
        self.file_path = ""
        self.codebox: Optional[cb.CodeBox] = None
        self.folder_path = path
        if not os.path.isdir(self.folder_path):
            os.makedirs(self.folder_path)

    def create_notebook(self, module: str):
        if not isLoadedRuntime:
            return ({"result": "Not created a notebook", "notebook_name": "None"}, None)

        # Create a new notebook
        counter = 0
        notebook_name = "notebook"
        self.file_path = os.path.join(self.folder_path, f"{notebook_name}.ipynb")

        while os.path.exists(self.file_path):
            counter += 1
            notebook_name = f"notebook{counter}"
            self.file_path = os.path.join(self.folder_path, f"{notebook_name}.ipynb")

        self.notebook = {
            "cells": [{"cell_type": "markdown", "metadata": {}, "source": [f"# {module}"]}],
            "metadata": {},
            "nbformat": 4,
            "nbformat_minor": 5,
        }
        # Create the file
        with open(self.file_path, "w") as file:
            json.dump(self.notebook, file)

        if CODEBOX_API_KEY:
            if self.codebox:
                self.codebox.astop()
            self.codebox = cb.CodeBox()
            self.codebox.start()
        else:
            self.ipython = IPython.InteractiveShell()
        return ({"result": "created a notebook", "notebook_name": notebook_name}, None)

    def stop(self):
        if self.codebox:
            self.codebox.stop()
            self.codebox = None

    def run_python_code(self, code: list, query: str):
        if not isLoadedRuntime:
            return (None, "")
        if query:
            self.notebook["cells"].append(
                {
                    "cell_type": "markdown",
                    "metadata": {},
                    "source": [f"**User**: {query}"],
                }
            )

        for i in range(len(code)):
            if not code[i].endswith("\n"):
                code[i] += "\n"
        outputs = []

        if self.codebox:
            output: cb.CodeBoxOutput = self.codebox.run("".join(code))
            print("***", output.type)
            if output.type == "text":
                outputs.append(
                    {
                        "output_type": "execute_result",
                        "data": {"text/plain": str(output)},
                        "execution_count": 1,
                        "metadata": {},
                    }
                )
                result = str(output)
            elif output.type == "error":
                outputs.append({"output_type": "stream", "name": "stderr", "text": str(output)})
                result = str(output)
            elif output.type == "image/png":
                outputs.append(
                    {
                        "data": {"image/png": output.content},
                        "output_type": "display_data",
                        "metadata": {},
                    }
                )
                result = "Image was successfully generated and presented."

                # Present it in a pop up window
                image_data = base64.b64decode(output.content)
                image_stream = io.BytesIO(image_data)
                image_array = mpimg.imread(image_stream, format="png")
                plt.imshow(image_array)
                plt.axis("off")
                plt.show(block=False)
            else:
                result = f"Something went wrong ({output.type})"
        else:
            stdout = io.StringIO()
            stderr = io.StringIO()

            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                if self.ipython:
                    exec_result = self.ipython.run_cell("".join(code) if isinstance(code, list) else code)

            # Handle stdout
            if stdout.getvalue():
                outputs.append(
                    {
                        "output_type": "stream",
                        "name": "stdout",
                        "text": stdout.getvalue(),
                    }
                )

            # Handle stderr
            if stderr.getvalue():
                outputs.append(
                    {
                        "output_type": "stream",
                        "name": "stderr",
                        "text": stderr.getvalue(),
                    }
                )
                print_error(stderr.getvalue())

            # Handle execution result
            if exec_result.result is not None:
                outputs.append(
                    {
                        "output_type": "execute_result",
                        "execution_count": 1,
                        "data": {"text/plain": str(exec_result.result)},
                        "metadata": {},
                    }
                )
            result = exec_result.result
            if result is None:
                result = stdout.getvalue()
                if result is None:
                    result = stderr.getvalue()
                    if result is None:
                        result = "Done"

        cell = {
            "cell_type": "code",
            "metadata": {},
            "execution_count": 1,
            "source": "".join(code),
            "outputs": outputs,
        }
        self.notebook["cells"].append(cell)
        with open(self.file_path, "w") as file:
            json.dump(self.notebook, file, indent=2)

        return (str(result), f"```Python\n{''.join(code)}\n```")

    # GPT sometimes call this function
    def python(self, code: Union[str, List[str]], query: str):
        if isinstance(code, str):
            code = [code]
        return self.run_python_code(code, query)

    def draw_diagram(self, code: str, query: str):
        codes = [
            "from graphviz import Source\n",
            "from IPython.display import Image, display\n",
            'diagram = """\n',
            code,
            '"""\n',
            "graph = Source(diagram)",
            # "display(Image(graph.pipe(format='png')))",
            'print("Here is the diagram")',
            "display(graph)",
        ]

        (res, message) = self.run_python_code(codes, query)
        return (res, message)
