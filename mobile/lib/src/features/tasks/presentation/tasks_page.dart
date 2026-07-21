import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../data/tasks_repository.dart';
import '../domain/task.dart';

class TasksPage extends ConsumerWidget {
  const TasksPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final tasks = ref.watch(tasksProvider);
    final theme = Theme.of(context);

    return RefreshIndicator(
      onRefresh: () => ref.refresh(tasksProvider.future),
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Text('GÃ¶revler', style: theme.textTheme.headlineMedium),
          const SizedBox(height: 6),
          Text(
            'Operasyon akÄ±ÅŸÄ±ndaki aÃ§Ä±k iÅŸleri, Ã¶ncelikleri ve teslim tarihlerini takip et.',
            style: theme.textTheme.bodyMedium,
          ),
          const SizedBox(height: 16),
          tasks.when(
            data: (items) => items.isEmpty
                ? _EmptyList(message: 'Henüz görev yok.', actionLabel: 'Onayları kontrol et', onAction: () => context.go('/app/approvals'))
                : Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      _TaskSummary(tasks: items),
                      const SizedBox(height: 14),
                      ...items.map((task) => _TaskTile(task: task)),
                    ],
                  ),
            error: (error, stackTrace) =>
                const _EmptyList(message: 'GÃ¶revler alÄ±namadÄ±.'),
            loading: () => const Center(child: CircularProgressIndicator()),
          ),
        ],
      ),
    );
  }
}

class _TaskSummary extends StatelessWidget {
  const _TaskSummary({required this.tasks});

  final List<Task> tasks;

  @override
  Widget build(BuildContext context) {
    final openCount = tasks.where((task) => task.status != 'completed').length;
    final urgentCount = tasks.where((task) {
      final priority = task.priority.toLowerCase();
      return priority == 'high' || priority == 'urgent';
    }).length;

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
              label: 'AÃ§Ä±k gÃ¶rev',
              value: openCount.toString(),
              icon: Icons.pending_actions,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: _SummaryMetric(
              label: 'YÃ¼ksek Ã¶ncelik',
              value: urgentCount.toString(),
              icon: Icons.priority_high,
            ),
          ),
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

class _TaskTile extends ConsumerWidget {
  const _TaskTile({required this.task});

  final Task task;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final isCompleted = task.status == 'completed';

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
                _PriorityDot(priority: task.priority),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    task.title,
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                          decoration: isCompleted
                              ? TextDecoration.lineThrough
                              : TextDecoration.none,
                        ),
                  ),
                ),
                _StatusChip(status: task.status),
              ],
            ),
            if (task.description != null && task.description!.isNotEmpty) ...[
              const SizedBox(height: 8),
              Text(task.description!,
                  style: Theme.of(context).textTheme.bodyMedium),
            ],
            const SizedBox(height: 12),
            Row(
              children: [
                Icon(
                  Icons.schedule,
                  size: 16,
                  color: Theme.of(context).colorScheme.onSurfaceVariant,
                ),
                const SizedBox(width: 6),
                Expanded(
                  child: Text(
                    task.dueAt == null
                        ? 'Teslim tarihi yok'
                        : 'Teslim: ${_formatDate(task.dueAt!)}',
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                ),
                Text(
                  _priorityLabel(task.priority),
                  style: Theme.of(context).textTheme.labelMedium,
                ),
                if (!isCompleted) ...[
                  const SizedBox(width: 8),
                  IconButton.filled(
                    tooltip: 'Tamamla',
                    icon: const Icon(Icons.check),
                    onPressed: () async {
                      await ref
                          .read(tasksRepositoryProvider)
                          .completeTask(task.id);
                      ref.invalidate(tasksProvider);
                    },
                  ),
                ],
              ],
            ),
          ],
        ),
      ),
    );
  }

  String _formatDate(DateTime value) {
    return '${value.day.toString().padLeft(2, '0')}.'
        '${value.month.toString().padLeft(2, '0')} '
        '${value.hour.toString().padLeft(2, '0')}:'
        '${value.minute.toString().padLeft(2, '0')}';
  }

  String _priorityLabel(String priority) {
    return switch (priority.toLowerCase()) {
      'urgent' => 'Acil',
      'high' => 'YÃ¼ksek',
      'medium' => 'Orta',
      'low' => 'DÃ¼ÅŸÃ¼k',
      _ => priority,
    };
  }
}

class _PriorityDot extends StatelessWidget {
  const _PriorityDot({required this.priority});

  final String priority;

  @override
  Widget build(BuildContext context) {
    final color = switch (priority.toLowerCase()) {
      'urgent' => const Color(0xFFFF6B6B),
      'high' => const Color(0xFFFF9F1C),
      'medium' => const Color(0xFF3525CD),
      _ => const Color(0xFF2EC4B6),
    };

    return Container(
      width: 12,
      height: 12,
      margin: const EdgeInsets.only(top: 4),
      decoration: BoxDecoration(color: color, shape: BoxShape.circle),
    );
  }
}

class _StatusChip extends StatelessWidget {
  const _StatusChip({required this.status});

  final String status;

  @override
  Widget build(BuildContext context) {
    final isCompleted = status == 'completed';

    return Chip(
      avatar: Icon(
        isCompleted ? Icons.check_circle : Icons.radio_button_unchecked,
        size: 16,
      ),
      label: Text(isCompleted ? 'Tamam' : 'AÃ§Ä±k'),
      visualDensity: VisualDensity.compact,
    );
  }
}

class _EmptyList extends StatelessWidget {
  const _EmptyList({required this.message, this.actionLabel, this.onAction});

  final String message;
  final String? actionLabel;
  final VoidCallback? onAction;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(message),
          if (actionLabel != null && onAction != null) ...[
            const SizedBox(height: 10),
            FilledButton.icon(onPressed: onAction, icon: const Icon(Icons.verified_outlined), label: Text(actionLabel!)),
          ],
        ]),
      ),
    );
  }
}
