import os
import sys

from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), "../../src"))

from slashgpt.chat_config import ChatConfig  # noqa: E402
from slashgpt.chat_session import ChatSession  # noqa: E402

load_dotenv()
current_dir = os.path.dirname(__file__)


class TestGPT:
    def process_event(self, callback_type, data):
        if callback_type == "bot":
            self.res = data

    def test_gpt(self):
        if os.getenv("OPENAI_API_KEY", None) is not None:
            config = ChatConfig(current_dir)
            session = ChatSession(config, manifest={})
            session.append_user_question("Which year was the declaration of independence written?")
            session.call_loop(self.process_event)
            assert "1776" in self.res
