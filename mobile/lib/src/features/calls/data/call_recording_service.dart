import 'dart:async';
import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:flutter_foreground_task/flutter_foreground_task.dart';
import 'package:path/path.dart' as path;
import 'package:path_provider/path_provider.dart';
import 'package:record/record.dart';

const String _recordFilePathKey = 'callRecordingFilePath';
const String _hasSignalKey = 'callRecordingHasSignal';
const String _recordDirectoryName = 'call_recordings';
const String _openRecorderButtonId = 'open_call_recorder';
const String _notificationTitle = 'NeuroDesk AI';
// Bu cihazda çağrı sesini doğrudan yakalayan bir kaynak (ör. voiceCall)
// doğrulanırsa adı burada önbelleğe alınır; hiçbiri doğrulanamazsa bu
// sentinel yazılır. Amaç: doğrulama gecikmesini SADECE cihazdaki ilk
// aramada ödemek, sonraki hiçbir aramada tekrar ödememek.
const String _preferredSourceKey = 'callRecordingSourcePreference';
const String _verifiedBadValue = 'verified_bad';
const Duration _sourceVerifyWindow = Duration(milliseconds: 1200);
const Duration _sourceVerifyPollInterval = Duration(milliseconds: 200);
// AOSP çoğu cihazda üçüncü parti uygulamalara çağrı sesini kapatır, ama
// bazı OEM derlemeleri (MIUI, bazı Oppo/Vivo/Realme, eski Samsung) bu
// kaynakları hâlâ tolere edip çağrı sesine doğrudan erişim veriyor.
const List<AndroidAudioSource> _directCallAudioSources = [
  AndroidAudioSource.voiceCall,
  AndroidAudioSource.voiceDownlink,
  AndroidAudioSource.voiceUplink,
];
// Cube ACR ve benzeri uygulamalardaki gibi: kayıt sırasında canlı ses
// seviyesini izleyip hiç konuşma yakalanmadıysa kullanıcıyı arama bitmeden
// uyarıyoruz. -50dB eşiği kasıtlı olarak toleranslı: amaç normalden sessiz
// bir konuşmayı elemek değil, "hiçbir ses yakalanmıyor" (yanlış kaynak,
// hoparlör kapalı, Bluetooth'a yönlenmiş çağrı vb.) durumunu erken görmek.
const double _silenceThresholdDb = -50.0;
const int _silenceWarningDelaySeconds = 6;
// 16 kHz mono: konuşma kaydı ve Whisper girişi için yeterli, native format.
// Kaynak zaten tek mikrofonla hoparlörden alındığı için stereo/48kHz hiçbir
// kalite katkısı sağlamadan dosya boyutunu ~6 kat büyütüp sunucudaki 25MB
// limitinde kullanılabilir kayıt süresini ~2 dakikaya düşürüyordu.
const int _callSampleRate = 16000;
const int _callBitRate = 128000;

@pragma('vm:entry-point')
void startCallRecordingTask() {
  FlutterForegroundTask.setTaskHandler(_CallRecordingTaskHandler());
}

class _CallRecordingTaskHandler extends TaskHandler {
  final AudioRecorder _recorder = AudioRecorder();
  DateTime? _startedAt;
  bool _hasDetectedSignal = false;

  @override
  Future<void> onStart(DateTime timestamp, TaskStarter starter) async {
    final filePath = await FlutterForegroundTask.getData<String>(
      key: _recordFilePathKey,
    );
    if (filePath == null) return;
    _startedAt = timestamp;
    _hasDetectedSignal = false;
    await FlutterForegroundTask.saveData(key: _hasSignalKey, value: false);

    // Android telefon görüşmesi sesini doğrudan üçüncü parti uygulamalara
    // açmaz. En güvenilir yöntem, hoparlörden çıkan sesi düz mikrofonla
    // yakalamaktır; iletişim modu bazı cihazlarda karşı taraf sesini bastırır.
    await _startBestEffortSpeakerphoneRecording(filePath);
  }

