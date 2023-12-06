import asyncio
import os
import sys

import websockets
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), "../../src"))
from slashgpt.chat_config import ChatConfig  # noqa: E402
from slashgpt.chat_session import ChatSession  # noqa: E402

load_dotenv()
current_dir = os.path.dirname(__file__)
config = ChatConfig(current_dir)

manifest = {"title": "AI Agent on Websocket"}


async def main():
    print(f"Activating {manifest.get('title')}")
    async with websockets.connect("ws://localhost:8765") as websocket:
        while True:
            question = await websocket.recv()
            print("question:", question)
            session = ChatSession(config, manifest=manifest)
            session.append_user_question(question)
            (message, _function_call, _) = session.call_llm()
            await websocket.send(message)


if __name__ == "__main__":
    asyncio.run(main())
