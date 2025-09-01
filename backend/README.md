# Voice Chat Proof‑of‑Concept (Azure)

This repository contains the first two chunks of a proof‑of‑concept (POC)
for a low‑latency voice chat application that relies on **Azure
Cognitive Services**.  The POC is written in Python using FastAPI
and is intended to serve as the backend for a Flutter front end that
will come later.

## Overview

The aim of this project is to build a simple but extensible service
that:

1. Accepts microphone audio streamed from a web/mobile client over
   WebSockets.
2. Uses Azure Speech‑to‑Text (STT) to transcribe that audio into text.
3. Passes the transcribed text to a language model (e.g., via OpenAI’s
   API) to generate an Arabic response.
4. Uses Azure Neural Text‑to‑Speech (TTS) to synthesise the Arabic
   response back into audio for playback on the client.

Chunks 1 & 2 establish the foundation by setting up the project
structure, implementing the basic FastAPI server and WebSocket
endpoint, and adding a synchronous STT endpoint for testing your
Azure credentials.

## Directory layout

```
voice_chat_poc/
├── .env.example             # Template for environment variables
├── backend/
│   ├── main.py              # FastAPI application (health, WebSocket, STT)
│   ├── azure_stt.py         # Helper for Azure Speech‑to‑Text
│   ├── requirements.txt     # Python dependencies
│   └── websocket_test.py    # Simple client to test the WebSocket echo
└── README.md                # This file
```

### Environment variables

All sensitive configuration (Azure keys, regions, etc.) is kept in a
`.env` file at the root of the repository.  A sample `.env.example`
is provided—copy it to `.env` and fill in your credentials.  The
backend uses `python-dotenv` to load these variables at runtime.  If
the Azure Speech key or region are missing, the STT functions will
raise a `RuntimeError` with an informative message.

### Running the backend

1. Create a virtual environment and install dependencies:

   ```bash
   cd voice_chat_poc/backend
   python -m venv .venv
   source .venv/bin/activate  # On Windows use .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Copy `.env.example` to `.env` in the project root and enter your
   Azure Speech subscription key, region and preferred language code.

3. Start the FastAPI server:

   ```bash
   uvicorn voice_chat_poc.backend.main:app --reload --host 0.0.0.0 --port 8000
   ```

4. Verify the service is running by visiting the health endpoint:

   ```bash
   curl http://localhost:8000/health
   # Expected response: {"status": "ok"}
   ```

### Testing STT (synchronous)

Before implementing streaming STT, you can test your Azure
credentials by sending a short audio file to the `/stt/recognize_once`
endpoint.  Use `curl` or a tool like Postman:

```bash
curl -F "file=@/path/to/sample.wav" \
  http://localhost:8000/stt/recognize_once

# Response: {"text": "…", "info": {"reason": "RecognizedSpeech"}}
```

Supported formats include WAV, OGG and MP3.  Note that this call is
blocking and meant only for sanity‑checking your setup; streaming
recognition will be added in the next chunk.

### Testing the WebSocket

The backend exposes a WebSocket at `/ws` that currently echoes any
text it receives.  You can test the echo behaviour with the included
`websocket_test.py` script:

```bash
python voice_chat_poc/backend/websocket_test.py
# Expected output: server replied: echo: hello from test client
```

This minimal echo service lays the groundwork for streaming audio in
later chunks.

## Next steps

With the scaffolding in place, the next chunk will:

1. Implement streaming Speech‑to‑Text by sending microphone audio
   over the WebSocket to Azure and returning interim transcripts.
2. Integrate a language model API to generate responses in Arabic.
3. Add a Text‑to‑Speech endpoint that converts the generated Arabic
   text into audio via Azure Neural TTS.
4. Scaffold a Flutter front end to capture microphone input, display
   transcripts and play audio responses.

This POC is intentionally simple but adheres to best practices in
structure and configuration, making it easy to extend and adapt as
features are layered on.