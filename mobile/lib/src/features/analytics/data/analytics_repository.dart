import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/api/api_client.dart';
import '../domain/analytics_models.dart';

final analyticsRepositoryProvider = Provider<AnalyticsRepository>((ref) {
  return AnalyticsRepository(ref.watch(dioProvider));
});

final analyticsSnapshotProvider =
    FutureProvider.autoDispose<AnalyticsSnapshot>((ref) async {
  return ref.watch(analyticsRepositoryProvider).getSnapshot();
});

class AnalyticsRepository {
  const AnalyticsRepository(this._dio);

  final Dio _dio;

  Future<AnalyticsSnapshot> getSnapshot() async {
    final responses = await Future.wait([
      _dio.get<Map<String, dynamic>>('/api/v1/analytics/overview'),
      _dio.get<List<dynamic>>('/api/v1/analytics/tasks'),
      _dio.get<List<dynamic>>('/api/v1/analytics/calls'),
      _dio.get<List<dynamic>>('/api/v1/analytics/ai'),
    ]);

    return AnalyticsSnapshot(
      overview: AnalyticsOverview.fromJson(
        responses[0].data! as Map<String, dynamic>,
      ),
      taskMetrics: (responses[1].data! as List<dynamic>)
          .cast<Map<String, dynamic>>()
          .map(TaskMetric.fromJson)
          .toList(growable: false),
      callMetrics: (responses[2].data! as List<dynamic>)
          .cast<Map<String, dynamic>>()
          .map(CallMetric.fromJson)
          .toList(growable: false),
      aiMetrics: (responses[3].data! as List<dynamic>)
          .cast<Map<String, dynamic>>()
          .map(AiMetric.fromJson)
          .toList(growable: false),
    );
  }

  Future<void> aggregateToday() async {
    await _dio.post<Map<String, dynamic>>(
      '/api/v1/analytics/aggregate',
      data: <String, dynamic>{},
    );
  }
}
