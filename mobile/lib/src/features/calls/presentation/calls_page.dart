import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:file_picker/file_picker.dart';
import 'package:go_router/go_router.dart';

import '../../../core/api/api_error.dart';
import '../../ai_approvals/data/ai_approvals_repository.dart';
import '../../ai_approvals/domain/ai_action_approval.dart';
import '../../ai_approvals/presentation/quick_approval_card.dart';
import '../../appointments/data/appointments_repository.dart';
import '../../conversations/data/conversations_repository.dart';
import '../../files/data/files_repository.dart';
import '../../tasks/data/tasks_repository.dart';
import '../data/call_recording_provider.dart';
import '../data/calls_repository.dart';
import '../domain/ai_analysis_job.dart';
import '../domain/call_record.dart';

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
    final calls = ref.watch(callsProvider);
    final jobs = ref.watch(callAnalysisJobsProvider);
    final approvals = ref.watch(pendingAiApprovalsProvider);
    final theme = Theme.of(context);

    return Scaffold(
      body: RefreshIndicator(
        onRefresh: () => Future.wait([
          ref.refresh(callsProvider.future),
          ref.refresh(callAnalysisJobsProvider.future),
        ]),
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Row(
              children: [
                Expanded(
                  child: Text('Çağrılar', style: theme.textTheme.headlineMedium),
                ),
                IconButton.outlined(
                  tooltip: 'Çağrıları temizle',
                  onPressed: _confirmClearCalls,
                  icon: const Icon(Icons.cleaning_services_outlined),
                ),
              ],
            ),
            const SizedBox(height: 6),
            Text(
              'Telefon çalarken kayıt otomatik başlar; istersen aşağıdan '
              'elle de başlatıp durdurabilirsin.',
              style: theme.textTheme.bodyMedium,
            ),
            const SizedBox(height: 12),
            OutlinedButton.icon(
              onPressed: () => context.go('/app/files'),
              icon: const Icon(Icons.auto_awesome),
              label: const Text('AI analiz için dosya yükle'),
            ),
            const SizedBox(height: 14),
            const _RecordingControlCard(),
            const SizedBox(height: 16),
            calls.when(
              data: (items) => items.isEmpty
                  ? const _PageMessage(message: 'Henüz çağrı kaydı yok.')
                  : Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        _CallsSummary(calls: items),
                        const SizedBox(height: 14),
                        ...items.map(
                          (call) => _CallCard(
                            call: call,
                            analysisJob: jobs.maybeWhen(
                              data: (list) => _latestJobFor(list, call),
                              orElse: () => null,
                            ),
                            approvals: approvals.maybeWhen(
                              data: (list) =>
                                  _approvalsForCall(list, call).toList(),
                              orElse: () => const [],
                            ),
                          ),
                        ),
                      ],
                    ),
              error: (error, stackTrace) => _PageMessage(
                message: readableApiError(error, 'Çağrılar alınamadı.'),
              ),
              loading: () => const Center(child: CircularProgressIndicator()),
            ),
          ],
        ),
      ),
      floatingActionButton: FloatingActionButton(
        tooltip: 'Çağrı metni ekle',
        onPressed: _showCreateSheet,
        child: const Icon(Icons.add_call),
      ),
    );
  }

  AiAnalysisJob? _latestJobFor(List<AiAnalysisJob> jobs, CallRecord call) {
    final matches = jobs.where(
      (job) =>
          job.sourceType.toLowerCase() == 'conversation' &&
          job.sourceId == call.conversationId,
    );
    return matches.isEmpty ? null : matches.first;
  }

  Iterable<AiActionApproval> _approvalsForCall(
    List<AiActionApproval> approvals,
    CallRecord call,
  ) {
    return approvals.where(
      (approval) =>
          approval.sourceType.toLowerCase() == 'conversation' &&
          approval.sourceId == call.conversationId,
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

  Future<void> _confirmClearCalls() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Çağrıları temizle'),
        content: const Text('Listedeki tüm çağrı kayıtları silinsin mi?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('Vazgeç'),
          ),
          FilledButton.icon(
            onPressed: () => Navigator.of(context).pop(true),
            icon: const Icon(Icons.delete_outline),
            label: const Text('Temizle'),
          ),
        ],
      ),
    );
    if (confirmed != true) return;
    await ref.read(callsRepositoryProvider).clearCalls();
    ref.invalidate(callsProvider);
    ref.invalidate(callAnalysisJobsProvider);
    ref.invalidate(pendingAiApprovalsProvider);
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
        return Card(
          child: Padding(
            padding: const EdgeInsets.all(14),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _ActionIcon(
                  icon: Icons.mic_none,
                  color: theme.colorScheme.primary,
                ),
                const SizedBox(width: 12),
                const Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Canlı görüşme kaydı',
                        style: TextStyle(fontWeight: FontWeight.w800),
                      ),
                      SizedBox(height: 4),
                      Text(
                        'Telefonu hoparlöre alıp kaydı başlat. En iyi sonuç '
                        'için sesi orta-yüksek seviyeye getir, telefonu '
                        'hoparlöre yakın ve sabit tut.',
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 10),
                FilledButton.icon(
                  onPressed: () =>
                      ref.read(callRecordingProvider.notifier).startRecording(),
                  icon: const Icon(Icons.fiber_manual_record),
                  label: const Text('Başlat'),
                ),
              ],
            ),
          ),
        );

      case CallRecordingStatus.recording:
        return Card(
          color: theme.colorScheme.primaryContainer,
          child: Padding(
            padding: const EdgeInsets.all(14),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Icon(Icons.fiber_manual_record,
                        color: theme.colorScheme.error, size: 16),
                    const SizedBox(width: 8),
                    Text(
                      'Görüşme kaydediliyor',
                      style: theme.textTheme.titleSmall?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Text(
                  'Aramayı hoparlörden yapın. Telefonu masaya sabit koyun, '
                  'hoparlör sesi mikrofona baksın ve ortam gürültüsünü '
                  'azaltın.',
                  style: theme.textTheme.bodySmall,
                ),
                const SizedBox(height: 10),
                const _RecordingQualityTips(),
                const SizedBox(height: 10),
                Align(
                  alignment: Alignment.centerRight,
                  child: OutlinedButton.icon(
                    onPressed: () => ref
                        .read(callRecordingProvider.notifier)
                        .stopAndProcess(),
                    icon: const Icon(Icons.stop_circle_outlined),
                    label: const Text('Durdur'),
                  ),
                ),
              ],
            ),
          ),
        );

      case CallRecordingStatus.uploading:
        return const _RecordingStatusCard(message: 'Kayıt yükleniyor...');

      case CallRecordingStatus.analyzing:
        return const _RecordingStatusCard(
          message: 'Ses metne çevrilip AI ile analiz ediliyor...',
        );

      case CallRecordingStatus.completed:
        return Card(
          child: Padding(
            padding: const EdgeInsets.all(14),
            child: Row(
              children: [
                Icon(
                  rec.analysisFailed
                      ? Icons.error_outline
                      : Icons.check_circle_outline,
                  color: rec.analysisFailed
                      ? theme.colorScheme.error
                      : theme.colorScheme.primary,
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    rec.analysisFailed
                        ? 'Kayıt kaydedildi ama AI analizi başarısız oldu. '
                            'Aşağıdaki çağrı kartından tekrar deneyebilirsin.'
                        : 'Kayıt tamamlandı ve AI analizi başlatıldı.',
                    style: theme.textTheme.bodyMedium,
                  ),
                ),
                TextButton(
                  onPressed: () {
                    ScaffoldMessenger.of(context).hideCurrentSnackBar();
                    ref.read(callRecordingProvider.notifier).reset();
                  },
                  child: const Text('Kapat'),
                ),
              ],
            ),
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

class _RecordingQualityTips extends StatelessWidget {
  const _RecordingQualityTips();

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final color = theme.colorScheme.primary;
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.08),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color.withValues(alpha: 0.16)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.graphic_eq, size: 18, color: color),
              const SizedBox(width: 6),
              Text(
                'Kayıt kalitesi',
                style: theme.textTheme.labelLarge?.copyWith(
                  color: color,
                  fontWeight: FontWeight.w800,
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),
          Text(
            'Ses düşükse hoparlör seviyesini artır. Karşı taraf çok uzaktan '
            'geliyorsa telefonu hoparlöre 20-30 cm yaklaştır.',
            style: theme.textTheme.bodySmall,
          ),
        ],
      ),
    );
  }
}

