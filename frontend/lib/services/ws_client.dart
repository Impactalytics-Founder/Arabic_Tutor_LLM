import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:web_socket_channel/web_socket_channel.dart';

import '../config.dart';

/// Wrapper around WebSocketChannel to manage connection state and
/// expose simple send methods.  It also logs all inbound and outbound
/// messages so the UI can display a chat history.
class WsClient extends ChangeNotifier {
  WebSocketChannel? _channel;
  bool _connected = false;
  final List<String> _log = [];

  /// Returns true if the WebSocket is currently connected.
  bool get isConnected => _connected;

  /// Returns an immutable copy of the log.  Each entry is a string
  /// prefixed with `WS->` or `WS<-` to indicate direction.
  List<String> get log => List.unmodifiable(_log);

  /// Initiates a connection to the server.  Does nothing if already connected.
  void connect() {
    if (_connected) return;
    try {
      _channel = WebSocketChannel.connect(Uri.parse(AppConfig.wsUrl));
      _connected = true;
      _log.add('WS: connecting to ${AppConfig.wsUrl}');
      // Listen for incoming messages
      _channel!.stream.listen((event) {
        final text = event is String ? event : '[binary ${event.runtimeType}]';
        _log.add('WS<- $text');
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
    } catch (e) {
      _log.add('WS connect error: $e');
    }
    notifyListeners();
  }

  /// Closes the WebSocket connection if open.
  void disconnect() {
    _channel?.sink.close();
    _connected = false;
    notifyListeners();
  }

  /// Sends a JSON encoded text message with a `type` and `payload`.
  void sendText(String text) {
    if (!_connected) {
      _log.add('WS not connected');
      notifyListeners();
      return;
    }
    final payload = jsonEncode({"type": "text", "payload": text});
    _channel!.sink.add(payload);
    _log.add('WS-> $payload');
    notifyListeners();
  }

  /// Sends a binary audio chunk.  In this POC the chunk is base64
  /// encoded into a JSON message to stay compatible across platforms.
  void sendBinary(List<int> bytes) {
    if (!_connected) {
      _log.add('WS not connected');
      notifyListeners();
      return;
    }
    final b64 = base64Encode(bytes);
    final payload = jsonEncode({"type": "audio_chunk_b64", "payload": b64});
    _channel!.sink.add(payload);
    _log.add('WS-> [audio chunk ${bytes.length} bytes]');
    notifyListeners();
  }
}