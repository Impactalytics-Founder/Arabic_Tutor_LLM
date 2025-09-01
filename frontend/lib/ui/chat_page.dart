import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/ws_client.dart';
import '../services/audio_recorder.dart';
import 'widgets/mic_button.dart';
import 'widgets/message_bubble.dart';

/// Main chat page that composes the UI for the voice chat POC.  It
/// connects to the WebSocket on initial build and displays log
/// entries in a scrollable list.  Users can type messages or send
/// audio chunks by tapping the microphone button.
class ChatPage extends StatefulWidget {
  const ChatPage({super.key});

  @override
  State<ChatPage> createState() => _ChatPageState();
}

class _ChatPageState extends State<ChatPage> {
  final TextEditingController _textCtrl = TextEditingController();

  @override
  void initState() {
    super.initState();
    // Connect to the WebSocket once the first frame is rendered.
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<WsClient>().connect();
    });
  }

  @override
  void dispose() {
    _textCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final ws = context.watch<WsClient>();
    final rec = context.watch<AudioRecorder>();
    return Scaffold(
      appBar: AppBar(
        title: const Text('Voice Chat POC'),
        actions: [
          IconButton(
            onPressed: ws.isConnected ? ws.disconnect : ws.connect,
            icon: Icon(ws.isConnected ? Icons.link_off : Icons.link),
            tooltip: ws.isConnected ? 'Disconnect' : 'Connect',
          ),
        ],
      ),
      body: Column(
        children: [
          // Display the log as a chat-like list.  Each entry is
          // prefixed with WS-> or WS<- so we use this to decide
          // alignment.  Remove the prefix for display.
          Expanded(
            child: ListView.builder(
              padding: const EdgeInsets.all(12),
              itemCount: ws.log.length,
              itemBuilder: (context, index) {
                final entry = ws.log[index];
                final mine = entry.startsWith('WS->');
                final text = entry.replaceFirst(RegExp(r'^WS[<-]\s*'), '');
                return MessageBubble(text: text, mine: mine);
              },
            ),
          ),
          // Text input row
          Padding(
            padding: const EdgeInsets.fromLTRB(12, 0, 12, 12),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _textCtrl,
                    decoration: const InputDecoration(
                      hintText: 'Type a message to send via WS...',
                      border: OutlineInputBorder(),
                    ),
                    onSubmitted: (_) => _sendText(ws),
                  ),
                ),
                const SizedBox(width: 8),
                ElevatedButton(
                  onPressed: () => _sendText(ws),
                  child: const Text('Send'),
                ),
              ],
            ),
          ),
        ],
      ),
      floatingActionButton: MicButton(
        isRecording: rec.isRecording,
        onStart: () async {
          await context.read<AudioRecorder>().start(onChunk: (Uint8List chunk) {
            context.read<WsClient>().sendBinary(chunk);
          });
        },
        onStop: () async {
          await context.read<AudioRecorder>().stop();
          // Future: send end-of-stream signal to backend.
        },
      ),
      floatingActionButtonLocation: FloatingActionButtonLocation.centerFloat,
    );
  }

  void _sendText(WsClient ws) {
    final text = _textCtrl.text.trim();
    if (text.isEmpty) return;
    ws.sendText(text);
    _textCtrl.clear();
  }
}