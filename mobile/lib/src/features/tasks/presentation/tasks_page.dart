import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../data/tasks_repository.dart';
import '../domain/task.dart';

class TasksPage extends ConsumerWidget {
  const TasksPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final tasks = ref.watch(tasksProvider);

    return RefreshIndicator(
      onRefresh: () => ref.refresh(tasksProvider.future),
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Text('Gorevler', style: Theme.of(context).textTheme.headlineMedium),
          const SizedBox(height: 16),
          tasks.when(
            data: (items) => items.isEmpty
                ? const _EmptyList(message: 'Henuz gorev yok.')
                : Column(
                    children: items
                        .map((task) => _TaskTile(task: task))
                        .toList(growable: false),
                  ),
            error: (error, stackTrace) => const _EmptyList(message: 'Gorevler alinamadi.'),
            loading: () => const Center(child: CircularProgressIndicator()),
          ),
        ],
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

    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      child: ListTile(
        title: Text(task.title),
        subtitle: Text(task.description ?? task.priority),
        trailing: isCompleted
            ? const Icon(Icons.check_circle)
            : IconButton(
                tooltip: 'Tamamla',
                icon: const Icon(Icons.check),
                onPressed: () async {
                  await ref.read(tasksRepositoryProvider).completeTask(task.id);
                  ref.invalidate(tasksProvider);
                },
              ),
      ),
    );
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
