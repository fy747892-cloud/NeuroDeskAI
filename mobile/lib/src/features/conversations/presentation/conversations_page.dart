import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/api/api_error.dart';
import '../../ai_approvals/data/ai_approvals_repository.dart';
import '../../calls/data/calls_repository.dart';
import '../../calls/domain/ai_analysis_job.dart';
import '../data/conversations_repository.dart';
import '../domain/conversation.dart';

class ConversationsPage extends ConsumerStatefulWidget {
  const ConversationsPage({super.key});

  @override
  ConsumerState<ConversationsPage> createState() => _ConversationsPageState();
}

class _ConversationsPageState extends ConsumerState<ConversationsPage> {
  final _searchController = TextEditingController();
  String _query = '';

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final conversations = ref.watch(conversationsProvider);
    final jobs = ref.watch(callAnalysisJobsProvider).valueOrNull ?? const [];
    final theme = Theme.of(context);

    return Scaffold(
      body: RefreshIndicator(
        onRefresh: () => ref.refresh(conversationsProvider.future),
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Text('Görüşmeler', style: theme.textTheme.headlineMedium),
            const SizedBox(height: 12),
            TextField(
              controller: _searchController,
              onChanged: (value) => setState(() => _query = value),
              decoration: const InputDecoration(
                hintText: 'Görüşme veya kişi ara...',
                prefixIcon: Icon(Icons.search),
              ),
            ),
            const SizedBox(height: 16),
            conversations.when(
              data: (items) {
                final filtered = items
                    .where((conversation) => conversation.title
                        .toLowerCase()
                        .contains(_query.toLowerCase()))
                    .toList(growable: false);
                if (filtered.isEmpty) {
                  return _PageMessage(
                    message: items.isEmpty
                        ? 'Henüz görüşme yok.'
                        : 'Aramanla eşleşen görüşme yok.',
                  );
                }
                return Column(
                  children: [
                    for (final conversation in filtered)
                      _ConversationCard(
                        conversation: conversation,
                        job: _matchingJob(jobs, conversation.id),
                      ),
                  ],
                );
              },
              error: (error, stackTrace) => _PageMessage(
                message: readableApiError(error, 'Görüşmeler alınamadı.'),
              ),
              loading: () => const Center(child: CircularProgressIndicator()),
            ),
          ],
        ),
      ),
      floatingActionButton: FloatingActionButton(
        tooltip: 'Görüşme ekle',
        onPressed: () => _showCreateCallSheet(context, ref),
        child: const Icon(Icons.add),
      ),
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

  Future<void> _showCreateCallSheet(BuildContext context, WidgetRef ref) async {
    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      builder: (context) => const _CreateCallSheet(),
    );
    ref.invalidate(conversationsProvider);
    ref.invalidate(pendingAiApprovalsProvider);
  }
}

class _ConversationCard extends ConsumerStatefulWidget {
  const _ConversationCard({required this.conversation, required this.job});

  final Conversation conversation;
  final AiAnalysisJob? job;

  @override
  ConsumerState<_ConversationCard> createState() => _ConversationCardState();
}

class _ConversationCardState extends ConsumerState<_ConversationCard> {
  bool _isSubmitting = false;

  @override
  Widget build(BuildContext context) {
    final conversation = widget.conversation;
    final job = widget.job;
    final theme = Theme.of(context);

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      child: Material(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        child: InkWell(
          borderRadius: BorderRadius.circular(16),
          onTap: () => context.go('/app/conversations/${conversation.id}'),
          child: Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: const Color(0xFFE5E7F1)),
            ),
            child: Row(
              children: [
                Container(
                  width: 44,
                  height: 44,
                  decoration: BoxDecoration(
                    color: theme.colorScheme.primary.withValues(alpha: 0.08),
                    shape: BoxShape.circle,
                  ),
                  child: Icon(Icons.person, color: theme.colorScheme.primary),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Expanded(
                            child: Text(
                              conversation.title,
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                              style: theme.textTheme.titleMedium,
                            ),
                          ),
                          Text(
                            _formatDate(conversation.createdAt),
                            style: theme.textTheme.bodySmall,
                          ),
                        ],
                      ),
                      const SizedBox(height: 6),
                      _JobStatusBadge(job: job),
                    ],
                  ),
                ),
                const SizedBox(width: 8),
                _TrailingAction(
                  job: job,
                  isSubmitting: _isSubmitting,
                  onRequestAnalysis: _requestAnalysis,
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  String _formatDate(DateTime value) {
    final local = value.toLocal();
    return '${local.day.toString().padLeft(2, '0')}.'
        '${local.month.toString().padLeft(2, '0')} '
        '${local.hour.toString().padLeft(2, '0')}:'
        '${local.minute.toString().padLeft(2, '0')}';
  }

  Future<void> _requestAnalysis() async {
    setState(() => _isSubmitting = true);
    try {
      await ref
          .read(conversationsRepositoryProvider)
          .requestAnalysis(widget.conversation.id);
      ref.invalidate(callAnalysisJobsProvider);
      ref.invalidate(pendingAiApprovalsProvider);
      if (mounted) {
        ScaffoldMessenger.of(context).hideCurrentSnackBar();
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('AI analiz başlatıldı.')),
        );
      }
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(readableApiError(error, 'AI analiz başlatılamadı.'))),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _isSubmitting = false);
      }
    }
  }
}

