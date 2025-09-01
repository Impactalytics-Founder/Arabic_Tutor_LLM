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
  // This text controller isn't used for voice, but we can keep it.
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
    final rec = context.watch<AudioRecordingService>();

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
              reverse: true, // Show latest messages at the bottom
              padding: const EdgeInsets.all(12),
              itemCount: ws.log.length,
              itemBuilder: (context, index) {
                final entry = ws.log.reversed.toList()[index];
                final mine = entry.startsWith('WS->');
                final text = entry.replaceFirst(RegExp(r'^WS[<-]\s*'), '');
                return MessageBubble(text: text, mine: mine);
              },
            ),
          ),
        ],
      ),
      floatingActionButton: MicButton(
        isRecording: rec.isRecording,
        onStart: () async {
          // --- THIS IS THE CORRECTED LOGIC ---
          // 1. Start the recording service first. It will wait for audio chunks.
          await context.read<AudioRecordingService>().start(
            onChunk: (Uint8List chunk) {
              // This callback will now fire correctly *after* audio_start is sent.
              context.read<WsClient>().sendBinary(chunk);
            },
          );

          // 2. NOW that the recorder is listening, tell the backend we are starting.
          context.read<WsClient>().sendAudioStart(sampleRate: 16000);
        },
        onStop: () async {
          await context.read<AudioRecordingService>().stop();
          context.read<WsClient>().sendAudioEnd();
        },
      ),
      floatingActionButtonLocation: FloatingActionButtonLocation.centerFloat,
    );
  }
}