class _RecordingStatusCard extends StatelessWidget {
  const _RecordingStatusCard({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Row(
          children: [
            const SizedBox(
              width: 18,
              height: 18,
              child: CircularProgressIndicator(strokeWidth: 2),
            ),
            const SizedBox(width: 12),
            Expanded(
              child:
                  Text(message, style: Theme.of(context).textTheme.bodyMedium),
            ),
          ],
        ),
      ),
    );
  }
}

class _CallsSummary extends StatelessWidget {
  const _CallsSummary({required this.calls});

  final List<CallRecord> calls;

  @override
  Widget build(BuildContext context) {
    final withTranscript =
        calls.where((call) => call.transcriptions.isNotEmpty).length;

    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: const Color(0xFF17152F),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        children: [
          Expanded(
            child: _SummaryMetric(
              label: 'Çağrı',
              value: calls.length.toString(),
              icon: Icons.call_outlined,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: _SummaryMetric(
              label: 'Transkript',
              value: withTranscript.toString(),
              icon: Icons.notes_outlined,
            ),
          ),
        ],
      ),
    );
  }
}

class _CallCard extends ConsumerStatefulWidget {
  const _CallCard({
    required this.call,
    required this.approvals,
    this.analysisJob,
  });

  final CallRecord call;
  final List<AiActionApproval> approvals;
  final AiAnalysisJob? analysisJob;

