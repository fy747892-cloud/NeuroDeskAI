import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:file_picker/file_picker.dart';
import 'package:go_router/go_router.dart';

import '../../../core/api/api_error.dart';
import '../../../core/widgets/app_components.dart';
import '../../../core/widgets/screen_header.dart';
import '../../ai_approvals/data/ai_approvals_repository.dart';
import '../../conversations/data/conversations_repository.dart';
import '../../files/data/files_repository.dart';
import '../data/call_recording_provider.dart';
import '../data/calls_repository.dart';

class CallsPage extends ConsumerStatefulWidget {
  const CallsPage({super.key});

  @override
  ConsumerState<CallsPage> createState() => _CallsPageState();
}

class _CallsPageState extends ConsumerState<CallsPage> {
  Timer? _pollingTimer;

  @override
  void initState() {
    super.initState();
    _pollingTimer = Timer.periodic(const Duration(seconds: 3), (_) {
      if (!mounted) return;
      final jobs = ref.read(callAnalysisJobsProvider).valueOrNull ?? const [];
      final hasActiveJob = jobs.any((job) => job.isPending);
      final rec = ref.read(callRecordingProvider);
      final hasActiveRecording = rec.status == CallRecordingStatus.uploading ||
          rec.status == CallRecordingStatus.analyzing;
      if (hasActiveJob || hasActiveRecording) {
        ref.invalidate(callsProvider);
        ref.invalidate(callAnalysisJobsProvider);
        ref.invalidate(pendingAiApprovalsProvider);
      }
    });
  }

  @override
  void dispose() {
    _pollingTimer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      body: ListView(
        padding: kScreenPadding,
        children: [
          const StitchScreenHeader(title: 'Çağrılar'),
          Text(
            'Aramaya başladığında kayıt otomatik başlar.',
            style: theme.textTheme.bodyMedium,
          ),
          const SizedBox(height: 20),
          const _RecordingControlCard(),
          const SizedBox(height: 20),
          Row(
            children: [
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: () => context.go('/app/files'),
                  icon: const Icon(Icons.upload_file_outlined),
                  label: const Text('Dosyadan analiz'),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: () => context.go('/app/conversations'),
                  icon: const Icon(Icons.forum_outlined),
                  label: const Text('Görüşmeler'),
                ),
              ),
            ],
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        tooltip: 'Çağrı metni ekle',
        onPressed: _showCreateSheet,
        child: const Icon(Icons.add_call),
      ),
    );
  }

  Future<void> _showCreateSheet() async {
    final result = await showModalBottomSheet<_CreateCallResult>(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      builder: (context) => const _CreateCallSheet(),
    );
    if (result != null) {
      ref.invalidate(callsProvider);
      ref.invalidate(callAnalysisJobsProvider);
      ref.invalidate(conversationsProvider);
      ref.invalidate(pendingAiApprovalsProvider);
      if (!mounted) return;
      _showActionSnack(
        result.analysisFailed
            ? 'Çağrı kaydedildi, AI analizi tekrar denenebilir.'
            : 'Çağrı kaydedildi ve AI analizi başlatıldı.',
        actionLabel: result.analysisFailed ? 'Çağrıya git' : 'Onay',
        route: '/app/calls',
      );
    }
  }

  void _showActionSnack(
    String message, {
    required String actionLabel,
    required String route,
  }) {
    final messenger = ScaffoldMessenger.of(context);
    messenger.hideCurrentSnackBar();
    messenger.showSnackBar(
      SnackBar(
        content: Text(message),
        duration: const Duration(seconds: 5),
        action: SnackBarAction(
          label: actionLabel,
          onPressed: () {
            messenger.hideCurrentSnackBar();
            context.go(route);
          },
        ),
      ),
    );
  }
}

class _RecordingControlCard extends ConsumerWidget {
  const _RecordingControlCard();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final rec = ref.watch(callRecordingProvider);
    final theme = Theme.of(context);

