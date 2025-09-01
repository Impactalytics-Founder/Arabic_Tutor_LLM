"""
Helper functions for interacting with Azure Speech-to-Text.

This module encapsulates the logic for performing speech recognition
using Azure Cognitive Services.  At this stage we implement
`recognize_once_from_file`, a convenience wrapper around the
Azure SDK’s synchronous `recognize_once` method.  When you call
`recognize_once_from_file`, the SDK loads the audio file, waits for
recognition to complete, and returns the recognised text along with
some metadata.  If the recognition fails, an exception is raised.

Environment variables used:

* ``AZURE_SPEECH_KEY`` – Your Azure Speech service subscription key.
* ``AZURE_SPEECH_REGION`` – The Azure region where your Speech
  resource is provisioned (e.g., ``westeurope``).
* ``AZURE_SPEECH_LANGUAGE`` – Optional.  The language locale code
  used for recognition.  Defaults to ``ar-EG`` (Arabic, Egypt),
  suitable for Modern Standard Arabic.

If these variables are not set, a RuntimeError will be thrown when
attempting to perform recognition.
"""
from __future__ import annotations

import os
import threading
from typing import Tuple, Dict, Any, Callable, Optional

try:
    import azure.cognitiveservices.speech as speechsdk  # type: ignore
    _HAS_AZURE = True
except ImportError:  # pragma: no cover
    # azure-cognitiveservices-speech may not be installed in all environments.
    speechsdk = None  # type: ignore
    _HAS_AZURE = False


def _get_speech_config() -> speechsdk.SpeechConfig:
    """Construct and return a configured SpeechConfig instance."""
    key = os.getenv("AZURE_SPEECH_KEY")
    region = os.getenv("AZURE_SPEECH_REGION")
    language = os.getenv("AZURE_STT_LANGUAGE", "ar-EG")
    if not key or not region:
        raise RuntimeError(
            "Azure Speech credentials are not configured. "
            "Please set AZURE_SPEECH_KEY and AZURE_SPEECH_REGION in your .env file."
        )
    # Import guard: ensure the Speech SDK is available
    if not _HAS_AZURE or speechsdk is None:
        raise RuntimeError(
            "azure-cognitiveservices-speech is not installed. "
            "Please install it by running 'pip install azure-cognitiveservices-speech'."
        )

    config = speechsdk.SpeechConfig(subscription=key, region=region)
    config.speech_recognition_language = language
    return config


def recognize_once_from_file(file_path: str) -> Tuple[str, Dict[str, Any]]:
    """Recognise speech in a single audio file using Azure STT."""
    # ... (rest of the function is unchanged, keeping it for completeness)
    if not _HAS_AZURE or speechsdk is None:
        raise RuntimeError(
            "azure-cognitiveservices-speech is not installed. "
            "Please install it before calling recognize_once_from_file."
        )

    speech_config = _get_speech_config()
    audio_config = speechsdk.audio.AudioConfig(filename=file_path)
    recognizer = speechsdk.SpeechRecognizer(
        speech_config=speech_config, audio_config=audio_config
    )

    result = recognizer.recognize_once()
    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        return result.text, {"reason": "RecognizedSpeech"}
    if result.reason == speechsdk.ResultReason.NoMatch:
        return "", {"reason": "NoMatch", "details": "Speech could not be recognized"}
    if result.reason == speechsdk.ResultReason.Canceled:
        cancellation = speechsdk.CancellationDetails(result)
        raise RuntimeError(
            f"Recognition canceled: {cancellation.reason}; error_details={cancellation.error_details}"
        )
    raise RuntimeError(f"Unexpected result from Azure STT: {result.reason}")

# --- Appended Streaming Recognizer Class ---

class StreamingRecognizer:
    """
    Simple wrapper around Azure Speech SDK PushAudioInputStream.
    - call start(sample_rate) to create the recognizer.
    - call write_chunk(bytes) as the client sends audio.
    - call stop() when done. Use on_partial/on_final to receive text.
    """
    def __init__(self,
                 language: str,
                 on_partial: Callable[[str], None],
                 on_final: Callable[[str], None]):
        if not _HAS_AZURE:
            raise RuntimeError("Azure Speech SDK not installed.")

        AZURE_SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")
        AZURE_SPEECH_REGION = os.getenv("AZURE_SPEECH_REGION")

        if not AZURE_SPEECH_KEY or not AZURE_SPEECH_REGION:
            raise RuntimeError("Missing AZURE_SPEECH_KEY/REGION")

        self.language = language
        self.on_partial = on_partial
        self.on_final = on_final
        self._stream: Optional[speechsdk.audio.PushAudioInputStream] = None
        self._recognizer: Optional[speechsdk.SpeechRecognizer] = None
        self._lock = threading.Lock()

    def start(self, sample_rate: int = 16000):
        audio_format = speechsdk.audio.AudioStreamFormat(
            samples_per_second=sample_rate,
            bits_per_sample=16,
            channels=1,
        )
        self._stream = speechsdk.audio.PushAudioInputStream(stream_format=audio_format)
        audio_config = speechsdk.audio.AudioConfig(stream=self._stream)

        speech_config = speechsdk.SpeechConfig(subscription=os.getenv("AZURE_SPEECH_KEY"), region=os.getenv("AZURE_SPEECH_REGION"))
        speech_config.speech_recognition_language = self.language

        self._recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

        def recognizing(evt):
            text = evt.result.text or ""
            if text:
                self.on_partial(text)

        def recognized(evt):
            text = evt.result.text or ""
            if text:
                self.on_final(text)

        self._recognizer.recognizing.connect(recognizing)
        self._recognizer.recognized.connect(recognized)

        self._recognizer.start_continuous_recognition_async().get()

    def write_chunk(self, pcm_bytes: bytes):
        with self._lock:
            if self._stream:
                self._stream.write(pcm_bytes)

    def stop(self):
        with self._lock:
            if self._stream:
                try:
                    self._stream.close()
                except Exception:
                    pass
        if self._recognizer:
            try:
                self._recognizer.stop_continuous_recognition_async().get()
            except Exception:
                pass