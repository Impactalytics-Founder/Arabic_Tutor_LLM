import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'services/ws_client.dart';
import 'services/audio_recorder.dart';
import 'ui/chat_page.dart';

/// Entry point for the Flutter voice chat POC client.  Registers
/// providers for the WebSocket client and audio recorder, and
/// launches the chat page.  Material 3 styling is used with a blue
/// seed color.
void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const VoiceChatApp());
}

class VoiceChatApp extends StatelessWidget {
  const VoiceChatApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => WsClient()),
        ChangeNotifierProvider(create: (_) => AudioRecorder()),
      ],
      child: MaterialApp(
        debugShowCheckedModeBanner: false,
        theme: ThemeData(
          useMaterial3: true,
          colorSchemeSeed: Colors.blue,
        ),
        home: const ChatPage(),
      ),
    );
  }
}