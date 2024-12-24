import asyncio
import json
import websockets
from websockets.exceptions import ConnectionClosedError

# WebSocket server configuration
HOST = '0.0.0.0'
PORT = 8080

connected_clients = set()

async def handle_connection(websocket, path):
    global connected_clients
    # Track the new connection
    connected_clients.add(websocket)
    client_address = websocket.remote_address[0]
    print(f"New client connected from {client_address}")
    print(f"Total connected clients: {len(connected_clients)}")

    # Send initial connection confirmation
    await websocket.send(json.dumps({"type": "connected", "message": "Successfully connected to server"}))

    try:
        async for message in websocket:
            print(f"Received audio chunk: {len(message)} bytes")
            # Broadcast the message to all other clients
            for client in connected_clients:
                if client != websocket and client.open:
                    try:
                        await client.send(message)
                    except ConnectionClosedError:
                        pass
    except ConnectionClosedError as e:
        print(f"Client disconnected with error: {e}")
    finally:
        # Remove the client from the set
        connected_clients.remove(websocket)
        print(f"Client disconnected. Remaining clients: {len(connected_clients)}")

async def heartbeat():
    while True:
        disconnected_clients = []
        for websocket in connected_clients:
            try:
                await websocket.ping()
            except ConnectionClosedError:
                disconnected_clients.append(websocket)
        for client in disconnected_clients:
            connected_clients.remove(client)
        await asyncio.sleep(30)

async def main():
    server = await websockets.serve(handle_connection, HOST, PORT)
    print(f"WebSocket server is running on ws://{HOST}:{PORT}")
    print("Ready to accept connections...")

    # Start the heartbeat task
    asyncio.create_task(heartbeat())

    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())
