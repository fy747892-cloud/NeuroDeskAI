import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/api/api_error.dart';
import '../../../core/widgets/app_components.dart';
import '../../../core/widgets/screen_header.dart';
import '../../calls/data/calls_repository.dart';
import '../../calls/domain/ai_analysis_job.dart';
import '../data/conversations_repository.dart';
import '../domain/conversation.dart';

class ConversationDetailPage extends ConsumerStatefulWidget {
  const ConversationDetailPage({required this.conversationId, super.key});

  final String conversationId;

  @override
  ConsumerState<ConversationDetailPage> createState() =>
      _ConversationDetailPageState();
}

class _ConversationDetailPageState
    extends ConsumerState<ConversationDetailPage>
    with SingleTickerProviderStateMixin {
  late final TabController _tabController =
      TabController(length: 4, vsync: this);

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final detail = ref.watch(conversationDetailProvider(widget.conversationId));
    final jobs = ref.watch(callAnalysisJobsProvider).valueOrNull ?? const [];
    final job = _matchingJob(jobs, widget.conversationId);

    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(20, 16, 20, 0),
          child: StitchDetailHeader(
            title: 'Görüşme Detayı',
            onBack: () => context.go('/app/conversations'),
          ),
        ),
        Expanded(
          child: detail.when(
            data: (conversation) => Column(
              children: [
                Padding(
                  padding: const EdgeInsets.fromLTRB(20, 0, 20, 12),
                  child: _SummaryCard(conversation: conversation, job: job),
                ),
                TabBar(
                  controller: _tabController,
                  labelColor: Theme.of(context).colorScheme.primary,
                  tabs: const [
                    Tab(text: 'Özet'),
                    Tab(text: 'Görevler'),
                    Tab(text: 'Randevular'),
                    Tab(text: 'Transkript'),
                  ],
                ),
                Expanded(
                  child: TabBarView(
                    controller: _tabController,
                    children: [
                      _SummaryTab(job: job),
                      _ItemsTab(
                        titles: job?.suggestedTaskTitles ?? const [],
                        emptyMessage: 'Bu görüşmeden çıkarılan görev yok.',
                      ),
                      _ItemsTab(
                        titles: job?.suggestedAppointmentTitles ?? const [],
                        emptyMessage: 'Bu görüşmeden çıkarılan randevu yok.',
                      ),
                      _TranscriptTab(conversation: conversation),
                    ],
                  ),
                ),
              ],
            ),
            error: (error, stackTrace) => Padding(
              padding: const EdgeInsets.all(16),
              child: Text(readableApiError(error, 'Görüşme alınamadı.')),
            ),
            loading: () => const Center(child: CircularProgressIndicator()),
          ),
        ),
      ],
    );
  }

  AiAnalysisJob? _matchingJob(List<AiAnalysisJob> jobs, String conversationId) {
    final matches = jobs.where(
      (job) =>
          job.sourceType.toLowerCase() == 'conversation' &&
          job.sourceId == conversationId,
    );
    return matches.isEmpty ? null : matches.first;
  }
}

class _SummaryCard extends StatelessWidget {
  const _SummaryCard({required this.conversation, required this.job});

  final ConversationDetail conversation;
  final AiAnalysisJob? job;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final call = conversation.calls.isEmpty ? null : conversation.calls.first;

    return AppCard(
      radius: kLargeCardRadius,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              CircleAvatar(
                radius: 22,
                backgroundColor: theme.colorScheme.surfaceContainerHigh,
                child: Icon(Icons.person, color: theme.colorScheme.primary),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      conversation.participantNames.isNotEmpty
                          ? conversation.participantNames.join(', ')
                          : (call?.phoneNumber ?? conversation.title),
                      style: theme.textTheme.titleMedium,
                    ),
                    Text(
                      _formatDateTime(conversation.createdAt) +
                          (call?.durationSeconds != null
                              ? ' • ${_formatDuration(call!.durationSeconds!)}'
                              : ''),
                      style: theme.textTheme.bodySmall,
                    ),
                  ],
                ),
              ),
              StatusPill(
                label: conversation.status,
                color: theme.colorScheme.primary,
                dense: true,
              ),
            ],
          ),
          if (job?.summary != null) ...[
            const SizedBox(height: 14),
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Icon(Icons.auto_awesome, size: 18, color: theme.colorScheme.primary),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(job!.summary!, style: theme.textTheme.bodyMedium),
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }
}

class _SummaryTab extends StatelessWidget {
  const _SummaryTab({required this.job});

  final AiAnalysisJob? job;

