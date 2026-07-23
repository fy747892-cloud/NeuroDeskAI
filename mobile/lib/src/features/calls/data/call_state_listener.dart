import 'dart:async';
import 'dart:io';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:phone_state/phone_state.dart';

import 'call_recording_provider.dart';

/// Watching this provider (once, from the authenticated app shell)
/// subscribes to the device's phone-call state and drives
/// [callRecordingProvider] automatically: recording starts the moment a
/// call connects (`CALL_STARTED`) and stops/uploads the moment it ends
/// (`CALL_ENDED`) — this is the "telefon çalınca kayıt otomatik başlasın"
/// behaviour, so the user never has to open the app or tap anything for a
/// normal call.
///
/// Android only: iOS does not expose call state to third-party apps. Also,
/// some OEMs' aggressive battery/background restrictions can still kill this
/// listener if the app process itself gets fully force-stopped — the manual
/// "Başlat/Durdur" button in CallsPage stays available as a fallback for
/// exactly that case.
final callAutoRecordListenerProvider = Provider<void>((ref) {
  if (!Platform.isAndroid) {
    return;
  }

  unawaited(_primePermissions());

  PhoneStateStatus? lastStatus;
  final subscription = PhoneState.stream.listen((phoneState) {
    final status = phoneState.status;
    if (status == lastStatus) {
      return;
    }
    lastStatus = status;

    final notifier = ref.read(callRecordingProvider.notifier);
    switch (status) {
      case PhoneStateStatus.CALL_STARTED:
        final current = ref.read(callRecordingProvider);
        if (current.status == CallRecordingStatus.idle ||
            current.status == CallRecordingStatus.completed ||
            current.status == CallRecordingStatus.error) {
          notifier.startRecording(phoneNumber: phoneState.number);
        }
      case PhoneStateStatus.CALL_ENDED:
      case PhoneStateStatus.NOTHING:
        final current = ref.read(callRecordingProvider);
        if (current.status == CallRecordingStatus.recording) {
          notifier.stopAndProcess();
        }
      case PhoneStateStatus.CALL_INCOMING:
        break;
    }
  });

  ref.onDispose(subscription.cancel);
});

/// Requests the permissions the auto-record flow needs up front, so a real
/// incoming call doesn't get interrupted by a system permission dialog the
/// first time it happens. Best-effort: if the user denies any of these, the
/// manual recording button still surfaces the same request on demand.
Future<void> _primePermissions() async {
  await [
    Permission.phone,
    Permission.microphone,
    Permission.notification,
  ].request();
}
