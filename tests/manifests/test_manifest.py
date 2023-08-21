import unittest
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
# from lib.common import llms
from lib.manifest import Manifest



manifest_data = {
    "title": "Home Automation",
    "description": "Controls home equipments",
    "bot": "Home",
    "source": "snakajima",
    "model": "gpt-3.5-turbo-16k-0613",
    "modelx": "gpt-4-0613",
    "temperature": "0.0",
    "functions": "./resources/home.json",
    "actions": {
        "fill_bath": { "message":"Success. I started filling the bath tab." },
        "set_temperature": { "message":"Success. I set the teperature to {temperature} for {location}" },
        "start_sprinkler": { "message":"Success. I started the sprinkler for {location}" },
        "take_picture": { "message":"Success. I took a picture of {location}" },
        "play_music": { "message":"Success. I started playing {music} in {location}" },
        "control_light": { "message":"Success. The light switch of {location} is now {switch}." }
    },
    "sample": "Turn on the light of the living room, take a picture, and turn it off",
    "prompt": [
        "Don't make any assumptions about what property values to plug into functions.",
        "Ask for clarification if a user request is ambiguous."
    ]
}
manifest = Manifest(manifest_data, "ai-agent")
    
def test_botname():
    assert manifest.botname() == "Home"
    
def test_username():
    assert manifest.username() == "You(ai-agent)"

