import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/api/api_error.dart';
import '../data/conversations_repository.dart';
import '../domain/conversation.dart';

class ConversationsPage extends ConsumerWidget {
  const ConversationsPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final conversations = ref.watch(conversationsProvider);
    final theme = Theme.of(context);

    return Scaffold(
      body: RefreshIndicator(
        onRefresh: () => ref.refresh(conversationsProvider.future),
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Text('Görüşmeler', style: theme.textTheme.headlineMedium),
            const SizedBox(height: 6),
            Text(
              'Manuel notları ve çağrı transkriptlerini AI analizine hazırla.',
              style: theme.textTheme.bodyMedium,
            ),
            const SizedBox(height: 16),
            conversations.when(
              data: (items) => items.isEmpty
                  ? const _PageMessage(message: 'Henüz görüşme yok.')
                  : Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        _ConversationSummary(conversations: items),
                        const SizedBox(height: 14),
                        ...items.map(
                          (conversation) =>
                              _ConversationTile(conversation: conversation),
                        ),
                      ],
                    ),
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

  Future<void> _showCreateCallSheet(BuildContext context, WidgetRef ref) async {
    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      builder: (context) => const _CreateCallSheet(),
    );
    ref.invalidate(conversationsProvider);
  }
}

class _ConversationSummary extends StatelessWidget {
  const _ConversationSummary({required this.conversations});

  final List<Conversation> conversations;

  @override
  Widget build(BuildContext context) {
    final pendingCount = conversations.where((conversation) {
      final status = conversation.status.toLowerCase();
      return status.contains('pending') ||
          status.contains('queued') ||
          status.contains('new');
    }).length;

    return _SummaryBand(
      color: const Color(0xFF17152F),
      metrics: [
        _SummaryMetricData(
          label: 'Kayıt',
          value: conversations.length.toString(),
          icon: Icons.forum_outlined,
        ),
        _SummaryMetricData(
          label: 'Analiz bekleyen',
          value: pendingCount.toString(),
          icon: Icons.auto_awesome,
        ),
      ],
    );
  }
}

class _ConversationTile extends ConsumerStatefulWidget {
  const _ConversationTile({required this.conversation});

  final Conversation conversation;

  @override
  ConsumerState<_ConversationTile> createState() => _ConversationTileState();
}

class _ConversationTileState extends ConsumerState<_ConversationTile> {
  bool _isSubmitting = false;
  String? _errorMessage;

  @override
  Widget build(BuildContext context) {
    final conversation = widget.conversation;
    final theme = Theme.of(context);

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
                  child: const Icon(
                    Icons.record_voice_over,
                    color: Color(0xFF3525CD),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    conversation.title,
                    style: theme.textTheme.titleMedium,
                  ),
                ),
                _StatusChip(status: conversation.status),
              ],
            ),
            const SizedBox(height: 12),
            Wrap(
              spacing: 12,
              runSpacing: 6,
              children: [
                _MetaLine(
                  icon: Icons.hub_outlined,
                  text: _sourceLabel(conversation.sourceType),
                ),
                _MetaLine(
                  icon: Icons.schedule,
                  text: _formatDate(conversation.createdAt),
                ),
              ],
            ),
            if (_errorMessage != null) ...[
              const SizedBox(height: 8),
              Text(
                _errorMessage!,
                style: TextStyle(color: Theme.of(context).colorScheme.error),
              ),
            ],
            const SizedBox(height: 10),
            Align(
              alignment: Alignment.centerRight,
              child: FilledButton.icon(
                onPressed: _isSubmitting ? null : _requestAnalysis,
                icon: const Icon(Icons.auto_awesome),
                label: Text(_isSubmitting ? 'Başlatılıyor' : 'AI analiz'),
              ),
            ),
          ],
        ),
      ),
    );
  }

  String _sourceLabel(String sourceType) {
    return switch (sourceType.toLowerCase()) {
      'call' => 'Çağrı',
      'manual' => 'Manuel',
      'email' => 'E-posta',
      _ => sourceType,
    };
  }

  String _formatDate(DateTime value) {
    final local = value.toLocal();
    return '${local.day.toString().padLeft(2, '0')}.'
        '${local.month.toString().padLeft(2, '0')} '
        '${local.hour.toString().padLeft(2, '0')}:'
        '${local.minute.toString().padLeft(2, '0')}';
  }

  Future<void> _requestAnalysis() async {
    setState(() {
      _isSubmitting = true;
      _errorMessage = null;
    });
    try {
      await ref
          .read(conversationsRepositoryProvider)
          .requestAnalysis(widget.conversation.id);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('AI analiz başlatıldı.')),
        );
      }
    } catch (error) {
      setState(() {
        _errorMessage = readableApiError(error, 'AI analiz başlatılamadı.');
      });
    } finally {
      if (mounted) {
        setState(() => _isSubmitting = false);
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
      if (mounted) {
        Navigator.of(context).pop();
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

class _SummaryBand extends StatelessWidget {
  const _SummaryBand({required this.color, required this.metrics});

  final Color color;
  final List<_SummaryMetricData> metrics;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: color,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        children: [
          for (final metric in metrics) ...[
            if (metric != metrics.first) const SizedBox(width: 12),
            Expanded(child: _SummaryMetric(metric: metric)),
          ],
        ],
      ),
    );
  }
}

class _SummaryMetricData {
  const _SummaryMetricData({
    required this.label,
    required this.value,
    required this.icon,
  });

  final String label;
  final String value;
  final IconData icon;
}

class _SummaryMetric extends StatelessWidget {
  const _SummaryMetric({required this.metric});

  final _SummaryMetricData metric;

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
          child: Icon(metric.icon, color: Colors.white, size: 20),
        ),
        const SizedBox(width: 10),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                metric.value,
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                      color: Colors.white,
                      fontWeight: FontWeight.w800,
                    ),
              ),
              Text(
                metric.label,
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
        const SizedBox(width: 6),
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
      'pending' => 'Bekliyor',
      'processing' => 'Isleniyor',
      'analyzed' => 'Analizli',
      'completed' => 'Tamam',
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
