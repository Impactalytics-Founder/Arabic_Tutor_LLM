# Voice Chat POC Client (Flutter)

This directory contains the Flutter client for the voice chat
proof‑of‑concept described in chunks 1 & 2 of the project.  The
primary purpose of this client is to provide a minimal, cross‑platform
application that can capture microphone audio, send it to a backend
via WebSockets, and display messages from the server.  It forms the
foundation for the real‑time voice chat application and will be
extended in future chunks with streaming STT, LLM integration and
Text‑to‑Speech playback.

## Key features

* **Mic capture**: Uses the `record` plugin to capture audio from the
  microphone on web, iOS and Android.  Audio samples are delivered
  as streams of bytes.
* **WebSocket integration**: Connects to the backend WebSocket (default
  `ws://localhost:8000/ws`) and sends text or binary audio chunks.
* **Chat UI**: Displays sent and received messages in a simple chat
  view.  A floating action button toggles audio recording.
* **Configuration**: The WebSocket URL can be overridden at build
  time using the `--dart-define` flag.

## Running the client

You must have Flutter installed.  Clone or copy this directory and
run the following commands from the root of the repository:

```bash
cd voice_chat_poc_client
flutter pub get
flutter run -d chrome
```

During development you might run the backend on a different host or
port.  Use the `WS_URL` define to configure the WebSocket:

```bash
flutter run -d chrome --dart-define=WS_URL=ws://10.0.2.2:8000/ws
```

The chat page will show a log of WebSocket traffic and a microphone
button.  In this chunk the backend simply echoes text and ignores
audio, but the pipeline is in place for future streaming STT and
TTS.

## Files overview

* `pubspec.yaml` – Defines dependencies and Flutter configuration.
* `lib/main.dart` – Entry point that sets up providers and the
  Material app.
* `lib/config.dart` – Reads configuration (e.g. WebSocket URL) from
  compile‑time environment variables.
* `lib/services/ws_client.dart` – Simple WebSocket client that
  maintains connection state, logs messages and exposes `sendText`
  and `sendBinary`.
* `lib/services/audio_recorder.dart` – Wrapper around `record` for
  microphone permissions and streaming audio.
* `lib/ui/chat_page.dart` – Main UI with text input, chat log, and
  microphone button.
* `lib/ui/widgets/mic_button.dart` – Reusable button component for
  starting/stopping recording.
* `lib/ui/widgets/message_bubble.dart` – Simple widget for chat
  bubbles.

Use this client as a starting point for your own experiments and
extend it as you integrate more backend capabilities.