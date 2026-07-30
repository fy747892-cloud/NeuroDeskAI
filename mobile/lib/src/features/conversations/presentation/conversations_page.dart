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

    return RefreshIndicator(
      onRefresh: () => Future.wait([
        ref.refresh(conversationsProvider.future),
        ref.refresh(callAnalysisJobsProvider.future),
      ]),
      child: ListView(
        padding: kScreenPadding,
        children: [
          const StitchScreenHeader(title: 'Gorusme takibi'),
          Text(
            'Webden kaydedilen gorusme icerikleri ve AI analiz durumlari mobilde sadece izlenir.',
            style: theme.textTheme.bodyMedium,
          ),
          const SizedBox(height: 16),
          Container(
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(kCardRadius),
              boxShadow: kCardShadow,
            ),
            child: TextField(
              controller: _searchController,
              onChanged: (value) => setState(() => _query = value),
              decoration: const InputDecoration(
                hintText: 'Gorusme veya kisi ara...',
                prefixIcon: Icon(Icons.search),
                filled: true,
                fillColor: Colors.white,
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.all(Radius.circular(kCardRadius)),
                  borderSide: BorderSide.none,
                ),
              ),
            ),
          ),
          const SizedBox(height: 20),
          SectionHeading(
            title: 'Son gorusmeler',
            trailing: _query.isNotEmpty ? 'Tumunu Gor' : null,
            onTrailingTap: () => setState(() {
              _query = '';
              _searchController.clear();
            }),
          ),
          const SizedBox(height: 10),
          conversations.when(
            data: (items) {
              final filtered = items
                  .where(
                    (conversation) => conversation.title
                        .toLowerCase()
                        .contains(_query.toLowerCase()),
                  )
                  .toList(growable: false);
              if (filtered.isEmpty) {
                return _PageMessage(
                  message: items.isEmpty
                      ? 'Backendde goruntulenecek gorusme henuz yok.'
                      : 'Aramanla eslesen gorusme yok.',
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
              message: readableApiError(error, 'Gorusmeler alinamadi.'),
            ),
            loading: () => const Center(child: CircularProgressIndicator()),
          ),
        ],
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
}

class _ConversationCard extends StatelessWidget {
  const _ConversationCard({required this.conversation, required this.job});

  final Conversation conversation;
  final AiAnalysisJob? job;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: AppCard(
        onTap: () => context.go('/app/conversations/${conversation.id}'),
        child: Row(
          children: [
            TintedIcon(
              icon: Icons.forum_outlined,
              color: theme.colorScheme.primary,
              size: 48,
            ),
            const SizedBox(width: 14),
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
            Icon(Icons.chevron_right, color: theme.colorScheme.outline),
          ],
        ),
      ),
    );
  }
}

class _JobStatusBadge extends StatelessWidget {
  const _JobStatusBadge({required this.job});

  final AiAnalysisJob? job;

  @override
  Widget build(BuildContext context) {
    final (label, color) = switch (job) {
      null => ('Analiz bekliyor', const Color(0xFF6B6F82)),
      _ when job!.isFailed => ('Analiz basarisiz', const Color(0xFFDC6465)),
      _ when job!.isPending => ('Analiz ediliyor', const Color(0xFF3525CD)),
      _ => ('Analiz edildi', const Color(0xFF15803D)),
    };

    return StatusPill(label: label.toUpperCase(), color: color, dense: true);
  }
}

class _PageMessage extends StatelessWidget {
  const _PageMessage({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    return AppCard(child: Text(message));
  }
}

String _formatDate(DateTime value) {
  final local = value.toLocal();
  return '${local.day.toString().padLeft(2, '0')}.'
      '${local.month.toString().padLeft(2, '0')} '
      '${local.hour.toString().padLeft(2, '0')}:'
      '${local.minute.toString().padLeft(2, '0')}';
}
