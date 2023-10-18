import asyncio
import websockets

async def main():
    async with websockets.connect("ws://localhost:8765") as websocket:
        while True:
            question = input("you:")
            await websocket.send(question)
            message = await websocket.recv()
            print("message:", message)

print("foo")
if __name__ == "__main__":
    asyncio.run(main())