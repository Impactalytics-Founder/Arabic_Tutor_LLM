"""
Simple WebSocket test client for the Voice Chat POC backend.

Run this script after starting the FastAPI server.  It connects to
``ws://localhost:8000/ws`` and sends a plain text message.  The
server should reply with a prefixed echo.  This script is useful for
verifying that the WebSocket infrastructure is functioning before
streaming audio is introduced.

Example:

```bash
uvicorn voice_chat_poc.backend.main:app --reload --host 0.0.0.0 --port 8000
python voice_chat_poc/backend/websocket_test.py
```
"""
import asyncio

import websockets


async def run_test() -> None:
    """Connects to the WebSocket and sends a text message to verify echo.

    The server should respond with ``echo: <your message>``.
    """
    uri = "ws://localhost:8000/ws"
    async with websockets.connect(uri) as websocket:
        message = "Hello from the test client"
        await websocket.send(message)
        response = await websocket.recv()
        print("Server response:", response)


if __name__ == "__main__":
    asyncio.run(run_test())
