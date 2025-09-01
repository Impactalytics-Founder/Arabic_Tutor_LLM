import os
from typing import Iterable
import logging

try :
    import azure.cognitiveservices.speech as speechsdk

    _HAS_AZURE = True
except ImportError :
    speechsdk = None
    _HAS_AZURE = False


def synthesize_tts_bytes(text: str) -> bytes :
    if not _HAS_AZURE :
        logging.error("Azure Speech SDK not installed, cannot synthesize TTS.")
        return b""

    speech_key = os.getenv("AZURE_SPEECH_KEY")
    speech_region = os.getenv("AZURE_SPEECH_REGION")
    tts_voice = os.getenv("AZURE_TTS_VOICE", "ar-EG-SalmaNeural")

    if not speech_key or not speech_region :
        logging.error("Azure Speech credentials for TTS are not configured.")
        return b""

    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=speech_region)
    speech_config.speech_synthesis_voice_name = tts_voice
    speech_config.set_speech_synthesis_output_format(speechsdk.SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3)

    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)
    result = synthesizer.speak_text_async(text).get()

    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted :
        return result.audio_data
    elif result.reason == speechsdk.ResultReason.Canceled :
        cancellation = result.cancellation_details
        logging.error(f"TTS Canceled: {cancellation.reason}, Error: {cancellation.error_details}")
    return b""


def chunk_bytes(src: bytes, chunk_size: int = 16000) -> Iterable[bytes] :
    for i in range(0, len(src), chunk_size) :
        yield src[i :i + chunk_size]