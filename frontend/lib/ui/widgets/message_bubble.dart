import 'package:flutter/material.dart';

/// A simple container that displays a chat message.  Aligns the
/// message to the left or right depending on whether it originated
/// from the current user (mine == true) or from the server.
class MessageBubble extends StatelessWidget {
  final String text;
  final bool mine;
  const MessageBubble({super.key, required this.text, required this.mine});

  @override
  Widget build(BuildContext context) {
    return Align(
      alignment: mine ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        margin: const EdgeInsets.symmetric(vertical: 4),
        decoration: BoxDecoration(
          color: mine ? Colors.blue.shade600 : Colors.grey.shade300,
          borderRadius: BorderRadius.circular(12),
        ),
        child: Text(
          text,
          style: TextStyle(color: mine ? Colors.white : Colors.black87),
        ),
      ),
    );
  }
}