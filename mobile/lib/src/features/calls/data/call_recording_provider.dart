import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/api/api_error.dart';
import 'call_recording_service.dart';
import 'calls_repository.dart';

final callRecordingServiceProvider = Provider<CallRecordingService>(
  (ref) => CallRecordingService(),
);

enum CallRecordingStatus {
  idle,
  recording,
  uploading,
  analyzing,
  completed,
  error,
}

class CallRecordingState {
  const CallRecordingState({
    this.status = CallRecordingStatus.idle,
    this.phoneNumber,
    this.errorMessage,
    this.analysisFailed = false,
  });

  final CallRecordingStatus status;
  final String? phoneNumber;
  final String? errorMessage;
  final bool analysisFailed;

  CallRecordingState copyWith({
    CallRecordingStatus? status,
    String? phoneNumber,
    String? errorMessage,
    bool? analysisFailed,
  }) {
    return CallRecordingState(
      status: status ?? this.status,
      phoneNumber: phoneNumber ?? this.phoneNumber,
      errorMessage: errorMessage,
      analysisFailed: analysisFailed ?? this.analysisFailed,
    );
  }
}

/// Drives the record → upload → transcribe → analyze pipeline for a
/// speakerphone call. The recording itself always happens locally (the
/// [CallRecordingService] foreground service); this notifier is what turns
/// the finished audio into a Call + AI analysis job on the existing backend
/// pipeline, reusing the same `/calls/*` + `/ai/analysis/*` endpoints the
/// manual transcript-paste flow already uses.
class CallRecordingNotifier extends Notifier<CallRecordingState> {
  @override
  CallRecordingState build() => const CallRecordingState();

  bool get isBusy =>
      state.status != CallRecordingStatus.idle &&
      state.status != CallRecordingStatus.completed &&
      state.status != CallRecordingStatus.error;

  Future<void> startRecording({String? phoneNumber}) async {
    if (isBusy) return;

    state = CallRecordingState(
      status: CallRecordingStatus.recording,
      phoneNumber: phoneNumber,
    );
    try {
      await ref.read(callRecordingServiceProvider).start();
    } catch (e) {
      state = state.copyWith(
        status: CallRecordingStatus.error,
        errorMessage:
            'Kayıt başlatılamadı. Mikrofon iznini, cihaz ses ayarlarını ve aktif kayıt durumunu kontrol edin.',
      );
    }
  }

  Future<void> stopAndProcess() async {
    if (state.status != CallRecordingStatus.recording) return;

    state = state.copyWith(status: CallRecordingStatus.uploading);
    try {
      final bytes = await ref.read(callRecordingServiceProvider).stopAndRead();

      final title = state.phoneNumber?.isNotEmpty == true
          ? 'Çağrı — ${state.phoneNumber}'
          : 'Hoparlörden kaydedilen görüşme';

      final result = await ref.read(callsRepositoryProvider).createFromAudio(
            title: title,
            audioBytes: bytes,
            participantNames: const [],
            phoneNumber: state.phoneNumber,
          );

      state = state.copyWith(status: CallRecordingStatus.analyzing);
      var analysisFailed = false;
      try {
        final job = await ref
            .read(callsRepositoryProvider)
            .requestAnalysis(result.conversationId);
        analysisFailed = job.isFailed;
      } catch (_) {
        analysisFailed = false;
      }

      state = state.copyWith(
        status: CallRecordingStatus.completed,
        analysisFailed: analysisFailed,
      );
    } catch (e) {
      state = state.copyWith(
        status: CallRecordingStatus.error,
        errorMessage: readableApiError(
          e,
          'Kayıt işlenemedi. Backend bağlantısını ve AI ses çözümleme ayarlarını kontrol edin.',
        ),
      );
    }
  }

  /// Stops recording without uploading — used when the user cancels.
  Future<void> discard() async {
    try {
      await ref.read(callRecordingServiceProvider).stopAndRead();
    } catch (_) {
      // Best-effort cleanup; nothing to surface if there was no active
      // recording to stop.
    }
    reset();
  }

  void reset() {
    state = const CallRecordingState();
  }
}

final callRecordingProvider =
    NotifierProvider<CallRecordingNotifier, CallRecordingState>(
  CallRecordingNotifier.new,
);
