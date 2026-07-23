import 'dart:io';

import 'package:flutter_foreground_task/flutter_foreground_task.dart';
import 'package:path/path.dart' as path;
import 'package:path_provider/path_provider.dart';
import 'package:record/record.dart';

const String _recordFilePathKey = 'callRecordingFilePath';
const String _recordDirectoryName = 'call_recordings';
const String _openRecorderButtonId = 'open_call_recorder';
const String _notificationTitle = 'NeuroDesk AI';

@pragma('vm:entry-point')
void startCallRecordingTask() {
  FlutterForegroundTask.setTaskHandler(_CallRecordingTaskHandler());
}

class _CallRecordingTaskHandler extends TaskHandler {
  final AudioRecorder _recorder = AudioRecorder();
  DateTime? _startedAt;

  @override
  Future<void> onStart(DateTime timestamp, TaskStarter starter) async {
    final filePath = await FlutterForegroundTask.getData<String>(
      key: _recordFilePathKey,
    );
    if (filePath == null) return;
    _startedAt = timestamp;

    // Use Android's communication mode for speakerphone calls. Native cellular
    // call audio is OS-restricted, so this captures the microphone/speaker mix
    // as reliably as Android allows while the Phone app has focus.
    await _recorder.start(
      const RecordConfig(
        encoder: AudioEncoder.aacLc,
        bitRate: 256000,
        sampleRate: 48000,
        numChannels: 1,
        autoGain: true,
        echoCancel: false,
        noiseSuppress: false,
        androidConfig: AndroidRecordConfig(
          audioSource: AndroidAudioSource.voiceCommunication,
          speakerphone: true,
          audioManagerMode: AudioManagerMode.modeInCommunication,
        ),
      ),
      path: filePath,
    );
  }

  @override
  void onRepeatEvent(DateTime timestamp) {
    final startedAt = _startedAt;
    final elapsed = startedAt == null
        ? Duration.zero
        : timestamp.difference(startedAt);
    FlutterForegroundTask.updateService(
      notificationTitle: _notificationTitle,
      notificationText: 'Hoparlöre al - Kayıt açık '
          '${_formatElapsed(elapsed)} - Uygulamaya dön',
      notificationButtons: const [
        NotificationButton(id: _openRecorderButtonId, text: 'Uygulamaya dön'),
      ],
    );
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
    final filePath = path.join(recordDir.path, '$fileName.m4a');

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

    final bytes = await file.readAsBytes();
    await file.delete();
    return bytes;
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