  @override
  ConsumerState<_CallCard> createState() => _CallCardState();
}

class _CallCardState extends ConsumerState<_CallCard> {
  bool _isRetrying = false;
  String? _retryError;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final call = widget.call;
    final firstTranscript =
        call.transcriptions.isEmpty ? null : call.transcriptions.first;

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  width: 42,
                  height: 42,
                  decoration: BoxDecoration(
                    color: const Color(0x1A3525CD),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: const Icon(Icons.call, color: Color(0xFF3525CD)),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    call.phoneNumber?.isNotEmpty == true
                        ? call.phoneNumber!
                        : 'Manuel çağrı',
                    style: theme.textTheme.titleMedium,
                  ),
                ),
                _StatusChip(status: call.status),
              ],
            ),
            const SizedBox(height: 12),
            Wrap(
              spacing: 12,
              runSpacing: 6,
              children: [
                _MetaLine(
                  icon: Icons.swap_calls,
                  text: _directionLabel(call.callDirection),
                ),
                _MetaLine(
                  icon: Icons.schedule,
                  text: _formatDateTime(call.startedAt ?? call.createdAt),
                ),
                if (call.durationSeconds != null)
                  _MetaLine(
                    icon: Icons.timer_outlined,
                    text: _formatDuration(call.durationSeconds!),
                  ),
              ],
            ),
            if (firstTranscript != null) ...[
              const SizedBox(height: 10),
              Text(
                'Transkript',
                style: theme.textTheme.labelLarge?.copyWith(
                  fontWeight: FontWeight.w700,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                firstTranscript.transcriptText,
                maxLines: 8,
                overflow: TextOverflow.fade,
                style: theme.textTheme.bodyMedium,
              ),
            ] else ...[
              const SizedBox(height: 10),
              Text(
                'Transkript henüz yok.',
                style: theme.textTheme.bodySmall?.copyWith(
                  color: theme.colorScheme.onSurfaceVariant,
                ),
              ),
            ],
            const SizedBox(height: 10),
            _buildAnalysisStatus(context),
            QuickApprovalCard(
              approvals: widget.approvals,
              onChanged: () {
                ref.invalidate(tasksProvider);
                ref.invalidate(appointmentsProvider);
                ref.invalidate(callAnalysisJobsProvider);
                ref.invalidate(callsProvider);
                ref.invalidate(pendingAiApprovalsProvider);
              },
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildAnalysisStatus(BuildContext context) {
    final theme = Theme.of(context);
    final job = widget.analysisJob;

    if (job == null) {
      return Row(
        children: [
          Icon(Icons.hourglass_empty,
              size: 16, color: theme.colorScheme.onSurfaceVariant),
          const SizedBox(width: 6),
          Text(
            'AI analizi henüz başlatılmadı.',
            style: theme.textTheme.bodySmall
                ?.copyWith(color: theme.colorScheme.onSurfaceVariant),
          ),
        ],
      );
    }

    if (job.isPending) {
      return Row(
        children: [
          const SizedBox(
            width: 14,
            height: 14,
            child: CircularProgressIndicator(strokeWidth: 2),
          ),
          const SizedBox(width: 8),
          Text('AI analizi işleniyor...', style: theme.textTheme.bodySmall),
        ],
      );
    }

    if (job.isFailed) {
      return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.error_outline,
                  size: 16, color: theme.colorScheme.error),
              const SizedBox(width: 6),
              Expanded(
                child: Text(
                  job.errorMessage?.isNotEmpty == true
                      ? 'AI analizi başarısız: ${readableBackendMessage(job.errorMessage, 'bilinmeyen hata')}'
                      : 'AI analizi başarısız oldu.',
                  style: theme.textTheme.bodySmall
                      ?.copyWith(color: theme.colorScheme.error),
                ),
              ),
            ],
          ),
          if (_retryError != null) ...[
            const SizedBox(height: 4),
            Text(_retryError!,
                style: theme.textTheme.bodySmall
                    ?.copyWith(color: theme.colorScheme.error)),
          ],
          Align(
            alignment: Alignment.centerRight,
            child: TextButton.icon(
              onPressed: _isRetrying ? null : () => _retry(job),
              icon: const Icon(Icons.refresh, size: 16),
              label: Text(_isRetrying ? 'Deneniyor...' : 'Tekrar dene'),
            ),
          ),
        ],
      );
    }

    return _CompletedAnalysisStatus(job: job);
  }

  Future<void> _retry(AiAnalysisJob job) async {
    setState(() {
      _isRetrying = true;
      _retryError = null;
    });
    try {
      await ref.read(callsRepositoryProvider).retryAnalysisJob(job.id);
      ref.invalidate(callAnalysisJobsProvider);
    } catch (error) {
      setState(() {
        _retryError = readableApiError(error, 'Tekrar deneme başarısız.');
      });
    } finally {
      if (mounted) {
        setState(() => _isRetrying = false);
      }
    }
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

class _CompletedAnalysisStatus extends StatelessWidget {
  const _CompletedAnalysisStatus({required this.job});

  final AiAnalysisJob job;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final summary = job.summary;
    final actionCount = job.suggestedTaskCount +
        job.suggestedAppointmentCount +
        job.suggestedDealCount;

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: theme.colorScheme.primary.withValues(alpha: 0.08),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: theme.colorScheme.primary.withValues(alpha: 0.18),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                Icons.check_circle_outline,
                size: 16,
                color: theme.colorScheme.primary,
              ),
              const SizedBox(width: 6),
              Text('AI analizi tamamlandı.', style: theme.textTheme.bodySmall),
            ],
          ),
          if (summary != null) ...[
            const SizedBox(height: 8),
            Text(
              _localizedAnalysisText(summary),
              maxLines: 5,
              overflow: TextOverflow.ellipsis,
              style: theme.textTheme.bodyMedium,
            ),
          ],
          if (actionCount > 0) ...[
            const SizedBox(height: 8),
            Text(
              '${job.suggestedTaskCount} görev, '
              '${job.suggestedAppointmentCount} randevu, '
              "${job.suggestedDealCount} fırsat önerisi bu kartta hazır.",
              style: theme.textTheme.bodySmall?.copyWith(
                color: theme.colorScheme.onSurfaceVariant,
              ),
            ),
          ],
        ],
      ),
    );
  }
}

