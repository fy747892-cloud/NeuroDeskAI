import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:file_picker/file_picker.dart';

import '../../../core/api/api_error.dart';
import '../../conversations/data/conversations_repository.dart';
import '../../files/data/files_repository.dart';
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
  String? _notice;

  @override
  Widget build(BuildContext context) {
    final calls = ref.watch(callsProvider);
    final jobs = ref.watch(callAnalysisJobsProvider);
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
            Text('Ã‡aÄŸrÄ±lar', style: theme.textTheme.headlineMedium),
            const SizedBox(height: 6),
            Text(
              'Telefon Ã§alarken kayÄ±t otomatik baÅŸlar; istersen aÅŸaÄŸÄ±dan '
              'elle de baÅŸlatÄ±p durdurabilirsin.',
              style: theme.textTheme.bodyMedium,
            ),
            const SizedBox(height: 14),
            const _RecordingControlCard(),
            if (_notice != null) ...[
              const SizedBox(height: 12),
              _PageMessage(message: _notice!),
            ],
            const SizedBox(height: 16),
            calls.when(
              data: (items) => items.isEmpty
                  ? const _PageMessage(message: 'HenÃ¼z Ã§aÄŸrÄ± kaydÄ± yok.')
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
                          ),
                        ),
                      ],
                    ),
              error: (error, stackTrace) => _PageMessage(
                message: readableApiError(error, 'Ã‡aÄŸrÄ±lar alÄ±namadÄ±.'),
              ),
              loading: () => const Center(child: CircularProgressIndicator()),
            ),
          ],
        ),
      ),
      floatingActionButton: FloatingActionButton(
        tooltip: 'Ã‡aÄŸrÄ± metni ekle',
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

  Future<void> _showCreateSheet() async {
    final job = await showModalBottomSheet<AiAnalysisJob>(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      builder: (context) => const _CreateCallSheet(),
    );
    if (job != null) {
      setState(() {
        _notice = job.isFailed
            ? 'Ã‡aÄŸrÄ± kaydedildi ama AI analizi baÅŸarÄ±sÄ±z oldu: '
                '${job.errorMessage ?? 'bilinmeyen hata'}. AÅŸaÄŸÄ±dan tekrar deneyebilirsin.'
            : 'Ã‡aÄŸrÄ± kaydedildi ve AI analizi baÅŸlatÄ±ldÄ±.';
      });
      ref.invalidate(callsProvider);
      ref.invalidate(callAnalysisJobsProvider);
      ref.invalidate(conversationsProvider);
    }
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
      }
    });

    switch (rec.status) {
      case CallRecordingStatus.idle:
        return Card(
          child: ListTile(
            leading: Icon(Icons.mic_none, color: theme.colorScheme.primary),
            title: const Text('GÃ¶rÃ¼ÅŸme kaydÄ±'),
            subtitle: const Text(
              'AramayÄ± hoparlÃ¶rden yap; kayÄ±t aramayla otomatik baÅŸlamazsa '
              'buradan elle baÅŸlat.',
            ),
            trailing: FilledButton.icon(
              onPressed: () =>
                  ref.read(callRecordingProvider.notifier).startRecording(),
              icon: const Icon(Icons.fiber_manual_record),
              label: const Text('BaÅŸlat'),
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
                      'GÃ¶rÃ¼ÅŸme kaydediliyor',
                      style: theme.textTheme.titleSmall?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Text(
                  'AramayÄ± hoparlÃ¶rden yapÄ±n ki mikrofon her iki tarafÄ± da '
                  'duyabilsin. Bitince "Durdur"a basÄ±n.',
                  style: theme.textTheme.bodySmall,
                ),
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
        return const _RecordingStatusCard(message: 'KayÄ±t yÃ¼kleniyor...');

      case CallRecordingStatus.analyzing:
        return const _RecordingStatusCard(
          message: 'Ses metne Ã§evrilip AI ile analiz ediliyor...',
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
                        ? 'KayÄ±t kaydedildi ama AI analizi baÅŸarÄ±sÄ±z oldu. '
                            'AÅŸaÄŸÄ±daki Ã§aÄŸrÄ± kartÄ±ndan tekrar deneyebilirsin.'
                        : 'KayÄ±t tamamlandÄ± ve AI analizi baÅŸlatÄ±ldÄ±.',
                    style: theme.textTheme.bodyMedium,
                  ),
                ),
                TextButton(
                  onPressed: () =>
                      ref.read(callRecordingProvider.notifier).reset(),
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
                        rec.errorMessage ?? 'KayÄ±t iÅŸlemi baÅŸarÄ±sÄ±z oldu.',
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
              label: 'Ã‡aÄŸrÄ±',
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
  const _CallCard({required this.call, this.analysisJob});

  final CallRecord call;
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
                        : 'Manuel Ã§aÄŸrÄ±',
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
                'Transkript henÃ¼z yok.',
                style: theme.textTheme.bodySmall?.copyWith(
                  color: theme.colorScheme.onSurfaceVariant,
                ),
              ),
            ],
            const SizedBox(height: 10),
            _buildAnalysisStatus(context),
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
            'AI analizi henÃ¼z baÅŸlatÄ±lmadÄ±.',
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
          Text('AI analizi iÅŸleniyor...', style: theme.textTheme.bodySmall),
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
                      ? 'AI analizi baÅŸarÄ±sÄ±z: ${job.errorMessage}'
                      : 'AI analizi baÅŸarÄ±sÄ±z oldu.',
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
        _retryError = readableApiError(error, 'Tekrar deneme baÅŸarÄ±sÄ±z.');
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
            Text('Ã‡aÄŸrÄ± metni ekle',
                style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 14),
            TextField(
              controller: _titleController,
              textInputAction: TextInputAction.next,
              decoration: const InputDecoration(
                labelText: 'BaÅŸlÄ±k',
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
                prefixIcon: Icon(Icons.phone_outlined),
              ),
            ),
            const SizedBox(height: 10),
            TextField(
              controller: _participantsController,
              textInputAction: TextInputAction.next,
              decoration: const InputDecoration(
                labelText: 'Katilimcilar',
                hintText: 'Virgul ile ayir',
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
                prefixIcon: Icon(Icons.notes_outlined),
              ),
            ),
            const SizedBox(height: 10),
            OutlinedButton.icon(
              onPressed: _isSaving ? null : _importTranscriptFile,
              icon: const Icon(Icons.text_snippet_outlined),
              label: const Text('TXT transkript dosyasÄ± iÃ§e aktar'),
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
      setState(() => _errorMessage = 'BaÅŸlÄ±k ve transkript zorunlu.');
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
      final job = await ref
          .read(callsRepositoryProvider)
          .requestAnalysis(result.conversationId);
      if (mounted) {
        Navigator.of(context).pop(job);
      }
    } catch (error) {
      setState(() {
        _errorMessage = readableApiError(error, 'Ã‡aÄŸrÄ± kaydedilemedi.');
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
        setState(() => _errorMessage = 'SeÃ§ilen transkript dosyasÄ± boÅŸ.');
        return;
      }
      _transcriptController.text = text;
      if (_titleController.text.trim().isEmpty) {
        final name =
            file.name.replaceAll(RegExp(r'\.txt$', caseSensitive: false), '');
        _titleController.text = name.isEmpty ? 'GÃ¶rÃ¼ÅŸme transkripti' : name;
      }
    } catch (error) {
      setState(() {
        _errorMessage = 'Transkript dosyasÄ± okunamadÄ±.';
      });
    }
  }
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
              Text('AI analizi tamamlandÄ±.', style: theme.textTheme.bodySmall),
            ],
          ),
          if (summary != null) ...[
            const SizedBox(height: 8),
            Text(
              summary,
              maxLines: 5,
              overflow: TextOverflow.ellipsis,
              style: theme.textTheme.bodyMedium,
            ),
          ],
          if (actionCount > 0) ...[
            const SizedBox(height: 8),
            Text(
              '${job.suggestedTaskCount} gÃ¶rev, '
              '${job.suggestedAppointmentCount} randevu, '
              "${job.suggestedDealCount} fÄ±rsat Ã¶nerisi Onay Merkezi'nde.",
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
      'uploaded' => 'YÃ¼klendi',
      'processed' => 'Islendi',
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
