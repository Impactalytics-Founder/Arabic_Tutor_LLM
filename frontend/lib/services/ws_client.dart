import 'dart:convert';
import 'dart:typed_data';
import 'package:flutter/foundation.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:audioplayers/audioplayers.dart';

import '../config.dart';

class WsClient extends ChangeNotifier {
  WebSocketChannel? _channel;
  bool _connected = false;
  final List<String> _log = [];

  // For playing and buffering incoming audio
  final List<int> _ttsBuffer = [];
  final AudioPlayer _player = AudioPlayer();

  bool get isConnected => _connected;
  List<String> get log => List.unmodifiable(_log);

  void connect() {
    if (_connected) return;
    try {
      _channel = WebSocketChannel.connect(Uri.parse(AppConfig.wsUrl));
      _connected = true;
      _log.add('WS: connecting to ${AppConfig.wsUrl}');

      _channel!.stream.listen((event) async {
        final text = event is String ? event : '[binary ${event.runtimeType}]';
        try {
          final msg = jsonDecode(text);
          final type = msg['type'];
          final payload = msg['payload'];

          if (type == 'stt_partial') {
            _log.add('WS<- (partial) $payload');
          } else if (type == 'stt_final') {
            _log.add('WS<- (final) $payload');
          } else if (type == 'assistant_text') {
            _log.add('WS<- (assistant) $payload');
          } else if (type == 'tts_start') {
            _log.add('WS<- [TTS start]');
            _ttsBuffer.clear();
          } else if (type == 'tts_chunk_b64') {
            final bytes = base64Decode(payload as String);
            _ttsBuffer.addAll(bytes);
          } else if (type == 'tts_end') {
            _log.add('WS<- [TTS end, playing audio]');
            if (_ttsBuffer.isNotEmpty) {
              await _player.stop();
              await _player.play(BytesSource(Uint8List.fromList(_ttsBuffer)));
            }
          } else if (type == 'error') {
            _log.add('WS<- [ERROR] $payload');
          } else {
            _log.add('WS<- $text');
          }
        } catch (_) {
          _log.add('WS<- $text'); // Fallback for non-JSON messages
        }

        notifyListeners();
      }, onDone: () {
        _log.add('WS: closed');
        _connected = false;
        notifyListeners();
      }, onError: (e) {
        _log.add('WS error: $e');
        _connected = false;
        notifyListeners();
      });

      notifyListeners();
    } catch (e) {
      _log.add('WS connect error: $e');
    }
  }

  void disconnect() {
    _channel?.sink.close();
    _connected = false;
    notifyListeners();
  }

  void _sendMessage(Map<String, dynamic> message) {
     if (!_connected) {
      _log.add('WS not connected');
      notifyListeners();
      return;
    }
    _channel!.sink.add(jsonEncode(message));
  }

  void sendAudioStart({int sampleRate = 16000}) {
    _sendMessage({"type": "audio_start", "payload": {"sample_rate": sampleRate}});
    _log.add('WS-> audio_start sr=$sampleRate');
    notifyListeners();
  }

  void sendBinary(List<int> bytes) {
    final b64 = base64Encode(bytes);
    _sendMessage({"type": "audio_chunk_b64", "payload": b64});
    _log.add('WS-> [audio chunk ${bytes.length} bytes]');
    notifyListeners();
  }

  void sendAudioEnd() {
    _sendMessage({"type": "audio_end"});
    _log.add('WS-> audio_end');
    notifyListeners();
  }
}