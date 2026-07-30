import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/api/api_error.dart';
import '../../../core/widgets/app_components.dart';
import '../../../core/widgets/screen_header.dart';
import '../data/calls_repository.dart';
import '../domain/ai_analysis_job.dart';
import '../domain/call_record.dart';

class CallsPage extends ConsumerWidget {
  const CallsPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final calls = ref.watch(callsProvider);
    final jobs = ref.watch(callAnalysisJobsProvider);
    final theme = Theme.of(context);

    return RefreshIndicator(
      onRefresh: () => Future.wait([
        ref.refresh(callsProvider.future),
        ref.refresh(callAnalysisJobsProvider.future),
      ]),
      child: ListView(
        padding: kScreenPadding,
        children: [
          const StitchScreenHeader(title: 'Cagri takibi'),
          Text(
            'Mobil uygulama artik gorusme dinlemez veya kayit baslatmaz. '
            'Webde olusturulan cagri iceriklerini ve AI analiz durumlarini buradan takip edebilirsin.',
            style: theme.textTheme.bodyMedium,
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: () => context.go('/app/files'),
                  icon: const Icon(Icons.folder_open_outlined),
                  label: const Text('Icerikler'),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: () => context.go('/app/settings'),
                  icon: const Icon(Icons.settings_outlined),
                  label: const Text('Ayarlar'),
                ),
              ),
            ],
          ),
          const SizedBox(height: 20),
          calls.when(
            data: (items) {
              if (items.isEmpty) {
                return const _PageMessage(
                  message: 'Henuz webden islenmis cagri kaydi yok.',
                );
              }
              return Column(
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
              );
            },
            error: (error, stackTrace) => _PageMessage(
              message: readableApiError(error, 'Cagrilar alinamadi.'),
            ),
            loading: () => const Center(child: CircularProgressIndicator()),
          ),
        ],
      ),
    );
  }
}

AiAnalysisJob? _latestJobFor(List<AiAnalysisJob> jobs, CallRecord call) {
  final matches = jobs.where(
    (job) =>
        job.sourceType.toLowerCase() == 'conversation' &&
        job.sourceId == call.conversationId,
  );
  return matches.isEmpty ? null : matches.first;
}

class _CallsSummary extends StatelessWidget {
  const _CallsSummary({required this.calls});

  final List<CallRecord> calls;

  @override
  Widget build(BuildContext context) {
    final withTranscript =
        calls.where((call) => call.transcriptions.isNotEmpty).length;
    return AppCard(
      radius: kLargeCardRadius,
      padding: const EdgeInsets.all(16),
      child: Row(
        children: [
          Expanded(
            child: _Metric(
              icon: Icons.call_outlined,
              label: 'Cagri',
              value: calls.length.toString(),
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: _Metric(
              icon: Icons.notes_outlined,
              label: 'Transkript',
              value: withTranscript.toString(),
            ),
          ),
        ],
      ),
    );
  }
}

class _Metric extends StatelessWidget {
  const _Metric({
    required this.icon,
    required this.label,
    required this.value,
  });

  final IconData icon;
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Row(
      children: [
        TintedIcon(icon: icon, color: theme.colorScheme.primary),
        const SizedBox(width: 10),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(value, style: theme.textTheme.titleLarge),
              Text(label, style: theme.textTheme.bodySmall),
            ],
          ),
        ),
      ],
    );
  }
}

class _CallCard extends StatelessWidget {
  const _CallCard({required this.call, this.analysisJob});

  final CallRecord call;
  final AiAnalysisJob? analysisJob;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final firstTranscript =
        call.transcriptions.isEmpty ? null : call.transcriptions.first;

    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: AppCard(
        radius: kLargeCardRadius,
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                TintedIcon(
                  icon: Icons.call_outlined,
                  color: theme.colorScheme.primary,
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        call.phoneNumber?.isNotEmpty == true
                            ? call.phoneNumber!
                            : 'Web cagri kaydi',
                        style: theme.textTheme.titleMedium,
                      ),
                      const SizedBox(height: 4),
                      Text(
                        _formatDateTime(call.startedAt ?? call.createdAt),
                        style: theme.textTheme.bodySmall,
                      ),
                    ],
                  ),
                ),
                _StatusChip(status: call.status),
              ],
            ),
            if (firstTranscript != null) ...[
              const SizedBox(height: 12),
              Text('Transkript', style: theme.textTheme.labelLarge),
              const SizedBox(height: 4),
              Text(
                firstTranscript.transcriptText,
                maxLines: 5,
                overflow: TextOverflow.ellipsis,
                style: theme.textTheme.bodyMedium,
              ),
            ],
            const SizedBox(height: 12),
            _AnalysisStatus(job: analysisJob),
          ],
        ),
      ),
    );
  }
}

class _AnalysisStatus extends StatelessWidget {
  const _AnalysisStatus({this.job});

  final AiAnalysisJob? job;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    if (job == null) {
      return _InlineStatus(
        icon: Icons.hourglass_empty,
        text: 'AI analizi bekleniyor.',
        color: theme.colorScheme.onSurfaceVariant,
      );
    }
    if (job!.isPending) {
      return _InlineStatus(
        icon: Icons.auto_awesome,
        text: 'AI analizi isleniyor.',
        color: theme.colorScheme.primary,
      );
    }
    if (job!.isFailed) {
      return _InlineStatus(
        icon: Icons.error_outline,
        text: job!.errorMessage?.isNotEmpty == true
            ? readableBackendMessage(job!.errorMessage, 'AI analizi tamamlanamadi.')
            : 'AI analizi tamamlanamadi.',
        color: theme.colorScheme.error,
      );
    }
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _InlineStatus(
          icon: Icons.check_circle_outline,
          text: 'AI analizi tamamlandi.',
          color: theme.colorScheme.primary,
        ),
        if (job!.summary != null) ...[
          const SizedBox(height: 8),
          Text(
            _localizedAnalysisText(job!.summary!),
            maxLines: 4,
            overflow: TextOverflow.ellipsis,
            style: theme.textTheme.bodyMedium,
          ),
        ],
      ],
    );
  }
}

class _InlineStatus extends StatelessWidget {
  const _InlineStatus({
    required this.icon,
    required this.text,
    required this.color,
  });

  final IconData icon;
  final String text;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Icon(icon, size: 16, color: color),
        const SizedBox(width: 6),
        Expanded(
          child: Text(
            text,
            style: Theme.of(context).textTheme.bodySmall?.copyWith(color: color),
          ),
        ),
      ],
    );
  }
}

class _StatusChip extends StatelessWidget {
  const _StatusChip({required this.status});

  final String status;

  @override
  Widget build(BuildContext context) {
    return Chip(label: Text(status), visualDensity: VisualDensity.compact);
  }
}

class _PageMessage extends StatelessWidget {
  const _PageMessage({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    return AppCard(
      radius: kLargeCardRadius,
      padding: const EdgeInsets.all(16),
      child: Text(message),
    );
  }
}

String _localizedAnalysisText(String value) {
  final trimmed = value.trim();
  if (trimmed.toLowerCase().startsWith('conversation:')) {
    return 'Gorusme: ${trimmed.substring('conversation:'.length).trim()}';
  }
  return trimmed;
}

String _formatDateTime(DateTime value) {
  final local = value.toLocal();
  return '${local.day.toString().padLeft(2, '0')}.'
      '${local.month.toString().padLeft(2, '0')} '
      '${local.hour.toString().padLeft(2, '0')}:'
      '${local.minute.toString().padLeft(2, '0')}';
}
