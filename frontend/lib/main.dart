import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'services/ws_client.dart';
import 'services/audio_recorder.dart'; // This now refers to the file with AudioRecordingService
import 'ui/chat_page.dart';

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
        // Use the new class name here
        ChangeNotifierProvider(create: (_) => AudioRecordingService()),
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