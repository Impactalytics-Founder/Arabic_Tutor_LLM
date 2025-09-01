import 'dart:async';
import 'dart:typed_data';
import 'package:flutter/foundation.dart';
import 'package:record/record.dart';

// Class renamed to avoid conflicts with the package
class AudioRecordingService extends ChangeNotifier {
  // The package now provides an AudioRecorder class
  final AudioRecorder _recorder = AudioRecorder();
  StreamSubscription<Uint8List>? _subscription;
  bool _isRecording = false;

  bool get isRecording => _isRecording;

  Future<void> start({void Function(Uint8List chunk)? onChunk}) async {
    if (_isRecording) return;

    // Check for permission
    if (await _recorder.hasPermission()) {
      // The startStream method is now start() and requires a config
      final stream = await _recorder.startStream(const RecordConfig(encoder: AudioEncoder.pcm16bits));
      _isRecording = true;
      notifyListeners();

      _subscription = stream.listen((data) {
        onChunk?.call(data); // The stream already provides Uint8List
      });
    }
  }

  Future<void> stop() async {
    if (!_isRecording) return;

    await _subscription?.cancel();
    _subscription = null;
    await _recorder.stop();
    _isRecording = false;
    notifyListeners();
  }

  // It's good practice to dispose of the recorder
  @override
  void dispose() {
    _recorder.dispose();
    super.dispose();
  }
}