  @override
  void onRepeatEvent(DateTime timestamp) {
    final startedAt = _startedAt;
    final elapsed = startedAt == null
        ? Duration.zero
        : timestamp.difference(startedAt);

    unawaited(_pollAmplitude());

    final warnSilence =
        !_hasDetectedSignal && elapsed.inSeconds >= _silenceWarningDelaySeconds;
    FlutterForegroundTask.updateService(
      notificationTitle: _notificationTitle,
      notificationText: warnSilence
          ? '⚠️ Ses algılanamıyor - hoparlörün açık ve yüksek olduğundan '
              'emin olun - ${_formatElapsed(elapsed)}'
          : 'Hoparlöre al - Kayıt açık '
              '${_formatElapsed(elapsed)} - Uygulamaya dön',
      notificationButtons: const [
        NotificationButton(id: _openRecorderButtonId, text: 'Uygulamaya dön'),
      ],
    );
  }

  Future<void> _pollAmplitude() async {
    if (_hasDetectedSignal) return;
    try {
      if (!await _recorder.isRecording()) return;
      final amplitude = await _recorder.getAmplitude();
      if (amplitude.current > _silenceThresholdDb) {
        _hasDetectedSignal = true;
        await FlutterForegroundTask.saveData(key: _hasSignalKey, value: true);
      }
    } catch (_) {
      // Seviye ölçümü yalnızca teşhis amaçlı; başarısız olursa kaydı
      // etkilememeli.
    }
  }

  @override
  void onNotificationButtonPressed(String id) {
    if (id == _openRecorderButtonId) {
      FlutterForegroundTask.launchApp('/app/calls');
    }
  }

  @override
  void onNotificationPressed() {
    FlutterForegroundTask.launchApp('/app/calls');
  }

  @override
  Future<void> onDestroy(DateTime timestamp, bool isTimeout) async {
    if (await _recorder.isRecording()) {
      await _recorder.stop();
    }
    await _recorder.dispose();
  }

  Future<void> _startBestEffortSpeakerphoneRecording(String filePath) async {
    if (await _tryDirectCallAudio(filePath)) return;

    // Guaranteed fallback: speakerphone + mic, verified on real hardware
    // (Samsung Galaxy A33) to produce non-empty, audible recordings. Accept
    // immediately on non-throw, same as before -- these don't get the
    // verification window since they're the known-good last resort and
    // delaying them further only costs recording time on the devices that
    // actually need them.
    final configs = <RecordConfig>[
      _recordConfig(AndroidAudioSource.unprocessed, speakerphone: true),
      _recordConfig(AndroidAudioSource.voiceRecognition, speakerphone: true),
      _recordConfig(AndroidAudioSource.mic, speakerphone: true),
    ];

    Object? lastError;
    for (final config in configs) {
      try {
        await _recorder.start(config, path: filePath);
        return;
      } catch (error) {
        lastError = error;
      }
    }
    throw lastError ?? Exception('Call recording could not start.');
  }

  /// Tries the direct call-audio sources (voiceCall/voiceDownlink/
  /// voiceUplink), which need no speakerphone and give clean two-way audio
  /// on the OEM builds that allow them. Returns true and leaves the
  /// recorder running on success.
  ///
  /// Cost is bounded to the device's FIRST recorded call only: once we know
  /// whether these sources work on this device, the result is cached
  /// ([_preferredSourceKey]) and every later call either starts the known-
  /// good source directly (no delay) or skips straight to the guaranteed
  /// fallback (no delay) -- never re-running the verification gauntlet.
  Future<bool> _tryDirectCallAudio(String filePath) async {
    final preference = await FlutterForegroundTask.getData<String>(
      key: _preferredSourceKey,
    );
    if (preference == _verifiedBadValue) return false;

    AndroidAudioSource? cachedSource;
    for (final source in _directCallAudioSources) {
      if (source.name == preference) {
        cachedSource = source;
        break;
      }
    }

    if (cachedSource != null) {
      try {
        await _recorder.start(
          _recordConfig(cachedSource, speakerphone: false),
          path: filePath,
        );
        debugPrint(
          'CallRecording: using cached direct source ${cachedSource.name}',
        );
        return true;
      } catch (_) {
        // Worked before, failed just now (transient) -- fall through to the
        // guaranteed chain for this call without touching the cache.
        return false;
      }
    }

    // Never tested on this device: run the verification gauntlet once and
    // cache whatever we learn, good or bad.
    for (final source in _directCallAudioSources) {
      final verified = await _tryVerifiedSource(
        _recordConfig(source, speakerphone: false),
        filePath,
      );
      if (verified) {
        await FlutterForegroundTask.saveData(
          key: _preferredSourceKey,
          value: source.name,
        );
        debugPrint('CallRecording: verified direct source ${source.name}');
        return true;
      }
    }

    await FlutterForegroundTask.saveData(
      key: _preferredSourceKey,
      value: _verifiedBadValue,
    );
    debugPrint(
      'CallRecording: no direct source verified, caching fallback-only',
    );
    return false;
  }

