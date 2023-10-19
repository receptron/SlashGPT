import asyncio
import websockets

async def main():
    async with websockets.connect("ws://localhost:8765") as websocket:
        while True:
            question = await websocket.recv()
            print("message:", question)
            await websocket.send(f"replying to {question}")

print("foo")
if __name__ == "__main__":
    asyncio.run(main())