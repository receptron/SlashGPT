import json
import os
import sys

from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), "../../src"))

from slashgpt.chat_config import ChatConfig  # noqa: E402
from slashgpt.chat_session import ChatSession  # noqa: E402

load_dotenv()
current_dir = os.path.dirname(__file__)
config = ChatConfig(current_dir)


class TestGPT:
    def process_event(self, callback_type, data):
        if callback_type == "bot":
            self.res = data  # record the output from the LLM

    def test_gpt(self):
        if os.getenv("OPENAI_API_KEY", None) is not None:
            question = "What year was the Declaration of Independence written？"
            # Just calls LLM (no process for function_call)
            session = ChatSession(config, manifest={})
            session.append_user_question(question)
            (message, _function_call) = session.call_llm()
            assert "1776" in message

            # legasy GPT (completion API)
            session = ChatSession(config, manifest=dict(model="gpt-3.5-turbo-instruct"))
            session.append_user_question(question)
            (message, _function_call) = session.call_llm()
            assert "1776" in message

            # Callback style (function_call will be processed)
            session = ChatSession(config, manifest={})
            session.append_user_question(question)
            session.call_loop(self.process_event)
            assert "1776" in self.res

    def test_function_call(self):
        if os.getenv("OPENAI_API_KEY", None) is not None:
            manifest = {
                "prompt": "When the user makes a request, call the 'play' function to play the specified music",
                "functions": [
                    {
                        "name": "play",
                        "description": "Play a music",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "title": {
                                    "type": "string",
                                    "description": "Title of the music.",
                                }
                            },
                        },
                        "required": ["title"],
                    }
                ],
            }
            session = ChatSession(config, manifest=manifest)
            session.append_user_question("Play Bohemian Rhapsody")
            (message, function_call) = session.call_llm()
            assert function_call is not None
            data = function_call.data()
            print(data)
            assert data.name == "play"
            arguments = data.arguments
            assert arguments is not None
            if isinstance(arguments, str):
                arguments = json.loads(arguments)
            assert arguments["title"] == "Bohemian Rhapsody"
