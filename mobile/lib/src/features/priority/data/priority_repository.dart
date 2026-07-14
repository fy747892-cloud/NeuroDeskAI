import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/api/api_client.dart';
import '../domain/priority_queue.dart';

final priorityRepositoryProvider = Provider<PriorityRepository>((ref) {
  return PriorityRepository(ref.watch(dioProvider));
});

final priorityQueueProvider =
    FutureProvider.autoDispose.family<PriorityQueue, int>((ref, limit) {
  return ref.watch(priorityRepositoryProvider).getQueue(limit: limit);
});

class PriorityRepository {
  const PriorityRepository(this._dio);

  final Dio _dio;

  Future<PriorityQueue> getQueue({int limit = 25}) async {
    final response = await _dio.get<Map<String, dynamic>>(
      '/api/v1/priority/queue',
      queryParameters: {'limit': limit},
    );
    return PriorityQueue.fromJson(response.data!);
  }
}
