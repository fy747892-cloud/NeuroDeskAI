import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/api/api_client.dart';
import '../domain/task.dart';

final tasksRepositoryProvider = Provider<TasksRepository>((ref) {
  return TasksRepository(ref.watch(dioProvider));
});

final tasksProvider = FutureProvider.autoDispose<List<Task>>((ref) async {
  return ref.watch(tasksRepositoryProvider).listTasks();
});

class TasksRepository {
  const TasksRepository(this._dio);

  final Dio _dio;

  Future<List<Task>> listTasks() async {
    final response = await _dio.get<List<dynamic>>('/api/v1/tasks');
    return response.data!
        .cast<Map<String, dynamic>>()
        .map(Task.fromJson)
        .toList(growable: false);
  }

  Future<Task> completeTask(String taskId) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/api/v1/tasks/$taskId/complete',
    );
    return Task.fromJson(response.data!);
  }
}