    ref.listen(callRecordingProvider, (previous, next) {
      if (next.status == CallRecordingStatus.completed &&
          previous?.status != CallRecordingStatus.completed) {
        ref.invalidate(callsProvider);
        ref.invalidate(callAnalysisJobsProvider);
        ref.invalidate(filesProvider);
        ref.invalidate(pendingAiApprovalsProvider);
        WidgetsBinding.instance.addPostFrameCallback((_) {
          if (!context.mounted) return;
          final messenger = ScaffoldMessenger.of(context);
          messenger.hideCurrentSnackBar();
          messenger.showSnackBar(
            SnackBar(
              content: Text(
                next.analysisFailed
                    ? 'Kayıt kaydedildi, AI analizi tekrar denenebilir.'
                    : 'Kayıt tamamlandı ve AI analizi başlatıldı.',
              ),
              duration: const Duration(seconds: 5),
              action: SnackBarAction(
                label: next.analysisFailed ? 'Çağrıya git' : 'Onay',
                onPressed: () {
                  messenger.hideCurrentSnackBar();
                  ref.read(callRecordingProvider.notifier).reset();
                  context.go(
                    '/app/calls',
                  );
                },
              ),
            ),
          );
        });
      }
    });

    switch (rec.status) {
      case CallRecordingStatus.idle:
        return AppCard(
          radius: kLargeCardRadius,
          padding: const EdgeInsets.symmetric(vertical: 28, horizontal: 20),
          child: Column(
            children: [
              Container(
                width: 72,
                height: 72,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: theme.colorScheme.primary.withValues(alpha: 0.1),
                ),
                child: Icon(Icons.mic_none,
                    size: 32, color: theme.colorScheme.primary),
              ),
              const SizedBox(height: 16),
              Text('Kayıt Hazır', style: theme.textTheme.titleLarge),
              const SizedBox(height: 6),
              Text(
                'Aramaya başladığında kayıt otomatik başlar',
                textAlign: TextAlign.center,
                style: theme.textTheme.bodyMedium,
              ),
              const SizedBox(height: 12),
              const StatusPill(label: 'BEKLEMEDE', color: Color(0xFF6B6F82)),
              const SizedBox(height: 20),
              SizedBox(
                width: double.infinity,
                child: FilledButton.icon(
                  onPressed: () => ref
                      .read(callRecordingProvider.notifier)
                      .startRecording(),
                  icon: const Icon(Icons.fiber_manual_record),
                  label: const Text('Kaydı Başlat'),
                ),
              ),
            ],
          ),
        );

      case CallRecordingStatus.recording:
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (!rec.hasSignal) ...[
              const _SilenceWarningBanner(),
              const SizedBox(height: 10),
            ],
            AppCard(
              radius: kLargeCardRadius,
              padding: const EdgeInsets.symmetric(vertical: 28, horizontal: 20),
              child: Column(
                children: [
                  Container(
                    width: 72,
                    height: 72,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: theme.colorScheme.primary,
                    ),
                    child: const Icon(Icons.mic, size: 32, color: Colors.white),
                  ),
                  const SizedBox(height: 16),
                  const _Waveform(),
                  const SizedBox(height: 12),
                  _ElapsedTimer(startedAt: rec.startedAt),
                  const SizedBox(height: 4),
                  Text(
                    'KAYIT DEVAM EDİYOR',
                    style: theme.textTheme.labelLarge?.copyWith(
                      color: theme.colorScheme.primary,
                      letterSpacing: 1,
                    ),
                  ),
                  const SizedBox(height: 16),
                  const StatusPill(
                    label: 'Hoparlörü açık tut',
                    color: Color(0xFF3525CD),
                    icon: Icons.volume_up_outlined,
                  ),
                  const SizedBox(height: 20),
                  Row(
                    children: [
                      Expanded(
                        child: OutlinedButton.icon(
                          onPressed: () =>
                              ref.read(callRecordingProvider.notifier).discard(),
                          icon: const Icon(Icons.close),
                          label: const Text('İptal'),
                        ),
                      ),
                      const SizedBox(width: 10),
                      Expanded(
                        child: FilledButton.icon(
                          onPressed: () => ref
                              .read(callRecordingProvider.notifier)
                              .stopAndProcess(),
                          icon: const Icon(Icons.check),
                          label: const Text('Tamamla'),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ],
        );

      case CallRecordingStatus.uploading:
        return const _ProcessingCard(step: 0);

      case CallRecordingStatus.analyzing:
        return const _ProcessingCard(step: 1);

      case CallRecordingStatus.completed:
        return AppCard(
          radius: kLargeCardRadius,
          padding: const EdgeInsets.all(20),
          child: Column(
            children: [
              Icon(
                rec.analysisFailed
                    ? Icons.error_outline
                    : Icons.check_circle,
                size: 48,
                color: rec.analysisFailed
                    ? theme.colorScheme.error
                    : const Color(0xFF15803D),
              ),
              const SizedBox(height: 12),
              Text(
                rec.analysisFailed ? 'Kayıt Tamamlandı' : 'Görüşme Kaydedildi',
                style: theme.textTheme.titleLarge,
              ),
              const SizedBox(height: 6),
              Text(
                rec.analysisFailed
                    ? 'Kayıt kaydedildi ama AI analizi başarısız oldu. '
                        'Aşağıdaki çağrı kartından tekrar deneyebilirsin.'
                    : 'Görüşme başarıyla analiz edildi ve CRM verilerine işlendi.',
                textAlign: TextAlign.center,
                style: theme.textTheme.bodyMedium,
              ),
              const SizedBox(height: 16),
              SizedBox(
                width: double.infinity,
                child: FilledButton(
                  onPressed: () {
                    ScaffoldMessenger.of(context).hideCurrentSnackBar();
                    ref.read(callRecordingProvider.notifier).reset();
                  },
                  child: const Text('Kapat'),
                ),
              ),
            ],
          ),
        );

      case CallRecordingStatus.error:
        return Card(
          child: Padding(
            padding: const EdgeInsets.all(14),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Icon(Icons.error_outline, color: theme.colorScheme.error),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Text(
                        rec.errorMessage ?? 'Kayıt işlemi başarısız oldu.',
                        style: TextStyle(color: theme.colorScheme.error),
                      ),
                    ),
                  ],
                ),
                Align(
                  alignment: Alignment.centerRight,
                  child: TextButton(
                    onPressed: () =>
                        ref.read(callRecordingProvider.notifier).reset(),
                    child: const Text('Kapat'),
                  ),
                ),
              ],
            ),
          ),
        );
    }
  }
}

