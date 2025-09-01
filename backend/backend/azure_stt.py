"""
Helper functions for interacting with Azure Speech‑to‑Text.

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
from typing import Tuple, Dict, Any

try:
    import azure.cognitiveservices.speech as speechsdk  # type: ignore
    _HAS_AZURE = True
except ImportError:  # pragma: no cover
    # azure-cognitiveservices-speech may not be installed in all environments.
    speechsdk = None  # type: ignore
    _HAS_AZURE = False


def _get_speech_config() -> speechsdk.SpeechConfig:
    """Construct and return a configured SpeechConfig instance.
       ...
       """
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
    """Recognise speech in a single audio file using Azure STT.

    Parameters
    ----------
    file_path: str
        Absolute path to an audio file to be transcribed.

    Returns
    -------
    Tuple[str, Dict[str, Any]]
        A tuple containing the recognised text and a dictionary with
        metadata about the recognition result.  The metadata includes
        the result reason and may include error details.

    Raises
    ------
    RuntimeError
        If the recognition result indicates an error or the SDK
        encounters a cancellation.
    """
    # Ensure the Azure SDK is installed
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
        # No speech could be recognised
        return "", {"reason": "NoMatch", "details": "Speech could not be recognized"}
    if result.reason == speechsdk.ResultReason.Canceled:
        cancellation = speechsdk.CancellationDetails(result)
        raise RuntimeError(
            f"Recognition canceled: {cancellation.reason}; error_details={cancellation.error_details}"
        )
    # Fallback case for other result reasons
    raise RuntimeError(f"Unexpected result from Azure STT: {result.reason}")