class _JobStatusBadge extends StatelessWidget {
  const _JobStatusBadge({required this.job});

  final AiAnalysisJob? job;

  @override
  Widget build(BuildContext context) {
    final (label, color) = switch (job) {
      null => ('Analiz bekliyor', const Color(0xFF6B6F82)),
      _ when job!.isFailed => ('Analiz başarısız', const Color(0xFFDC6465)),
      _ when job!.isPending => ('Analiz ediliyor', const Color(0xFF3525CD)),
      _ => ('Analiz edildi', const Color(0xFF15803D)),
    };

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(999),
      ),
      child: Text(
        label,
        style: TextStyle(
          color: color,
          fontWeight: FontWeight.w700,
          fontSize: 11,
        ),
      ),
    );
  }
}

class _TrailingAction extends StatelessWidget {
  const _TrailingAction({
    required this.job,
    required this.isSubmitting,
    required this.onRequestAnalysis,
  });

  final AiAnalysisJob? job;
  final bool isSubmitting;
  final VoidCallback onRequestAnalysis;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    if (isSubmitting || job?.isPending == true) {
      return const SizedBox(
        width: 20,
        height: 20,
        child: CircularProgressIndicator(strokeWidth: 2),
      );
    }

    if (job == null || job!.isFailed) {
      return IconButton(
        tooltip: job == null ? 'AI analiz başlat' : 'Tekrar dene',
        onPressed: onRequestAnalysis,
        icon: Icon(Icons.auto_awesome, color: theme.colorScheme.primary),
      );
    }

    return Icon(Icons.chevron_right, color: theme.colorScheme.outline);
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
  final _transcriptController = TextEditingController();
  bool _isSubmitting = false;
  String? _errorMessage;

  @override
  void dispose() {
    _titleController.dispose();
    _participantsController.dispose();
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
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              'Görüşme metni ekle',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _titleController,
              textInputAction: TextInputAction.next,
              decoration: const InputDecoration(labelText: 'Başlık'),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _participantsController,
              textInputAction: TextInputAction.next,
              decoration: const InputDecoration(
                labelText: 'Katılımcılar',
                hintText: 'Virgül ile ayır',
              ),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _transcriptController,
              minLines: 5,
              maxLines: 8,
              decoration: const InputDecoration(labelText: 'Transkript'),
            ),
            if (_errorMessage != null) ...[
              const SizedBox(height: 10),
              Text(
                _errorMessage!,
                style: TextStyle(color: Theme.of(context).colorScheme.error),
              ),
            ],
            const SizedBox(height: 16),
            SizedBox(
              width: double.infinity,
              child: FilledButton.icon(
                onPressed: _isSubmitting ? null : _submit,
                icon: const Icon(Icons.save),
                label: Text(_isSubmitting ? 'Kaydediliyor' : 'Kaydet'),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _submit() async {
    final title = _titleController.text.trim();
    final transcript = _transcriptController.text.trim();
    final participants = _participantsController.text
        .split(',')
        .map((name) => name.trim())
        .where((name) => name.isNotEmpty)
        .toList(growable: false);

    if (title.isEmpty || transcript.isEmpty) {
      setState(() {
        _errorMessage = 'Başlık ve transkript zorunlu.';
      });
      return;
    }

    setState(() {
      _isSubmitting = true;
      _errorMessage = null;
    });
    try {
      final result =
          await ref.read(conversationsRepositoryProvider).createCallFromText(
                title: title,
                transcriptText: transcript,
                participantNames: participants,
              );
      await ref
          .read(conversationsRepositoryProvider)
          .requestAnalysis(result.conversationId);
      ref.invalidate(conversationsProvider);
      ref.invalidate(pendingAiApprovalsProvider);
      if (mounted) {
        Navigator.of(context).pop();
        ScaffoldMessenger.of(context).hideCurrentSnackBar();
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Görüşme kaydedildi ve analiz başladı.'),
          ),
        );
      }
    } catch (error) {
      setState(() {
        _errorMessage = readableApiError(error, 'Görüşme kaydedilemedi.');
      });
    } finally {
      if (mounted) {
        setState(() => _isSubmitting = false);
      }
    }
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