/// Decorative bar waveform matching the Stitch "Ses Kaydı" overlay -- not
/// driven by real audio amplitude (the recorder doesn't expose that), just
/// an animated visual cue that a recording is in progress.
class _Waveform extends StatefulWidget {
  const _Waveform();

  @override
  State<_Waveform> createState() => _WaveformState();
}

class _WaveformState extends State<_Waveform> with SingleTickerProviderStateMixin {
  late final AnimationController _controller = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 900),
  )..repeat(reverse: true);

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    const heights = [10.0, 22.0, 14.0, 28.0, 18.0, 24.0, 12.0];
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, child) {
        return SizedBox(
          height: 28,
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              for (var i = 0; i < heights.length; i++)
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 2),
                  child: Container(
                    width: 4,
                    height: heights[i] * (0.4 + 0.6 * ((_controller.value + i / heights.length) % 1)),
                    decoration: BoxDecoration(
                      color: theme.colorScheme.primary.withValues(alpha: 0.7),
                      borderRadius: BorderRadius.circular(2),
                    ),
                  ),
                ),
            ],
          ),
        );
      },
    );
  }
}

class _SilenceWarningBanner extends StatelessWidget {
  const _SilenceWarningBanner();

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(0xFFFFF7ED),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: const Color(0xFFFDBA74)),
      ),
      child: Row(
        children: [
          const Icon(Icons.warning_amber_rounded,
              color: Color(0xFFC2410C), size: 20),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              'Sesin geldiğini duyamıyoruz, hoparlörü kontrol eder misin?',
              style: TextStyle(
                color: const Color(0xFF9A3412),
                fontWeight: FontWeight.w700,
                fontSize: Theme.of(context).textTheme.bodySmall?.fontSize,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _ElapsedTimer extends StatefulWidget {
  const _ElapsedTimer({required this.startedAt});

  final DateTime? startedAt;

  @override
  State<_ElapsedTimer> createState() => _ElapsedTimerState();
}

class _ElapsedTimerState extends State<_ElapsedTimer> {
  Timer? _ticker;

  @override
  void initState() {
    super.initState();
    _ticker = Timer.periodic(const Duration(seconds: 1), (_) {
      if (mounted) setState(() {});
    });
  }

  @override
  void dispose() {
    _ticker?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final startedAt = widget.startedAt;
    final elapsed =
        startedAt == null ? Duration.zero : DateTime.now().difference(startedAt);
    final minutes = elapsed.inMinutes.remainder(60).toString().padLeft(2, '0');
    final seconds = elapsed.inSeconds.remainder(60).toString().padLeft(2, '0');
    return Text(
      '$minutes:$seconds',
      style: Theme.of(context).textTheme.headlineMedium?.copyWith(
            color: Theme.of(context).colorScheme.primary,
            fontWeight: FontWeight.w800,
          ),
    );
  }
}

class _ProcessingCard extends StatelessWidget {
  const _ProcessingCard({required this.step});

  /// 0 = yükleniyor, 1 = metne dönüştürülüyor ve özetleniyor.
  final int step;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return AppCard(
      radius: kLargeCardRadius,
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Görüşmen işleniyor', style: theme.textTheme.titleLarge),
          const SizedBox(height: 4),
          Text(
            'Yapay zeka görüşmeyi analiz edip önemli notları çıkarıyor.',
            style: theme.textTheme.bodyMedium,
          ),
          const SizedBox(height: 16),
          _ProcessingStep(label: 'Yükleniyor', done: step > 0, active: step == 0),
          const SizedBox(height: 10),
          _ProcessingStep(
            label: 'Metne dönüştürülüyor ve özetleniyor',
            done: false,
            active: step == 1,
          ),
        ],
      ),
    );
  }
}

