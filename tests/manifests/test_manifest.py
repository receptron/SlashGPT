import os
import sys

import pytest

sys.path.append(os.path.join(os.path.dirname(__file__), "../../src"))

from slashgpt.manifest import Manifest  # noqa: E402

current_dir = os.path.dirname(__file__)


@pytest.fixture
def manifest():
    manifest_data = {
        "title": "Home Automation",
        "description": "Controls home equipments",
        "bot": "Home",
        "source": "snakajima",
        "model": "gpt-3.5-turbo-16k-0613",
        "modelx": "gpt-4-0613",
        "temperature": "0.0",
        "functions": "../../resources/functions/home.json",
        "actions": {
            "fill_bath": {"message": "Success. I started filling the bath tab."},
            "set_temperature": {"message": "Success. I set the teperature to {temperature} for {location}"},
            "start_sprinkler": {"message": "Success. I started the sprinkler for {location}"},
            "take_picture": {"message": "Success. I took a picture of {location}"},
            "play_music": {"message": "Success. I started playing {music} in {location}"},
            "control_light": {"message": "Success. The light switch of {location} is now {switch}."},
        },
        "sample": "Turn on the light of the living room, take a picture, and turn it off",
        "prompt": [
            "Don't make any assumptions about what property values to plug into functions.",
            "Ask for clarification if a user request is ambiguous.",
        ],
    }
    return Manifest(manifest_data, current_dir, "ai-agent")


def test_username(manifest):
    assert manifest.username() == "You(ai-agent)"


def test_botname(manifest):
    assert manifest.botname() == "Home"


# def test_actions(manifest):
#    assert manifest.actions() == ""


def test_title(manifest):
    assert manifest.title() == "Home Automation"


def test_temperature(manifest):
    assert manifest.temperature() == 0.0


def test_model(manifest):
    assert manifest.model() == "gpt-3.5-turbo-16k-0613"


# def test_functions(manifest):
#    assert manifest.functions() == json.load

# def test_read_module(manifest):
#    assert manifest.read_module() == ""


def test_prompt_data(manifest):
    assert manifest.prompt_data() == "\n".join(
        [
            "Don't make any assumptions about what property values to plug into functions.",
            "Ask for clarification if a user request is ambiguous.",
        ]
    )
