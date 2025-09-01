import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/ws_client.dart';
import '../services/audio_recorder.dart';
import 'widgets/mic_button.dart';
import 'widgets/message_bubble.dart';

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
          // Text input is disabled in this version to focus on voice
        ],
      ),
      floatingActionButton: MicButton(
        isRecording: rec.isRecording,
        onStart: () async {
          // Tell server we’re starting the audio stream
          context.read<WsClient>().sendAudioStart(sampleRate: 16000);
          await context.read<AudioRecorder>().start(
            onChunk: (Uint8List chunk) {
              // Stream microphone bytes over WebSocket
              context.read<WsClient>().sendBinary(chunk);
            },
          );
        },
        onStop: () async {
          await context.read<AudioRecorder>().stop();
          // Signal the end of the stream to the backend
          context.read<WsClient>().sendAudioEnd();
        },
      ),
      floatingActionButtonLocation: FloatingActionButtonLocation.centerFloat,
    );
  }
}