class _ProcessingStep extends StatelessWidget {
  const _ProcessingStep({
    required this.label,
    required this.done,
    required this.active,
  });

  final String label;
  final bool done;
  final bool active;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Row(
      children: [
        if (done)
          const Icon(Icons.check_circle, color: Color(0xFF15803D), size: 20)
        else if (active)
          SizedBox(
            width: 18,
            height: 18,
            child: CircularProgressIndicator(
              strokeWidth: 2,
              color: theme.colorScheme.primary,
            ),
          )
        else
          Icon(Icons.circle_outlined,
              size: 20, color: theme.colorScheme.outline),
        const SizedBox(width: 10),
        Text(
          label,
          style: theme.textTheme.bodyMedium?.copyWith(
            fontWeight: active ? FontWeight.w700 : FontWeight.normal,
            color: done ? const Color(0xFF15803D) : null,
          ),
        ),
      ],
    );
  }
}

class _CreateCallSheet extends ConsumerStatefulWidget {
  const _CreateCallSheet();

  @override
  ConsumerState<_CreateCallSheet> createState() => _CreateCallSheetState();
}

class _CreateCallSheetState extends ConsumerState<_CreateCallSheet> {
  final _titleController = TextEditingController();
  final _participantsController = TextEditingController();
  final _phoneController = TextEditingController();
  final _transcriptController = TextEditingController();
  String _direction = 'outbound';
  bool _isSaving = false;
  String? _errorMessage;

