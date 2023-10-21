import asyncio
import websockets

async def main():
    async with websockets.connect("ws://localhost:8765") as websocket:
        while True:
            question = input("you: ")
            if question == "/bye":
                return
            await websocket.send(question)
            message = await websocket.recv()
            print("agent:", message)

if __name__ == "__main__":
    asyncio.run(main())