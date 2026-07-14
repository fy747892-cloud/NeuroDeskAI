import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/api/api_client.dart';
import '../domain/app_notification.dart';

final notificationsRepositoryProvider =
    Provider<NotificationsRepository>((ref) {
  return NotificationsRepository(ref.watch(dioProvider));
});

final notificationsProvider =
    FutureProvider.autoDispose<List<AppNotification>>((ref) async {
  return ref.watch(notificationsRepositoryProvider).listNotifications();
});

class NotificationsRepository {
  const NotificationsRepository(this._dio);

  final Dio _dio;

  Future<List<AppNotification>> listNotifications() async {
    final response = await _dio.get<List<dynamic>>('/api/v1/notifications');
    return response.data!
        .cast<Map<String, dynamic>>()
        .map(AppNotification.fromJson)
        .toList(growable: false);
  }

  Future<AppNotification> markRead(String notificationId) async {
    final response = await _dio.patch<Map<String, dynamic>>(
      '/api/v1/notifications/$notificationId/read',
    );
    return AppNotification.fromJson(response.data!);
  }
}
