import os
from typing import Iterable
import azure.cognitiveservices.speech as speechsdk

def synthesize_tts_bytes(text: str) -> bytes:
    """Converts text to speech using Azure TTS and returns audio bytes."""
    AZURE_SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")
    AZURE_SPEECH_REGION = os.getenv("AZURE_SPEECH_REGION")
    AZURE_TTS_VOICE = os.getenv("AZURE_TTS_VOICE", "ar-EG-SalmaNeural")

    if not AZURE_SPEECH_KEY or not AZURE_SPEECH_REGION:
        print("Warning: Azure Speech Key/Region not configured.")
        return b""

    speech_config = speechsdk.SpeechConfig(subscription=AZURE_SPEECH_KEY, region=AZURE_SPEECH_REGION)
    speech_config.speech_synthesis_voice_name = AZURE_TTS_VOICE
    # Output format: MP3 is smaller and suitable for streaming
    speech_config.set_speech_synthesis_output_format(
        speechsdk.SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3
    )

    # Use a PullAudioOutputStream to get the audio data as a byte array
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)
    result = synthesizer.speak_text_async(text).get()

    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        return result.audio_data
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation = result.cancellation_details
        print(f"TTS Canceled: {cancellation.reason}, Error: {cancellation.error_details}")
        return b""
    return b""

def chunk_bytes(src: bytes, chunk_size: int = 16_000) -> Iterable[bytes]:
    """Yields fixed-size chunks from a byte string."""
    for i in range(0, len(src), chunk_size):
        yield src[i:i + chunk_size]