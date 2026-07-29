import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/api/api_error.dart';
import '../data/tasks_repository.dart';
import '../domain/task.dart';

enum _TaskFilter { today, week, all }

class TasksPage extends ConsumerStatefulWidget {
  const TasksPage({super.key});

  @override
  ConsumerState<TasksPage> createState() => _TasksPageState();
}

class _TasksPageState extends ConsumerState<TasksPage> {
  _TaskFilter _filter = _TaskFilter.today;

  @override
  Widget build(BuildContext context) {
    final tasks = ref.watch(tasksProvider);
    final theme = Theme.of(context);

    return Scaffold(
      body: RefreshIndicator(
        onRefresh: () => ref.refresh(tasksProvider.future),
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Row(
              children: [
                Expanded(
                  child: Text('Görevler', style: theme.textTheme.headlineMedium),
                ),
                IconButton.outlined(
                  tooltip: 'Görevleri temizle',
                  onPressed: () => _confirmClear(context, ref),
                  icon: const Icon(Icons.cleaning_services_outlined),
                ),
              ],
            ),
            const SizedBox(height: 16),
            SegmentedButton<_TaskFilter>(
              segments: const [
                ButtonSegment(value: _TaskFilter.today, label: Text('Bugün')),
                ButtonSegment(value: _TaskFilter.week, label: Text('Bu Hafta')),
                ButtonSegment(value: _TaskFilter.all, label: Text('Tümü')),
              ],
              selected: {_filter},
              onSelectionChanged: (selection) =>
                  setState(() => _filter = selection.first),
            ),
            const SizedBox(height: 16),
            tasks.when(
              data: (items) => items.isEmpty
                  ? const _EmptyList(message: 'Henüz görev yok.')
                  : _TaskLists(tasks: items, filter: _filter),
              error: (error, stackTrace) =>
                  const _EmptyList(message: 'Görevler alınamadı.'),
              loading: () => const Center(child: CircularProgressIndicator()),
            ),
          ],
        ),
      ),
      floatingActionButton: FloatingActionButton(
        tooltip: 'Görev ekle',
        onPressed: () => _showCreateTaskSheet(context, ref),
        child: const Icon(Icons.add),
      ),
    );
  }

  Future<void> _confirmClear(BuildContext context, WidgetRef ref) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Görevleri temizle'),
        content: const Text('Listedeki tüm görevler silinsin mi?'),
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
    await ref.read(tasksRepositoryProvider).clearTasks();
    ref.invalidate(tasksProvider);
  }

  Future<void> _showCreateTaskSheet(BuildContext context, WidgetRef ref) async {
    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      builder: (context) => const _CreateTaskSheet(),
    );
    ref.invalidate(tasksProvider);
  }
}

class _TaskLists extends ConsumerWidget {
  const _TaskLists({required this.tasks, required this.filter});

  final List<Task> tasks;
  final _TaskFilter filter;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    bool matches(Task task) {
      if (filter == _TaskFilter.all) return true;
      final due = task.dueAt?.toLocal();
      if (due == null) return false;
      final now = DateTime.now();
      final today = DateTime(now.year, now.month, now.day);
      final dueDay = DateTime(due.year, due.month, due.day);
      if (filter == _TaskFilter.today) return dueDay == today;
      final weekEnd = today.add(const Duration(days: 7));
      return !dueDay.isBefore(today) && dueDay.isBefore(weekEnd);
    }

    final open = tasks
        .where((task) => task.status != 'completed' && matches(task))
        .toList(growable: false);
    final completed = tasks
        .where((task) => task.status == 'completed' && matches(task))
        .toList(growable: false);

    if (open.isEmpty && completed.isEmpty) {
      return const _EmptyList(message: 'Bu aralıkta görev yok.');
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text('Bekleyen Görevler',
                style: Theme.of(context).textTheme.titleMedium),
            _CountPill(count: open.length),
          ],
        ),
        const SizedBox(height: 10),
        if (open.isEmpty)
          const _EmptyList(message: 'Bekleyen görev yok.')
        else
          ...open.map((task) => _TaskTile(task: task)),
        if (completed.isNotEmpty) ...[
          const SizedBox(height: 18),
          Text('Tamamlananlar',
              style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 10),
          ...completed.map((task) => _TaskTile(task: task)),
        ],
      ],
    );
  }
}

class _CountPill extends StatelessWidget {
  const _CountPill({required this.count});

  final int count;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.primary.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(999),
      ),
      child: Text(
        '$count',
        style: TextStyle(
          color: Theme.of(context).colorScheme.primary,
          fontWeight: FontWeight.w800,
        ),
      ),
    );
  }
}

class _TaskTile extends ConsumerWidget {
  const _TaskTile({required this.task});

