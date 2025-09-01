import 'dart:async';
import 'dart:typed_data';
import 'package:flutter/foundation.dart';
import 'package:record/record.dart';

/// A thin wrapper over the record plugin that handles microphone
/// permissions and exposes a stream of audio chunks.  The record
/// package automatically selects appropriate defaults for
/// sample rate and encoding across platforms.  You can tune these
/// parameters later in the project when integrating Azure STT.
class AudioRecorder extends ChangeNotifier {
  final Record _recorder = Record();
  StreamSubscription<Uint8List>? _subscription;
  bool _isRecording = false;

  /// Whether the recorder is currently active.
  bool get isRecording => _isRecording;

  Future<bool> _ensurePermission() async {
    final hasPermission = await _recorder.hasPermission();
    if (!hasPermission) {
      // On web the permission is requested automatically when
      // startStream is called.  On mobile this will fail without
      // adding the appropriate Android/iOS permissions in
      // AndroidManifest.xml and Info.plist.
      return false;
    }
    return true;
  }

  /// Starts recording and streaming microphone audio.  The [onChunk]
  /// callback will be invoked for each chunk of bytes captured.  The
  /// caller is responsible for forwarding these chunks over the
  /// WebSocket or handling them otherwise.
  Future<void> start({void Function(Uint8List chunk)? onChunk}) async {
    if (_isRecording) return;
    await _ensurePermission();
    final stream = await _recorder.startStream();
    _isRecording = true;
    notifyListeners();
    _subscription = stream.listen((data) {
      onChunk?.call(Uint8List.fromList(data));
    });
  }

  /// Stops recording and closes the underlying stream.  It is safe to
  /// call this method even if the recorder is not currently active.
  Future<void> stop() async {
    if (!_isRecording) return;
    await _subscription?.cancel();
    _subscription = null;
    await _recorder.stop();
    _isRecording = false;
    notifyListeners();
  }
}