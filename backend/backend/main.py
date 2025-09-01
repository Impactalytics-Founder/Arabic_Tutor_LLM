import os
import json
import base64
import logging
from typing import Dict, Any, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

# Local imports
from .azure_stt import StreamingRecognizer
from .azure_tts import synthesize_tts_bytes, chunk_bytes
from .azure_llm import generate_response, get_azure_openai_client # Use our existing azure_llm

# .env loader
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not found. Skipping .env file loading.")

app = FastAPI(title="Voice Chat POC (Azure Full Pipeline)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Be more specific in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initializes the Azure OpenAI client at application startup."""
    app.state.llm_client = get_azure_openai_client()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    rec: Optional[StreamingRecognizer] = None
    got_final = False
    final_text = ""
    AZURE_SPEECH_LANGUAGE = os.getenv("AZURE_SPEECH_LANGUAGE", "ar-EG")

    async def send_json(obj: Dict[str, Any]):
        await ws.send_text(json.dumps(obj, ensure_ascii=False))

    try:
        while True:
            raw = await ws.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await send_json({"type": "error", "payload": "invalid json"})
                continue

            mtype = msg.get("type")
            payload = msg.get("payload")

            if mtype == "audio_start":
                sample_rate = int(payload.get("sample_rate", 16000)) if isinstance(payload, dict) else 16000

                def on_partial(text: str):
                    import asyncio
                    asyncio.create_task(send_json({"type": "stt_partial", "payload": text}))

                def on_final(text: str):
                    nonlocal got_final, final_text
                    got_final = True
                    final_text = text
                    import asyncio
                    asyncio.create_task(send_json({"type": "stt_final", "payload": text}))

                rec = StreamingRecognizer(language=AZURE_SPEECH_LANGUAGE, on_partial=on_partial, on_final=on_final)
                rec.start(sample_rate=sample_rate)

            elif mtype == "audio_chunk_b64":
                if not rec:
                    await send_json({"type": "error", "payload": "audio_start must be sent first"})
                    continue
                try:
                    chunk = base64.b64decode(payload or "")
                    rec.write_chunk(chunk)
                except Exception:
                    await send_json({"type": "error", "payload": "bad base64 audio chunk"})

            elif mtype == "audio_end":
                if rec:
                    rec.stop()
                    rec = None

                if got_final and final_text.strip():
                    # Use azure_llm.py's generate_response function
                    answer = generate_response(ws.app.state.llm_client, final_text)
                    await send_json({"type": "assistant_text", "payload": answer})

                    await send_json({"type": "tts_start"})
                    audio = synthesize_tts_bytes(answer)
                    if audio:
                        for part in chunk_bytes(audio, 24_000):
                            await send_json({"type": "tts_chunk_b64", "payload": base64.b64encode(part).decode("ascii")})
                    await send_json({"type": "tts_end"})

                got_final = False
                final_text = ""

            else:
                await send_json({"type": "error", "payload": f"unknown message type: {mtype}"})

    except WebSocketDisconnect:
        logging.info("WebSocket disconnected.")
    except Exception as e:
        logging.error(f"WebSocket Error: {e}")
        try:
            await send_json({"type": "error", "payload": str(e)})
        except Exception:
            pass