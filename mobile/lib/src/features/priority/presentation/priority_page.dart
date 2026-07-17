import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/api/api_error.dart';
import '../data/priority_repository.dart';
import '../domain/priority_queue.dart';

class PriorityPage extends ConsumerStatefulWidget {
  const PriorityPage({super.key});

  @override
  ConsumerState<PriorityPage> createState() => _PriorityPageState();
}

class _PriorityPageState extends ConsumerState<PriorityPage> {
  int _limit = 25;

  @override
  Widget build(BuildContext context) {
    final queue = ref.watch(priorityQueueProvider(_limit));
    final theme = Theme.of(context);

    return RefreshIndicator(
      onRefresh: () => ref.refresh(priorityQueueProvider(_limit).future),
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Öncelik', style: theme.textTheme.headlineMedium),
                    const SizedBox(height: 6),
                    Text(
                      'Görev ve randevuları skorlayıp sıraya al.',
                      style: theme.textTheme.bodyMedium,
                    ),
                  ],
                ),
              ),
              PopupMenuButton<int>(
                tooltip: 'Limit',
                icon: const Icon(Icons.tune),
                onSelected: (value) => setState(() => _limit = value),
                itemBuilder: (context) => const [
                  PopupMenuItem(value: 10, child: Text('10 kayıt')),
                  PopupMenuItem(value: 25, child: Text('25 kayıt')),
                  PopupMenuItem(value: 50, child: Text('50 kayıt')),
                ],
              ),
            ],
          ),
          const SizedBox(height: 16),
          queue.when(
            data: (data) => data.items.isEmpty
                ? const _PageMessage(message: 'Önceliklendirilecek iş yok.')
                : Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      _PrioritySummary(queue: data),
                      const SizedBox(height: 14),
                      ...data.items.map((item) => _PriorityCard(item: item)),
                    ],
                  ),
            error: (error, stackTrace) => _PageMessage(
              message: readableApiError(error, 'Öncelik kuyruğu alınamadı.'),
            ),
            loading: () => const Center(child: CircularProgressIndicator()),
          ),
        ],
      ),
    );
  }
}

class _PrioritySummary extends StatelessWidget {
  const _PrioritySummary({required this.queue});

  final PriorityQueue queue;

  @override
  Widget build(BuildContext context) {
    final urgentCount = queue.items.where((item) => item.score >= 70).length;
    final highCount =
        queue.items.where((item) => item.priority == 'high').length;

    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: const Color(0xFF3525CD),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        children: [
          Row(
            children: [
              Expanded(
                child: _SummaryMetric(
                  label: 'Toplam',
                  value: queue.items.length.toString(),
                  icon: Icons.format_list_numbered,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: _SummaryMetric(
                  label: 'Acil/Yüksek',
                  value: '${urgentCount + highCount}',
                  icon: Icons.priority_high,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          _MetaLine(
            icon: Icons.schedule,
            text: 'Uretim: ${_formatDateTime(queue.generatedAt)}',
            color: Colors.white.withValues(alpha: 0.8),
          ),
        ],
      ),
    );
  }
}

class _PriorityCard extends StatelessWidget {
  const _PriorityCard({required this.item});

  final PriorityItem item;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final scoreColor = _scoreColor(item.score);

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _ScoreBadge(score: item.score, color: scoreColor),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Expanded(
                        child: Text(item.title,
                            style: theme.textTheme.titleMedium),
                      ),
                      Chip(
                        label: Text(priorityLabel(item.priority)),
                        visualDensity: VisualDensity.compact,
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Wrap(
                    spacing: 8,
                    runSpacing: 6,
                    children: [
                      _TinyChip(
                        icon: item.itemType == 'task'
                            ? Icons.checklist
                            : Icons.event,
                        label: priorityItemTypeLabel(item.itemType),
                      ),
                      _TinyChip(icon: Icons.flag_outlined, label: item.status),
                      if (item.dueAt != null)
                        _TinyChip(
                          icon: Icons.schedule,
                          label: _formatDateTime(item.dueAt!),
                        ),
                    ],
                  ),
                  if (item.factors.isNotEmpty) ...[
                    const SizedBox(height: 10),
                    Wrap(
                      spacing: 6,
                      runSpacing: 6,
                      children: [
                        for (final factor in item.factors.take(4))
                          Chip(
                            label: Text(_factorLabel(factor)),
                            visualDensity: VisualDensity.compact,
                          ),
                      ],
                    ),
                  ],
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _ScoreBadge extends StatelessWidget {
  const _ScoreBadge({required this.score, required this.color});

  final int score;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 54,
      height: 54,
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color.withValues(alpha: 0.3)),
      ),
      child: Center(
        child: Text(
          score.toString(),
          style: Theme.of(context).textTheme.titleLarge?.copyWith(
                color: color,
                fontWeight: FontWeight.w900,
              ),
        ),
      ),
    );
  }
}

class _TinyChip extends StatelessWidget {
  const _TinyChip({required this.icon, required this.label});

  final IconData icon;
  final String label;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon,
            size: 15, color: Theme.of(context).colorScheme.onSurfaceVariant),
        const SizedBox(width: 4),
        Text(label, style: Theme.of(context).textTheme.bodySmall),
      ],
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
  const _MetaLine({required this.icon, required this.text, this.color});

  final IconData icon;
  final String text;
  final Color? color;

  @override
  Widget build(BuildContext context) {
    final resolvedColor =
        color ?? Theme.of(context).colorScheme.onSurfaceVariant;
    return Row(
      children: [
        Icon(icon, size: 16, color: resolvedColor),
        const SizedBox(width: 6),
        Expanded(
          child: Text(
            text,
            style: Theme.of(context)
                .textTheme
                .bodySmall
                ?.copyWith(color: resolvedColor),
          ),
        ),
      ],
    );
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

Color _scoreColor(int score) {
  if (score >= 70) {
    return const Color(0xFFDC2626);
  }
  if (score >= 45) {
    return const Color(0xFFD97706);
  }
  if (score >= 25) {
    return const Color(0xFF3525CD);
  }
  return const Color(0xFF64748B);
}

String _factorLabel(PriorityFactor factor) {
  return switch (factor.key) {
    'explicit_priority' => 'Öncelik +${factor.weight}',
    'status' => 'Durum +${factor.weight}',
    'overdue' => 'Gecikti +${factor.weight}',
    'due_soon' => 'Yaklaşan +${factor.weight}',
    'upcoming' => '3 gün +${factor.weight}',
    'planned' => 'Planlı +${factor.weight}',
    'contact_linked' => 'Kişi +${factor.weight}',
    'urgent_language' => 'Acil dil +${factor.weight}',
    _ => '+${factor.weight}',
  };
}

String _formatDateTime(DateTime value) {
  final local = value.toLocal();
  return '${local.day.toString().padLeft(2, '0')}.'
      '${local.month.toString().padLeft(2, '0')} '
      '${local.hour.toString().padLeft(2, '0')}:'
      '${local.minute.toString().padLeft(2, '0')}';
}
