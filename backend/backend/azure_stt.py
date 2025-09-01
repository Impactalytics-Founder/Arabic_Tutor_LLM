"""
Helper functions for interacting with Azure Speech-to-Text.
"""
from __future__ import annotations

import os
import threading
from typing import Tuple, Dict, Any, Callable, Optional

try:
    import azure.cognitiveservices.speech as speechsdk  # type: ignore
    _HAS_AZURE = True
except ImportError:  # pragma: no cover
    speechsdk = None
    _HAS_AZURE = False

def _get_speech_config() -> speechsdk.SpeechConfig:
    # ... (This function remains unchanged)
    key = os.getenv("AZURE_SPEECH_KEY")
    region = os.getenv("AZURE_SPEECH_REGION")
    language = os.getenv("AZURE_STT_LANGUAGE", "ar-EG")
    if not key or not region:
        raise RuntimeError("Azure Speech credentials are not configured.")
    if not _HAS_AZURE or speechsdk is None:
        raise RuntimeError("azure-cognitiveservices-speech is not installed.")
    config = speechsdk.SpeechConfig(subscription=key, region=region)
    config.speech_recognition_language = language
    return config

def recognize_once_from_file(file_path: str) -> Tuple[str, Dict[str, Any]]:
    # ... (This function remains unchanged)
    if not _HAS_AZURE or speechsdk is None:
        raise RuntimeError("azure-cognitiveservices-speech is not installed.")
    speech_config = _get_speech_config()
    audio_config = speechsdk.audio.AudioConfig(filename=file_path)
    recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
    result = recognizer.recognize_once()
    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        return result.text, {"reason": "RecognizedSpeech"}
    if result.reason == speechsdk.ResultReason.NoMatch:
        return "", {"reason": "NoMatch", "details": "Speech could not be recognized"}
    if result.reason == speechsdk.ResultReason.Canceled:
        cancellation = speechsdk.CancellationDetails(result)
        raise RuntimeError(f"Recognition canceled: {cancellation.reason}; error_details={cancellation.error_details}")
    raise RuntimeError(f"Unexpected result from Azure STT: {result.reason}")

class StreamingRecognizer:
    """
    More robust wrapper for Azure Speech SDK that signals completion.
    """
    def __init__(self, language: str, on_partial: Callable[[str], None], on_final: Callable[[str], None]):
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

        # --- This event will reliably signal completion ---
        self.stop_event = threading.Event()

    def start(self, sample_rate: int = 16000):
        audio_format = speechsdk.audio.AudioStreamFormat(samples_per_second=sample_rate, bits_per_sample=16, channels=1)
        self._stream = speechsdk.audio.PushAudioInputStream(stream_format=audio_format)
        audio_config = speechsdk.audio.AudioConfig(stream=self._stream)

        speech_config = speechsdk.SpeechConfig(subscription=os.getenv("AZURE_SPEECH_KEY"), region=os.getenv("AZURE_SPEECH_REGION"))
        speech_config.speech_recognition_language = self.language

        self._recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

        # Connect callbacks
        self._recognizer.recognizing.connect(lambda evt: self.on_partial(evt.result.text))
        self._recognizer.recognized.connect(lambda evt: self.on_final(evt.result.text))
        # --- This callback is crucial for the fix ---
        self._recognizer.session_stopped.connect(lambda evt: self.stop_event.set())

        self._recognizer.start_continuous_recognition()

    def write_chunk(self, pcm_bytes: bytes):
        if self._stream:
            self._stream.write(pcm_bytes)

    def stop(self):
        if self._recognizer:
            self._recognizer.stop_continuous_recognition()
        if self._stream:
            self._stream.close()

        # Wait for the session_stopped event to be set by the callback
        self.stop_event.wait(timeout=5)