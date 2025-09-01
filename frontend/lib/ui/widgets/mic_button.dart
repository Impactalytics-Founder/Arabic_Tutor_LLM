import 'package:flutter/material.dart';

/// A floating action button that toggles between recording and
/// not-recording states.  The parent widget should provide
/// [onStart] and [onStop] callbacks to begin and end microphone
/// capture respectively.
class MicButton extends StatelessWidget {
  final bool isRecording;
  final VoidCallback onStart;
  final VoidCallback onStop;

  const MicButton({
    super.key,
    required this.isRecording,
    required this.onStart,
    required this.onStop,
  });

  @override
  Widget build(BuildContext context) {
    return FloatingActionButton.extended(
      onPressed: isRecording ? onStop : onStart,
      icon: Icon(isRecording ? Icons.stop : Icons.mic),
      label: Text(isRecording ? 'Stop' : 'Speak'),
    );
  }
}