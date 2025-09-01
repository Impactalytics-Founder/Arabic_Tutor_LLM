/// Global configuration for the Flutter client.
///
/// The WebSocket URL can be overridden at build time using the
/// `--dart-define=WS_URL=ws://...` flag.  If no override is provided
/// the default value below is used.  The backend from chunks 1 & 2
/// runs on `ws://localhost:8000/ws` when started locally.
class AppConfig {
  static const String wsUrl = String.fromEnvironment(
    'WS_URL',
    defaultValue: 'ws://localhost:8000/ws',
  );
}