  /// Starts [config] and, within [_sourceVerifyWindow], polls the real
  /// signal level to confirm it actually captures audio -- "start() didn't
  /// throw" alone is not proof (see git history: some devices start these
  /// sources successfully but record silence). Discards and returns false
  /// if nothing audible showed up in time.
  Future<bool> _tryVerifiedSource(RecordConfig config, String filePath) async {
    try {
      await _recorder.start(config, path: filePath);
    } catch (_) {
      return false;
    }

    final deadline = DateTime.now().add(_sourceVerifyWindow);
    while (DateTime.now().isBefore(deadline)) {
      await Future.delayed(_sourceVerifyPollInterval);
      try {
        final amplitude = await _recorder.getAmplitude();
        if (amplitude.current > _silenceThresholdDb) {
          _hasDetectedSignal = true;
          await FlutterForegroundTask.saveData(
            key: _hasSignalKey,
            value: true,
          );
          return true;
        }
      } catch (_) {
        // Keep waiting out the window; amplitude reads can be flaky right
        // after start().
      }
    }

    try {
      await _recorder.cancel();
    } catch (_) {
      // Best-effort discard; the next start() call overwrites the same path
      // regardless.
    }
    return false;
  }

  RecordConfig _recordConfig(
    AndroidAudioSource audioSource, {
    required bool speakerphone,
  }) {
    return RecordConfig(
      encoder: AudioEncoder.wav,
      bitRate: _callBitRate,
      sampleRate: _callSampleRate,
      numChannels: 1,
      autoGain: true,
      echoCancel: false,
      noiseSuppress: false,
      androidConfig: AndroidRecordConfig(
        audioSource: audioSource,
        speakerphone: speakerphone,
        manageBluetooth: false,
        audioManagerMode: AudioManagerMode.modeNormal,
      ),
    );
  }
}

class CallRecordingService {
  bool _initialized = false;

  void _ensureInitialized() {
    if (_initialized) return;
    _initialized = true;

    FlutterForegroundTask.init(
      androidNotificationOptions: AndroidNotificationOptions(
        channelId: 'call_recording_service',
        channelName: 'Görüşme kaydı',
        channelDescription: 'Görüşme kaydı alınırken gösterilir.',
        channelImportance: NotificationChannelImportance.HIGH,
        priority: NotificationPriority.HIGH,
      ),
      iosNotificationOptions: const IOSNotificationOptions(
        showNotification: false,
      ),
      foregroundTaskOptions: ForegroundTaskOptions(
        eventAction: ForegroundTaskEventAction.repeat(1000),
        allowWakeLock: true,
      ),
    );
  }

