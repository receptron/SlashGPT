import asyncio
import websockets

async def handle_websocket(websocket, path):
    while True:
        message = await websocket.recv()
        print("message:", message)
        await websocket.send(f"replying to {message}")

async def main():
    async with websockets.serve(handle_websocket, "localhost", 8765):
        await asyncio.sleep(2000000)

if __name__ == "__main__":
    asyncio.run(main())