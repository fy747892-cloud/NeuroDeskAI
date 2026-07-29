import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/api/api_error.dart';
import '../../../core/widgets/app_components.dart';
import '../../../core/widgets/screen_header.dart';
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

    return Scaffold(
      body: RefreshIndicator(
        onRefresh: () => ref.refresh(tasksProvider.future),
        child: ListView(
          padding: kScreenPadding,
          children: [
            const StitchScreenHeader(title: 'Görevler'),
            Row(
              children: [
                Expanded(child: _SegmentedControl(value: _filter, onChanged: (value) => setState(() => _filter = value))),
                IconButton(
                  tooltip: 'Görevleri temizle',
                  onPressed: () => _confirmClear(context, ref),
                  icon: const Icon(Icons.cleaning_services_outlined, size: 20),
                ),
              ],
            ),
            const SizedBox(height: 20),
            tasks.when(
              data: (items) => items.isEmpty
                  ? const _EmptyList(message: 'Henüz görev yok.')
                  : _TaskLists(tasks: items, filter: _filter),
              error: (error, stackTrace) => _EmptyList(
                message: readableApiError(error, 'Görevler alınamadı.'),
              ),
              loading: () => const Padding(
                padding: EdgeInsets.only(top: 40),
                child: Center(child: CircularProgressIndicator()),
              ),
            ),
          ],
        ),
      ),
      floatingActionButton: FloatingActionButton(
        backgroundColor: Theme.of(context).colorScheme.secondaryContainer,
        tooltip: 'Görev ekle',
        onPressed: () => _showCreateTaskSheet(context, ref),
        child: const Icon(Icons.add, color: Colors.white),
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

class _SegmentedControl extends StatelessWidget {
  const _SegmentedControl({required this.value, required this.onChanged});

  final _TaskFilter value;
  final ValueChanged<_TaskFilter> onChanged;

  static const _labels = {
    _TaskFilter.today: 'Bugün',
    _TaskFilter.week: 'Bu Hafta',
    _TaskFilter.all: 'Tümü',
  };

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Container(
      padding: const EdgeInsets.all(4),
      decoration: BoxDecoration(
        color: theme.colorScheme.surfaceContainerHigh,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        children: [
          for (final entry in _labels.entries)
            Expanded(
              child: GestureDetector(
                onTap: () => onChanged(entry.key),
                child: AnimatedContainer(
                  duration: const Duration(milliseconds: 150),
                  padding: const EdgeInsets.symmetric(vertical: 8),
                  decoration: BoxDecoration(
                    color: value == entry.key ? Colors.white : null,
                    borderRadius: BorderRadius.circular(8),
                    boxShadow: value == entry.key
                        ? const [BoxShadow(color: Color(0x0D000000), blurRadius: 8)]
                        : null,
                  ),
                  child: Text(
                    entry.value,
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                      color: value == entry.key
                          ? theme.colorScheme.primary
                          : theme.colorScheme.onSurfaceVariant,
                    ),
                  ),
                ),
              ),
            ),
        ],
      ),
    );
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
        SectionHeading(title: 'Bekleyen Görevler'),
        const SizedBox(height: 4),
        Align(
          alignment: Alignment.centerLeft,
          child: StatusPill(label: '${open.length} Yeni', color: const Color(0xFF3525CD)),
        ),
        const SizedBox(height: 12),
        if (open.isEmpty)
          const _EmptyList(message: 'Bekleyen görev yok.')
        else
          ...open.map((task) => _TaskTile(task: task)),
        if (completed.isNotEmpty) ...[
          const SizedBox(height: 20),
          Row(
            children: [
              Icon(Icons.check_circle, color: Theme.of(context).colorScheme.outline, size: 20),
              const SizedBox(width: 8),
              Text('Tamamlananlar',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        color: Theme.of(context).colorScheme.outline,
                      )),
            ],
          ),
          const SizedBox(height: 10),
          Opacity(
            opacity: 0.6,
            child: Column(children: completed.map((task) => _TaskTile(task: task)).toList()),
          ),
        ],
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
    final theme = Theme.of(context);

    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(kCardRadius),
        child: Container(
          decoration: BoxDecoration(
            color: isCompleted ? theme.colorScheme.surfaceContainer : Colors.white,
            boxShadow: isCompleted ? null : kCardShadow,
          ),
          child: IntrinsicHeight(
            child: Row(
              children: [
                Container(width: 6, color: priorityColor(task.priority)),
                Expanded(
                  child: Padding(
                    padding: const EdgeInsets.all(14),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Padding(
                          padding: const EdgeInsets.only(top: 2),
                          child: GestureDetector(
                            onTap: isCompleted
                                ? null
                                : () async {
                                    await ref.read(tasksRepositoryProvider).completeTask(task.id);
                                    ref.invalidate(tasksProvider);
                                  },
                            child: Container(
                              width: 24,
                              height: 24,
                              decoration: BoxDecoration(
                                color: isCompleted ? theme.colorScheme.primary : null,
                                border: Border.all(
                                  color: isCompleted ? theme.colorScheme.primary : const Color(0xFFC7C4D8),
                                  width: 2,
                                ),
                                borderRadius: BorderRadius.circular(6),
                              ),
                              child: isCompleted
                                  ? const Icon(Icons.check, size: 16, color: Colors.white)
                                  : null,
                            ),
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
                                  fontWeight: FontWeight.w600,
                                  decoration: isCompleted ? TextDecoration.lineThrough : null,
                                  color: isCompleted ? theme.colorScheme.outline : null,
                                ),
                              ),
                              const SizedBox(height: 2),
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
                          icon: Icon(Icons.more_vert, color: theme.colorScheme.outline, size: 20),
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
                ),
              ],
            ),
          ),
        ),
      ),
    );
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
    final now = DateTime.now();
    final dueDay = DateTime(local.year, local.month, local.day);
    final today = DateTime(now.year, now.month, now.day);
    final time = '${local.hour.toString().padLeft(2, '0')}:${local.minute.toString().padLeft(2, '0')}';
    if (dueDay == today) return 'Bugün $time';
    if (dueDay == today.add(const Duration(days: 1))) return 'Yarın $time';
    return '${local.day.toString().padLeft(2, '0')}.${local.month.toString().padLeft(2, '0')} $time';
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
              onChanged: (value) => setState(() => _priority = value ?? 'medium'),
            ),
            const SizedBox(height: 12),
            OutlinedButton.icon(
              onPressed: _pickDueDate,
              icon: const Icon(Icons.calendar_today_outlined),
              label: Text(_dueAt == null ? 'Teslim tarihi seç (opsiyonel)' : _formatDueAt(_dueAt!)),
            ),
            if (_errorMessage != null) ...[
              const SizedBox(height: 10),
              Text(_errorMessage!, style: TextStyle(color: Theme.of(context).colorScheme.error)),
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
    final time = await showTimePicker(context: context, initialTime: TimeOfDay.now());
    if (!mounted) return;
    setState(() {
      _dueAt = DateTime(date.year, date.month, date.day, time?.hour ?? 9, time?.minute ?? 0);
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
    return AppCard(child: Text(message));
  }
}