  Future<String> start() async {
    if (!Platform.isAndroid) {
      throw Exception(
        'Görüşme kaydı yalnızca Android\'de destekleniyor: iOS üçüncü '
        'parti uygulamaların telefon görüşmesi sırasında mikrofona '
        'erişmesine izin vermiyor.',
      );
    }

    _ensureInitialized();

    if (!await AudioRecorder().hasPermission()) {
      throw Exception('Mikrofon izni verilmedi.');
    }

    if (await FlutterForegroundTask.checkNotificationPermission() !=
        NotificationPermission.granted) {
      await FlutterForegroundTask.requestNotificationPermission();
    }

    final supportDir = await getApplicationSupportDirectory();
    final recordDir = Directory(path.join(supportDir.path, _recordDirectoryName));
    await recordDir.create(recursive: true);

    final fileName = DateTime.now().toIso8601String().replaceAll(
          RegExp(r'[:.]'),
          '-',
        );
    final filePath = path.join(recordDir.path, '$fileName.wav');

    await FlutterForegroundTask.saveData(
      key: _recordFilePathKey,
      value: filePath,
    );

    final result = await FlutterForegroundTask.startService(
      serviceId: 401,
      serviceTypes: const [ForegroundServiceTypes.microphone],
      notificationTitle: _notificationTitle,
      notificationText: 'Hoparlöre al - Kayıt başlıyor - Uygulamaya dön',
      notificationButtons: const [
        NotificationButton(id: _openRecorderButtonId, text: 'Uygulamaya dön'),
      ],
      callback: startCallRecordingTask,
    );

    if (result is ServiceRequestFailure) {
      throw result.error;
    }

    return filePath;
  }

  Future<List<int>> stopAndRead() async {
    final filePath = await FlutterForegroundTask.getData<String>(
      key: _recordFilePathKey,
    );

    final result = await FlutterForegroundTask.stopService();
    if (result is ServiceRequestFailure) {
      throw result.error;
    }

    if (filePath == null) {
      throw Exception('Kayıt dosyası bulunamadı.');
    }
    final file = File(filePath);

    // MediaRecorder, servis durdurulduktan hemen sonra dosyanın trailer'ını
    // (moov atom) yazmayı bitirmemiş olabilir. Dosya boyutu iki ölçüm
    // arasında değişmeyene kadar kısa aralıklarla bekle.
    int lastSize = -1;
    for (var i = 0; i < 15; i++) {
      if (await file.exists()) {
        final size = await file.length();
        if (size > 0 && size == lastSize) break;
        lastSize = size;
      }
      await Future.delayed(const Duration(milliseconds: 200));
    }

    if (!await file.exists() || await file.length() == 0) {
      throw Exception(
        'Kayıt dosyası boş görünüyor. Hoparlörün açık olduğundan ve '
        'mikrofon izninin verildiğinden emin olup tekrar deneyin.',
      );
    }

    // Kayıt boyunca hiç ses seviyesi eşiği geçilmediyse (yanlış kaynak,
    // hoparlör kapalı, Bluetooth'a yönlenmiş çağrı vb.) dosya boş olmasa
    // bile analiz için işe yaramaz; bunu backend'e göndermeden burada
    // yakalamak, sessiz ses üzerinde Whisper halüsinasyonu üretip belirsiz
    // bir hatayla karşılaşmaktan daha nettir. Anahtar hiç yazılmadıysa
    // (beklenmedik bir durum) akışı bloke etmemek için varsayılan `true`.
    final hasSignal =
        await FlutterForegroundTask.getData<bool>(key: _hasSignalKey) ?? true;
    if (!hasSignal) {
      await file.delete();
      throw Exception(
        'Kayıtta konuşma sesi algılanamadı. Hoparlörün açık ve yüksek '
        'olduğundan, telefonun karşı tarafa yakın durduğundan emin olup '
        'tekrar deneyin.',
      );
    }

    final bytes = await file.readAsBytes();
    await file.delete();
    return bytes;
  }

  /// Live signal check for the UI while recording is in progress -- backed
  /// by the same flag the foreground task writes in [_pollAmplitude], so
  /// this reflects whether any audible speech has been detected so far in
  /// the current recording. Defaults to `true` (no warning) if the key
  /// hasn't been written yet, e.g. right at recording start.
  Future<bool> hasDetectedSignal() async {
    return await FlutterForegroundTask.getData<bool>(key: _hasSignalKey) ??
        true;
  }
}

String _formatElapsed(Duration duration) {
  final minutes = duration.inMinutes.remainder(60).toString().padLeft(2, '0');
  final seconds = duration.inSeconds.remainder(60).toString().padLeft(2, '0');
  final hours = duration.inHours;
  if (hours > 0) {
    return '${hours.toString().padLeft(2, '0')}:$minutes:$seconds';
  }
  return '$minutes:$seconds';
}
