import os
import json
import base64
import logging
import asyncio
from typing import Dict, Any, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

# Local imports
from .azure_stt import StreamingRecognizer
from .azure_tts import synthesize_tts_bytes, chunk_bytes
from .azure_llm import generate_response, get_azure_openai_client

# Setup basic logging to see detailed messages
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

try :
    from dotenv import load_dotenv

    load_dotenv()
except ImportError :
    logging.warning("python-dotenv not found. Skipping .env file loading.")

app = FastAPI(title="Voice Chat POC (Azure Full Pipeline)")


@app.on_event("startup")
async def startup_event() :
    app.state.llm_client = get_azure_openai_client()


app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"],
                   allow_headers=["*"])


@app.get("/health")
def health() :
    return {"status" : "ok"}


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket) :
    await ws.accept()
    rec: Optional[StreamingRecognizer] = None
    final_text = ""

    # Get the current event loop to safely send messages from background threads.
    loop = asyncio.get_running_loop()

    async def send_json(obj: Dict[str, Any]) :
        await ws.send_text(json.dumps(obj, ensure_ascii=False))

    try :
        while True :
            raw = await ws.receive_text()
            msg = json.loads(raw)
            mtype = msg.get("type")
            payload = msg.get("payload")

            if mtype == "audio_start" :
                final_text = ""

                def on_partial(text: str) :
                    if text :
                        # Use the thread-safe way to call the async function
                        asyncio.run_coroutine_threadsafe(send_json({"type" : "stt_partial", "payload" : text}), loop)

                def on_final(text: str) :
                    nonlocal final_text
                    if text :
                        final_text = text
                        # Use the thread-safe way to call the async function
                        asyncio.run_coroutine_threadsafe(send_json({"type" : "stt_final", "payload" : text}), loop)

                rec = StreamingRecognizer(language=os.getenv("AZURE_SPEECH_LANGUAGE", "ar-EG"), on_partial=on_partial,
                                          on_final=on_final)
                rec.start()

            elif mtype == "audio_chunk_b64" :
                if rec : rec.write_chunk(base64.b64decode(payload or ""))

            elif mtype == "audio_end" :
                if rec :
                    rec.stop()
                    rec = None

                # Add a small, reliable delay to ensure the final callback has time to be processed
                await asyncio.sleep(0.5)

                if final_text.strip() :
                    answer = generate_response(ws.app.state.llm_client, final_text)
                    await send_json({"type" : "assistant_text", "payload" : answer})

                    audio = synthesize_tts_bytes(answer)
                    if audio :
                        await send_json({"type" : "tts_start"})
                        for part in chunk_bytes(audio, 24000) :
                            await send_json(
                                {"type" : "tts_chunk_b64", "payload" : base64.b64encode(part).decode("ascii")})
                        await send_json({"type" : "tts_end"})

    except WebSocketDisconnect :
        logging.info("WebSocket disconnected.")
    except Exception as e :
        logging.error(f"WebSocket Error: {e}", exc_info=True)
        if rec : rec.stop()
        try :
            await send_json({"type" : "error", "payload" : str(e)})
        except Exception :
            pass