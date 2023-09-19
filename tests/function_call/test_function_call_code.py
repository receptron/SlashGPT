import os
import sys
from typing import List

import pytest

sys.path.append(os.path.join(os.path.dirname(__file__), "../../src"))

from slashgpt.llms.engine.base import LLMEngineBase  # noqa: E402
from slashgpt.manifest import Manifest  # noqa: E402


class LLMEngineTest(LLMEngineBase):
    def __init__(self, llm_model):
        self.llm_model = llm_model
        return

    def test_extract_function_call(self, last_message: dict, manifest: Manifest, res: str):
        return self._extract_function_call(last_message, manifest, res, True)

    def chat_completion(self, messages: List[dict], manifest: Manifest, verbose: bool):
        return (None, None, None)


@pytest.fixture
def engine():
    return LLMEngineTest({})


manifest = Manifest({"notebook": True})


def test_pip_result_should_call(engine):
    last_message = {"role": "assistant", "content": "```Python\n!pip install geopandas\n\n```", "preset": False}

    function_call = engine.test_extract_function_call(last_message, manifest, last_message["content"])
    data = function_call.data()
    print(data)
    assert data["name"] == "run_python_code"
    assert data["arguments"]["code"][0] == "!pip install geopandas"


def test_from_result_should_call(engine):
    last_message = {
        "role": "assistant",
        "content": '```Python\nfrom selenium.webdriver.common.by import By\n\ninput_field = driver.find_element(By.NAME, "input_name")\n\n```',
        "preset": False,
    }

    function_call = engine.test_extract_function_call(last_message, manifest, last_message["content"])
    data = function_call.data()
    print(data)
    assert data["name"] == "run_python_code"
    assert data["arguments"]["code"][0] == "from selenium.webdriver.common.by import By"


def test_import_result_should_call(engine):
    last_message = {
        "role": "assistant",
        "content": '```Python\nimport yfinance as yf\nimport matplotlib.pyplot as plt\n\n# Get the stock data for Apple and Tesla\napple = yf.Ticker("AAPL")\ntesla = yf.Ticker("TSLA")\n\n# Get the historical stock prices for the past 4 years\napple_history = apple.history(period="4y")\ntesla_history = tesla.history(period="4y")\n\n# Plot the stock prices\nplt.figure(figsize=(12, 6))\nplt.plot(apple_history.index, apple_history["Close"], label="Apple")\nplt.plot(tesla_history.index, tesla_history["Close"], label="Tesla")\nplt.xlabel("Date")\nplt.ylabel("Stock Price")\nplt.title("4 Year Stock Price of Apple and Tesla")\nplt.legend()\nplt.show()\n\n```',
        "preset": False,
    }

    function_call = engine.test_extract_function_call(last_message, manifest, last_message["content"])
    data = function_call.data()
    print(data)
    assert data["name"] == "run_python_code"
    assert data["arguments"]["code"][0] == "import yfinance as yf"


def test_markdown_result_should_call(engine):
    last_message = {
        "role": "assistant",
        "content": "```Python\nYear,Country,Population,Electric Vehicles\n2010,World,6.845 billion,1.2 million\n2011,World,6.974 billion,1.3 million\n2012,World,7.103 billion,1.4 million\n2013,World,7.232 billion,1.5 million\n2014,World,7.361 billion,1.6 million\n\n```",
        "preset": False,
    }

    function_call = engine.test_extract_function_call(last_message, manifest, last_message["content"])
    assert function_call is None
