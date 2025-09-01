"""
FastAPI backend for the Voice Chat POC (Chunk 1 & 2).

This module defines a simple API and a WebSocket endpoint.  The goal of
this proof‑of‑concept is to lay the groundwork for a low‑latency
voice chat system using Azure Cognitive Services.  In this initial
iteration we implement:

* A health check at `/health` to verify the service is running.
* A WebSocket endpoint at `/ws` that echoes any text payload.  This
  will be extended to stream microphone audio and transcripts in later
  chunks.
* A synchronous POST endpoint at `/stt/recognize_once` that accepts
  small audio files (e.g., WAV/OGG/MP3) and returns the recognised
  text using Azure Speech‑to‑Text (STT).  This endpoint is intended
  solely for sanity‑checking your Azure credentials before tackling
  streaming STT.

The backend expects environment variables to be defined in a `.env`
file at the repository root.  See the provided `.env.example` for
details.
"""

import os
import tempfile
import shutil
from typing import Dict, Tuple

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
try:
    from fastapi import UploadFile, File  # type: ignore
    # Test import from python-multipart; if missing this will raise ImportError at runtime
    import multipart  # type: ignore  # noqa: F401
    _HAS_MULTIPART = True
except Exception:
    # Fallback if python-multipart isn't installed.  We won't register file upload routes.
    UploadFile = None  # type: ignore
    File = None  # type: ignore
    _HAS_MULTIPART = False
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
try:
    from dotenv import load_dotenv  # type: ignore
except ImportError:  # pragma: no cover
    # Define a fallback loader if python-dotenv is unavailable.
    def load_dotenv(dotenv_path: str | None = None) -> None:
        """Minimal .env loader used when python-dotenv is not installed.

        Reads key=value pairs from the specified file and populates
        ``os.environ`` for any variables that are not already set.

        Parameters
        ----------
        dotenv_path: str | None
            Path to the .env file.  If ``None``, defaults to `.env` in
            the current working directory.
        """
        path = dotenv_path or ".env"
        if not os.path.isfile(path):
            return
        try:
            with open(path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, value = line.split("=", 1)
                    os.environ.setdefault(key.strip(), value.strip())
        except Exception:
            # Fail silently if we can't read the file
            return

from .azure_stt import recognize_once_from_file

# Load environment variables from a `.env` file if present.  This call
# silently ignores missing files, so it's safe in production where
# variables may be set differently.
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

app = FastAPI(title="Voice Chat POC (Azure)")

# Configure Cross‑Origin Resource Sharing (CORS).  During development
# we allow all origins so that a Flutter web app can connect from
# `localhost`.  In production you should restrict this.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> Dict[str, str]:
    """Simple health check endpoint.

    Returns a JSON object indicating the service is up.
    """
    return {"status": "ok"}


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket) -> None:
    """
    Minimal WebSocket endpoint for the POC.

    Clients can connect over WebSocket and send plain text.  The server
    simply echoes the message back with an "echo:" prefix.  In later
    chunks this handler will stream microphone audio to Azure STT and
    return interim transcripts and final responses.
    """
    await ws.accept()
    try:
        while True:
            # Read incoming text
            data = await ws.receive_text()
            await ws.send_text(f"echo: {data}")
    except WebSocketDisconnect:
        # Client disconnected; nothing else to do
        return


if _HAS_MULTIPART:
    @app.post("/stt/recognize_once")
    async def stt_recognize_once(file: UploadFile = File(...)) -> JSONResponse:
        """
        Recognise speech from a single uploaded audio file using Azure STT.

        This endpoint accepts a short audio clip and returns the recognised
        transcript.  It is synchronous and intended only for initial
        connectivity testing—streaming recognition will be implemented
        later.
        """
        # Save uploaded file to a temporary location.  We use a named
        # temporary file so that Azure STT can read from disk.
        try:
            suffix = os.path.splitext(file.filename or "")[1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                shutil.copyfileobj(file.file, tmp)
                tmp_path = tmp.name

            text, info = recognize_once_from_file(tmp_path)
            return JSONResponse({"text": text, "info": info})
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        finally:
            # Make sure we clean up the temporary file
            try:
                os.unlink(tmp_path)  # type: ignore[name-defined]
            except Exception:
                pass
else:
    # If python-multipart is not installed, register a placeholder route
    @app.post("/stt/recognize_once")
    async def stt_recognize_once_unavailable() -> JSONResponse:
        """Placeholder STT endpoint when python-multipart is missing."""
        raise HTTPException(
            status_code=503,
            detail=(
                "The /stt/recognize_once endpoint is unavailable because the "
                "optional dependency python-multipart is not installed. "
                "Install it with 'pip install python-multipart' to enable file uploads."
            ),
        )