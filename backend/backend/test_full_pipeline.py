import asyncio
import websockets
import base64
import json

# --- IMPORTANT: Replace with the path to a short audio file on your computer ---
# --- You can record one yourself. It should be a WAV file. ---
# Use a raw string (r"...") to handle the backslashes correctly in Python
TEST_AUDIO_FILE_PATH = r"C:\Users\Alsho\PycharmProjects\LLM Projects\Arabic-Tutor-LLM-Sep\Agent_v1\backend\audio_files\Recording.wav"
async def run_test():
    uri = "ws://localhost:8000/ws"
    print(f"Connecting to {uri}...")

    try:
        with open(TEST_AUDIO_FILE_PATH, "rb") as f:
            audio_data = f.read()
    except FileNotFoundError:
        print(f"ERROR: Test audio file not found at '{TEST_AUDIO_FILE_PATH}'")
        print("Please record a short WAV file and update the path in this script.")
        return

    async with websockets.connect(uri) as websocket:
        print("Connection successful.")

        # 1. Send audio_start message
        print(">>> Sending audio_start...")
        await websocket.send(json.dumps({
            "type": "audio_start",
            "payload": {"sample_rate": 16000}
        }))

        # 2. Send audio chunk
        print(">>> Sending audio_chunk_b64...")
        await websocket.send(json.dumps({
            "type": "audio_chunk_b64",
            "payload": base64.b64encode(audio_data).decode('ascii')
        }))

        # 3. Send audio_end message
        print(">>> Sending audio_end...")
        await websocket.send(json.dumps({"type": "audio_end"}))
        print("--- All messages sent. Now listening for responses... ---")

        # 4. Listen for all server responses
        try:
            while True:
                response = await websocket.recv()
                print(f"<<< Received: {response}")
        except websockets.exceptions.ConnectionClosed:
            print("--- Connection closed by server. Test finished. ---")

if __name__ == "__main__":
    asyncio.run(run_test())