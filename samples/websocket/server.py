import asyncio
import websockets

connected_clients = set()

async def handle_websocket(websocket, path):
    connected_clients.add(websocket)
    print(f"Connected {path}")

    try:
        while True:
            message = await websocket.recv()
            print("message:", message)
            await websocket.send(f"replying to {message}")
    except websockets.exceptions.ConnectionClosed:
        # Connection was lost, remove client
        print("Connection closed {path}")
    finally:
        # Make sure to remove the client in any case to prevent memory leaks
        connected_clients.remove(websocket)

async def main():
    async with websockets.serve(handle_websocket, "localhost", 8765):
        await asyncio.sleep(2000000)

if __name__ == "__main__":
    asyncio.run(main())