  final Task task;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final isCompleted = task.status == 'completed';
    final theme = Theme.of(context);

    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      decoration: BoxDecoration(
        color: isCompleted ? const Color(0xFFF0EEFB) : Colors.white,
        borderRadius: BorderRadius.circular(14),
        border: Border(
          left: BorderSide(color: _priorityColor(task.priority), width: 4),
          top: const BorderSide(color: Color(0xFFE5E7F1)),
          right: const BorderSide(color: Color(0xFFE5E7F1)),
          bottom: const BorderSide(color: Color(0xFFE5E7F1)),
        ),
      ),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Row(
          children: [
            GestureDetector(
              onTap: isCompleted
                  ? null
                  : () async {
                      await ref
                          .read(tasksRepositoryProvider)
                          .completeTask(task.id);
                      ref.invalidate(tasksProvider);
                    },
              child: Container(
                width: 24,
                height: 24,
                decoration: BoxDecoration(
                  color: isCompleted ? theme.colorScheme.primary : null,
                  border: Border.all(
                    color: isCompleted
                        ? theme.colorScheme.primary
                        : const Color(0xFFC7C4D8),
                    width: 2,
                  ),
                  borderRadius: BorderRadius.circular(6),
                ),
                child: isCompleted
                    ? const Icon(Icons.check, size: 16, color: Colors.white)
                    : null,
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    task.title,
                    style: theme.textTheme.bodyLarge?.copyWith(
                      decoration:
                          isCompleted ? TextDecoration.lineThrough : null,
                      color: isCompleted ? theme.colorScheme.outline : null,
                    ),
                  ),
                  Text(
                    isCompleted
                        ? 'Tamamlandı'
                        : (task.dueAt == null
                            ? _priorityLabel(task.priority)
                            : '${_formatDate(task.dueAt!)} • ${_priorityLabel(task.priority)}'),
                    style: theme.textTheme.bodySmall,
                  ),
                ],
              ),
            ),
            PopupMenuButton<String>(
              onSelected: (value) async {
                if (value == 'delete') {
                  await ref.read(tasksRepositoryProvider).deleteTask(task.id);
                  ref.invalidate(tasksProvider);
                }
              },
              itemBuilder: (context) => const [
                PopupMenuItem(value: 'delete', child: Text('Sil')),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Color _priorityColor(String priority) {
    return switch (priority.toLowerCase()) {
      'urgent' => const Color(0xFFFF6B6B),
      'high' => const Color(0xFFFF9F1C),
      'medium' => const Color(0xFF3525CD),
      _ => const Color(0xFF2EC4B6),
    };
  }

  String _priorityLabel(String priority) {
    return switch (priority.toLowerCase()) {
      'urgent' => 'Acil',
      'high' => 'Yüksek',
      'medium' => 'Orta',
      'low' => 'Düşük',
      _ => priority,
    };
  }

  String _formatDate(DateTime value) {
    final local = value.toLocal();
    return '${local.day.toString().padLeft(2, '0')}.'
        '${local.month.toString().padLeft(2, '0')} '
        '${local.hour.toString().padLeft(2, '0')}:'
        '${local.minute.toString().padLeft(2, '0')}';
  }
}

class _CreateTaskSheet extends ConsumerStatefulWidget {
  const _CreateTaskSheet();

  @override
  ConsumerState<_CreateTaskSheet> createState() => _CreateTaskSheetState();
}

class _CreateTaskSheetState extends ConsumerState<_CreateTaskSheet> {
  final _titleController = TextEditingController();
  String _priority = 'medium';
  DateTime? _dueAt;
  bool _isSubmitting = false;
  String? _errorMessage;

  @override
  void dispose() {
    _titleController.dispose();
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
            Text('Görev ekle', style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 16),
            TextField(
              controller: _titleController,
              decoration: const InputDecoration(labelText: 'Başlık'),
            ),
            const SizedBox(height: 12),
            DropdownButtonFormField<String>(
              initialValue: _priority,
              decoration: const InputDecoration(labelText: 'Öncelik'),
              items: const [
                DropdownMenuItem(value: 'low', child: Text('Düşük')),
                DropdownMenuItem(value: 'medium', child: Text('Orta')),
                DropdownMenuItem(value: 'high', child: Text('Yüksek')),
                DropdownMenuItem(value: 'urgent', child: Text('Acil')),
              ],
              onChanged: (value) =>
                  setState(() => _priority = value ?? 'medium'),
            ),
            const SizedBox(height: 12),
            OutlinedButton.icon(
              onPressed: _pickDueDate,
              icon: const Icon(Icons.calendar_today_outlined),
              label: Text(
                _dueAt == null ? 'Teslim tarihi seç (opsiyonel)' : _formatDueAt(_dueAt!),
              ),
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

  Future<void> _pickDueDate() async {
    final date = await showDatePicker(
      context: context,
      initialDate: DateTime.now(),
      firstDate: DateTime.now().subtract(const Duration(days: 1)),
      lastDate: DateTime.now().add(const Duration(days: 365)),
    );
    if (date == null || !mounted) return;
    final time = await showTimePicker(
      context: context,
      initialTime: TimeOfDay.now(),
    );
    if (!mounted) return;
    setState(() {
      _dueAt = DateTime(
        date.year,
        date.month,
        date.day,
        time?.hour ?? 9,
        time?.minute ?? 0,
      );
    });
  }

  String _formatDueAt(DateTime value) {
    return '${value.day.toString().padLeft(2, '0')}.'
        '${value.month.toString().padLeft(2, '0')} '
        '${value.hour.toString().padLeft(2, '0')}:'
        '${value.minute.toString().padLeft(2, '0')}';
  }

  Future<void> _submit() async {
    final title = _titleController.text.trim();
    if (title.isEmpty) {
      setState(() => _errorMessage = 'Başlık zorunlu.');
      return;
    }

    setState(() {
      _isSubmitting = true;
      _errorMessage = null;
    });
    try {
      await ref.read(tasksRepositoryProvider).createTask(
            title: title,
            priority: _priority,
            dueAt: _dueAt,
          );
      if (mounted) Navigator.of(context).pop();
    } catch (error) {
      setState(() {
        _errorMessage = readableApiError(error, 'Görev eklenemedi.');
      });
    } finally {
      if (mounted) {
        setState(() => _isSubmitting = false);
      }
    }
  }
}

class _EmptyList extends StatelessWidget {
  const _EmptyList({required this.message});

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