String _localizedAnalysisText(String value) {
  final trimmed = value.trim();
  if (trimmed.toLowerCase().startsWith('conversation:')) {
    return 'Görüşme: ${trimmed.substring('conversation:'.length).trim()}';
  }
  return trimmed;
}

class _SummaryMetric extends StatelessWidget {
  const _SummaryMetric({
    required this.label,
    required this.value,
    required this.icon,
  });

  final String label;
  final String value;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Container(
          width: 38,
          height: 38,
          decoration: BoxDecoration(
            color: Colors.white.withValues(alpha: 0.12),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Icon(icon, color: Colors.white, size: 20),
        ),
        const SizedBox(width: 10),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                value,
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                      color: Colors.white,
                      fontWeight: FontWeight.w800,
                    ),
              ),
              Text(
                label,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: Colors.white.withValues(alpha: 0.72),
                    ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _ActionIcon extends StatelessWidget {
  const _ActionIcon({required this.icon, required this.color});

  final IconData icon;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 44,
      height: 44,
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Icon(icon, color: color),
    );
  }
}

class _MetaLine extends StatelessWidget {
  const _MetaLine({required this.icon, required this.text});

  final IconData icon;
  final String text;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(
          icon,
          size: 16,
          color: Theme.of(context).colorScheme.onSurfaceVariant,
        ),
        const SizedBox(width: 5),
        Text(text, style: Theme.of(context).textTheme.bodySmall),
      ],
    );
  }
}

class _StatusChip extends StatelessWidget {
  const _StatusChip({required this.status});

  final String status;

  @override
  Widget build(BuildContext context) {
    final label = switch (status.toLowerCase()) {
      'uploaded' => 'Yüklendi',
      'processed' => 'İşlendi',
      'completed' => 'Tamamlandı',
      'failed' => 'Hata',
      _ => status,
    };

    return Chip(label: Text(label), visualDensity: VisualDensity.compact);
  }
}

class _PageMessage extends StatelessWidget {
  const _PageMessage({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Text(message),
      ),
    );
  }
}

String _directionLabel(String? value) {
  return switch (value) {
    'inbound' => 'Gelen',
    'outbound' => 'Giden',
    _ => 'Yok',
  };
}

String _formatDuration(int seconds) {
  final minutes = seconds ~/ 60;
  final remaining = seconds % 60;
  return '${minutes}d ${remaining}s';
}

String _formatDateTime(DateTime value) {
  final local = value.toLocal();
  return '${local.day.toString().padLeft(2, '0')}.'
      '${local.month.toString().padLeft(2, '0')} '
      '${local.hour.toString().padLeft(2, '0')}:'
      '${local.minute.toString().padLeft(2, '0')}';
}