  @override
  void dispose() {
    _titleController.dispose();
    _participantsController.dispose();
    _phoneController.dispose();
    _transcriptController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final bottomInset = MediaQuery.viewInsetsOf(context).bottom;

    return Padding(
      padding: EdgeInsets.fromLTRB(16, 16, 16, 16 + bottomInset),
      child: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          mainAxisSize: MainAxisSize.min,
          children: [
            Text('Çağrı metni ekle',
                style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 6),
            Text(
              'Geçmiş bir görüşmenin notunu veya transkriptini yapıştır. Kayıt çağrılar listesine düşer, ardından AI analizi başlatılır.',
              style: Theme.of(context).textTheme.bodyMedium,
            ),
            const SizedBox(height: 14),
            TextField(
              controller: _titleController,
              textInputAction: TextInputAction.next,
              decoration: const InputDecoration(
                labelText: 'Başlık',
                hintText: 'Örn. Sinan Kul ile teklif görüşmesi',
                prefixIcon: Icon(Icons.title),
              ),
            ),
            const SizedBox(height: 10),
            SegmentedButton<String>(
              segments: const [
                ButtonSegment(value: 'outbound', label: Text('Giden')),
                ButtonSegment(value: 'inbound', label: Text('Gelen')),
              ],
              selected: {_direction},
              onSelectionChanged: (values) {
                setState(() => _direction = values.first);
              },
            ),
            const SizedBox(height: 10),
            TextField(
              controller: _phoneController,
              keyboardType: TextInputType.phone,
              textInputAction: TextInputAction.next,
              decoration: const InputDecoration(
                labelText: 'Telefon',
                hintText: 'İsteğe bağlı',
                prefixIcon: Icon(Icons.phone_outlined),
              ),
            ),
            const SizedBox(height: 10),
            TextField(
              controller: _participantsController,
              textInputAction: TextInputAction.next,
              decoration: const InputDecoration(
                labelText: 'Katılımcılar',
                hintText: 'Virgül ile ayır',
                prefixIcon: Icon(Icons.people_alt_outlined),
              ),
            ),
            const SizedBox(height: 10),
            TextField(
              controller: _transcriptController,
              minLines: 5,
              maxLines: 8,
              decoration: const InputDecoration(
                labelText: 'Transkript',
                hintText:
                    'Konuşulanları buraya yapıştır. Görev, randevu ve özet önerileri bu metinden çıkarılır.',
                prefixIcon: Icon(Icons.notes_outlined),
              ),
            ),
            const SizedBox(height: 10),
            OutlinedButton.icon(
              onPressed: _isSaving ? null : _importTranscriptFile,
              icon: const Icon(Icons.text_snippet_outlined),
              label: const Text('TXT transkript dosyası içe aktar'),
            ),
            if (_errorMessage != null) ...[
              const SizedBox(height: 10),
              Text(
                _errorMessage!,
                style: TextStyle(color: Theme.of(context).colorScheme.error),
              ),
            ],
            const SizedBox(height: 14),
            FilledButton.icon(
              onPressed: _isSaving ? null : _save,
              icon: _isSaving
                  ? const SizedBox.square(
                      dimension: 18,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.auto_awesome),
              label: const Text('Kaydet ve analiz et'),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _save() async {
    final title = _titleController.text.trim();
    final transcript = _transcriptController.text.trim();
    final participants = _participantsController.text
        .split(',')
        .map((name) => name.trim())
        .where((name) => name.isNotEmpty)
        .toList(growable: false);

    if (title.isEmpty || transcript.isEmpty) {
      setState(() => _errorMessage = 'Başlık ve transkript zorunlu.');
      return;
    }

    setState(() {
      _isSaving = true;
      _errorMessage = null;
    });

    try {
      final result = await ref.read(callsRepositoryProvider).createFromText(
            title: title,
            transcriptText: transcript,
            participantNames: participants,
            callDirection: _direction,
            phoneNumber: _phoneController.text,
          );
      var analysisFailed = false;
      String? errorMessage;
      try {
        final job = await ref
            .read(callsRepositoryProvider)
            .requestAnalysis(result.conversationId);
        ref.invalidate(pendingAiApprovalsProvider);
        analysisFailed = job.isFailed;
        errorMessage = job.errorMessage;
      } catch (error) {
        analysisFailed = false;
        errorMessage = readableApiError(error, 'AI analizi başlatılamadı.');
      }
      if (mounted) {
        Navigator.of(context).pop(
          _CreateCallResult(
            analysisFailed: analysisFailed,
            errorMessage: errorMessage,
          ),
        );
      }
    } catch (error) {
      setState(() {
        _errorMessage = readableApiError(error, 'Çağrı kaydedilemedi.');
      });
    } finally {
      if (mounted) {
        setState(() => _isSaving = false);
      }
    }
  }

  Future<void> _importTranscriptFile() async {
    setState(() => _errorMessage = null);
    try {
      final result = await FilePicker.platform.pickFiles(
        type: FileType.custom,
        allowedExtensions: const ['txt'],
        allowMultiple: false,
        withData: true,
      );
      final file = result?.files.single;
      final bytes = file?.bytes;
      if (file == null || bytes == null) {
        return;
      }
      final text = String.fromCharCodes(bytes).trim();
      if (text.isEmpty) {
        setState(() => _errorMessage = 'Seçilen transkript dosyası boş.');
        return;
      }
      _transcriptController.text = text;
      if (_titleController.text.trim().isEmpty) {
        final name =
            file.name.replaceAll(RegExp(r'\.txt$', caseSensitive: false), '');
        _titleController.text = name.isEmpty ? 'Görüşme transkripti' : name;
      }
    } catch (error) {
      setState(() {
        _errorMessage = 'Transkript dosyası okunamadı.';
      });
    }
  }
}

class _CreateCallResult {
  const _CreateCallResult({
    required this.analysisFailed,
    this.errorMessage,
  });

  final bool analysisFailed;
  final String? errorMessage;
}

