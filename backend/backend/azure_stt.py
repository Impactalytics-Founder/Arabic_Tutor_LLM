import os
import threading
from typing import Callable, Optional
import logging

try:
    import azure.cognitiveservices.speech as speechsdk
    _HAS_AZURE = True
except ImportError:
    speechsdk = None
    _HAS_AZURE = False

class StreamingRecognizer:
    def __init__(self, language: str, on_partial: Callable[[str], None], on_final: Callable[[str], None]):
        if not _HAS_AZURE:
            raise RuntimeError("Azure Speech SDK not installed.")

        self.language = language
        self.on_partial = on_partial
        self.on_final = on_final
        self.stop_event = threading.Event()

        speech_key = os.getenv("AZURE_SPEECH_KEY")
        speech_region = os.getenv("AZURE_SPEECH_REGION")
        if not speech_key or not speech_region:
            raise RuntimeError("Missing AZURE_SPEECH_KEY or AZURE_SPEECH_REGION")

        speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=speech_region)
        speech_config.speech_recognition_language = language

        self.audio_format = speechsdk.audio.AudioStreamFormat(samples_per_second=16000, bits_per_sample=16, channels=1)
        self.stream = speechsdk.audio.PushAudioInputStream(stream_format=self.audio_format)
        audio_config = speechsdk.audio.AudioConfig(stream=self.stream)

        self.recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

        # Connect callbacks
        self.recognizer.recognizing.connect(lambda evt: self.on_partial(evt.result.text))
        self.recognizer.recognized.connect(lambda evt: self.on_final(evt.result.text))
        self.recognizer.session_stopped.connect(self._session_stopped)
        self.recognizer.canceled.connect(self._canceled)

    def _session_stopped(self, evt):
        logging.info(f"Azure STT session stopped: {evt}")
        self.stop_event.set()

    def _canceled(self, evt):
        logging.error(f"Azure STT recognition canceled: {evt.reason} - {evt.error_details}")
        self.stop_event.set()

    def start(self):
        self.recognizer.start_continuous_recognition()

    def write_chunk(self, pcm_bytes: bytes):
        if self.stream:
            self.stream.write(pcm_bytes)

    def stop(self):
        if self.recognizer:
            self.recognizer.stop_continuous_recognition()
        if self.stream:
            self.stream.close()

        # Wait for the session to be officially stopped by Azure
        self.stop_event.wait(timeout=10)