import 'dart:async';

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/api/api_error.dart';
import 'call_recording_service.dart';
import 'calls_repository.dart';

const _signalWarningDelay = Duration(seconds: 6);
const _signalPollInterval = Duration(seconds: 2);

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
    this.startedAt,
    this.hasSignal = true,
  });

  final CallRecordingStatus status;
  final String? phoneNumber;
  final String? errorMessage;
  final bool analysisFailed;
  final DateTime? startedAt;
  // Whether any audible speech has been detected so far in the current
  // recording; drives the in-app "hoparlörü kontrol et" warning banner. See
  // CallRecordingService.hasDetectedSignal().
  final bool hasSignal;

  CallRecordingState copyWith({
    CallRecordingStatus? status,
    String? phoneNumber,
    String? errorMessage,
    bool? analysisFailed,
    DateTime? startedAt,
    bool? hasSignal,
  }) {
    return CallRecordingState(
      status: status ?? this.status,
      phoneNumber: phoneNumber ?? this.phoneNumber,
      errorMessage: errorMessage,
      analysisFailed: analysisFailed ?? this.analysisFailed,
      startedAt: startedAt ?? this.startedAt,
      hasSignal: hasSignal ?? this.hasSignal,
    );
  }
}

/// Drives the record -> upload -> transcribe -> analyze pipeline for a
/// speakerphone call. The recording itself always happens locally; this
/// notifier turns the finished audio into a Call + AI analysis job.
class CallRecordingNotifier extends Notifier<CallRecordingState> {
  Timer? _signalTimer;

  @override
  CallRecordingState build() {
    ref.onDispose(() => _signalTimer?.cancel());
    return const CallRecordingState();
  }

  bool get isBusy =>
      state.status != CallRecordingStatus.idle &&
      state.status != CallRecordingStatus.completed &&
      state.status != CallRecordingStatus.error;

  Future<void> startRecording({String? phoneNumber}) async {
    if (isBusy) return;

    state = CallRecordingState(
      status: CallRecordingStatus.recording,
      phoneNumber: phoneNumber,
      startedAt: DateTime.now(),
    );
    try {
      await ref.read(callRecordingServiceProvider).start();
      _startSignalPolling();
    } catch (e) {
      state = state.copyWith(
        status: CallRecordingStatus.error,
        errorMessage:
            'Kayıt başlatılamadı. Mikrofon iznini, cihaz ses ayarlarını ve aktif kayıt durumunu kontrol edin.',
      );
    }
  }

  void _startSignalPolling() {
    _signalTimer?.cancel();
    _signalTimer = Timer.periodic(_signalPollInterval, (_) async {
      if (state.status != CallRecordingStatus.recording) {
        _signalTimer?.cancel();
        return;
      }
      final startedAt = state.startedAt;
      final elapsed = startedAt == null
          ? Duration.zero
          : DateTime.now().difference(startedAt);
      if (elapsed < _signalWarningDelay) return;

      final detected =
          await ref.read(callRecordingServiceProvider).hasDetectedSignal();
      if (state.status == CallRecordingStatus.recording) {
        state = state.copyWith(hasSignal: detected);
      }
    });
  }

  Future<void> stopAndProcess() async {
    if (state.status != CallRecordingStatus.recording) return;
    _signalTimer?.cancel();

    state = state.copyWith(status: CallRecordingStatus.uploading);
    try {
      final startedAt = state.startedAt;
      final elapsed = startedAt == null
          ? Duration.zero
          : DateTime.now().difference(startedAt);
      final bytes = await ref.read(callRecordingServiceProvider).stopAndRead();
      if (elapsed.inSeconds < 4) {
        throw Exception(
          'Kayıt çok kısa. Arama başladıktan sonra hoparlörü açıp en az birkaç saniye konuşma kaydedin.',
        );
      }

      final title = state.phoneNumber?.isNotEmpty == true
          ? 'Çağrı - ${state.phoneNumber}'
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
      // Local failures (empty/too-short recording, mic permission, missing
      // file) are already specific, actionable Turkish messages thrown by
      // stopAndRead()/this method -- readableApiError only knows how to
      // translate DioException and would otherwise flatten them all into
      // the generic network-error fallback below.
      final message = e is DioException
          ? readableApiError(
              e,
              'Kayıt işlenemedi. Backend bağlantısını ve AI ses çözümleme ayarlarını kontrol edin.',
            )
          : e.toString().replaceFirst('Exception: ', '');
      state = state.copyWith(
        status: CallRecordingStatus.error,
        errorMessage: message,
      );
    }
  }

  /// Stops recording without uploading - used when the user cancels.
  Future<void> discard() async {
    _signalTimer?.cancel();
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
