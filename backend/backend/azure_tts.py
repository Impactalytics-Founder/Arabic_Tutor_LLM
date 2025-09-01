import os
import azure.cognitiveservices.speech as speechsdk


def text_to_speech(text: str) -> bytes :
    """Converts text to speech using Azure TTS and returns the audio as bytes."""
    speech_key = os.getenv("AZURE_SPEECH_KEY")
    speech_region = os.getenv("AZURE_SPEECH_REGION")
    voice_name = os.getenv("AZURE_TTS_VOICE", "ar-EG-SalmaNeural")

    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=speech_region)
    speech_config.speech_synthesis_voice_name = voice_name

    audio_output = speechsdk.audio.AudioOutputConfig(use_default_speaker=False,
                                                     stream=speechsdk.audio.PullAudioOutputStream())
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_output)

    result = synthesizer.speak_text_async(text).get()
    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted :
        return result.audio_data
    elif result.reason == speechsdk.ResultReason.Canceled :
        cancellation = result.cancellation_details
        raise RuntimeError(f"TTS Canceled: {cancellation.reason}, Error: {cancellation.error_details}")
    return b""