  @override
  Widget build(BuildContext context) {
    if (job == null) {
      return const _EmptyTabMessage(
        message: 'Bu görüşme için henüz AI analizi yapılmadı.',
      );
    }
    if (job!.isPending) {
      return const _EmptyTabMessage(message: 'AI analizi işleniyor...');
    }
    if (job!.isFailed) {
      return _EmptyTabMessage(
        message: job!.errorMessage ?? 'AI analizi başarısız oldu.',
      );
    }
    if (job!.summary == null) {
      return const _EmptyTabMessage(message: 'Özet oluşturulamadı.');
    }
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [Text(job!.summary!, style: Theme.of(context).textTheme.bodyLarge)],
    );
  }
}

class _ItemsTab extends StatelessWidget {
  const _ItemsTab({required this.titles, required this.emptyMessage});

  final List<String> titles;
  final String emptyMessage;

  @override
  Widget build(BuildContext context) {
    if (titles.isEmpty) {
      return _EmptyTabMessage(message: emptyMessage);
    }
    return ListView.separated(
      padding: const EdgeInsets.all(16),
      itemCount: titles.length,
      separatorBuilder: (context, index) => const SizedBox(height: 10),
      itemBuilder: (context, index) => AppCard(
        child: Row(
          children: [
            Icon(Icons.check_box_outline_blank,
                color: Theme.of(context).colorScheme.primary),
            const SizedBox(width: 10),
            Expanded(child: Text(titles[index])),
          ],
        ),
      ),
    );
  }
}

class _TranscriptTab extends StatelessWidget {
  const _TranscriptTab({required this.conversation});

  final ConversationDetail conversation;

  @override
  Widget build(BuildContext context) {
    final transcript = conversation.calls
        .expand((call) => call.transcripts)
        .where((text) => text.trim().isNotEmpty)
        .join('\n');

    if (transcript.trim().isEmpty) {
      return const _EmptyTabMessage(message: 'Bu görüşme için transkript yok.');
    }

    final turns = _parseTranscript(transcript);
    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: turns.length,
      itemBuilder: (context, index) => _TranscriptBubble(turn: turns[index]),
    );
  }

  List<_TranscriptTurn> _parseTranscript(String text) {
    final pattern = RegExp(r'^([^:]{1,40}):\s*(.+)$');
    final turns = <_TranscriptTurn>[];
    for (final rawLine in text.split('\n')) {
      final line = rawLine.trim();
      if (line.isEmpty) continue;
      final match = pattern.firstMatch(line);
      if (match != null) {
        turns.add(_TranscriptTurn(speaker: match.group(1)!.trim(), text: match.group(2)!.trim()));
      } else if (turns.isNotEmpty) {
        final last = turns.removeLast();
        turns.add(_TranscriptTurn(speaker: last.speaker, text: '${last.text} $line'));
      } else {
        turns.add(_TranscriptTurn(speaker: '', text: line));
      }
    }
    return turns;
  }
}

class _TranscriptTurn {
  const _TranscriptTurn({required this.speaker, required this.text});

  final String speaker;
  final String text;

  bool get isAgent {
    final lower = speaker.toLowerCase();
    return lower.contains('temsilci') || lower.contains('ai') || lower.contains('neurodesk');
  }
}

class _TranscriptBubble extends StatelessWidget {
  const _TranscriptBubble({required this.turn});

  final _TranscriptTurn turn;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isAgent = turn.isAgent;

    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Column(
        crossAxisAlignment:
            isAgent ? CrossAxisAlignment.end : CrossAxisAlignment.start,
        children: [
          if (turn.speaker.isNotEmpty)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 2),
              child: Text(turn.speaker, style: theme.textTheme.bodySmall),
            ),
          Container(
            constraints: BoxConstraints(
              maxWidth: MediaQuery.sizeOf(context).width * 0.78,
            ),
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: isAgent
                  ? theme.colorScheme.primary
                  : const Color(0xFFEAE6F4),
              borderRadius: BorderRadius.only(
                topLeft: const Radius.circular(16),
                topRight: const Radius.circular(16),
                bottomLeft: Radius.circular(isAgent ? 16 : 4),
                bottomRight: Radius.circular(isAgent ? 4 : 16),
              ),
            ),
            child: Text(
              turn.text,
              style: TextStyle(
                color: isAgent ? Colors.white : theme.colorScheme.onSurface,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _EmptyTabMessage extends StatelessWidget {
  const _EmptyTabMessage({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Text(
          message,
          textAlign: TextAlign.center,
          style: Theme.of(context).textTheme.bodyMedium,
        ),
      ),
    );
  }
}

String _formatDateTime(DateTime value) {
  final local = value.toLocal();
  return '${local.day.toString().padLeft(2, '0')}.'
      '${local.month.toString().padLeft(2, '0')}.${local.year} '
      '${local.hour.toString().padLeft(2, '0')}:'
      '${local.minute.toString().padLeft(2, '0')}';
}

String _formatDuration(int seconds) {
  final minutes = seconds ~/ 60;
  final secs = seconds % 60;
  return '$minutes:${secs.toString().padLeft(2, '0')}';
}
