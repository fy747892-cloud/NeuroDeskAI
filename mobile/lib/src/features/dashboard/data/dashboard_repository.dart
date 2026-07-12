import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/api/api_client.dart';
import '../domain/dashboard_models.dart';

final dashboardRepositoryProvider = Provider<DashboardRepository>((ref) {
  return DashboardRepository(ref.watch(dioProvider));
});

final dashboardProvider = FutureProvider.autoDispose<DashboardData>((ref) async {
  return ref.watch(dashboardRepositoryProvider).getDashboard();
});

class DashboardRepository {
  const DashboardRepository(this._dio);

  final Dio _dio;

  Future<DashboardData> getDashboard() async {
    final response = await _dio.get<Map<String, dynamic>>('/api/v1/dashboard');
    return DashboardData.fromJson(response.data!);
  }
}
