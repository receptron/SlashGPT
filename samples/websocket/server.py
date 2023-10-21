import asyncio

import websockets

connected_clients = set()


async def handle_websocket(websocket, path):
    connected_clients.add(websocket)
    print(f"Connected {path}")

    try:
        while True:
            message = await websocket.recv()
            # Now we want to send this message to all clients, excluding the sender.
            for client in connected_clients:
                if client != websocket:  # Don't send the message back to the same client who sent it
                    # You can format the message, or even add sender details, timestamps, etc.
                    await client.send(message)  # Forward the message to another client

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
