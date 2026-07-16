import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/api/api_client.dart';
import '../domain/user_profile.dart';

final settingsRepositoryProvider = Provider<SettingsRepository>((ref) {
  return SettingsRepository(ref.watch(dioProvider));
});

final currentUserProvider = FutureProvider.autoDispose<CurrentUser>((ref) {
  return ref.watch(settingsRepositoryProvider).getCurrentUser();
});

class SettingsRepository {
  const SettingsRepository(this._dio);

  final Dio _dio;

  Future<CurrentUser> getCurrentUser() async {
    final response = await _dio.get<Map<String, dynamic>>('/api/v1/users/me');
    return CurrentUser.fromJson(response.data!);
  }

  Future<CurrentUser> updateProfile({
    required String fullName,
    String? title,
  }) async {
    final response = await _dio.patch<Map<String, dynamic>>(
      '/api/v1/users/me',
      data: {
        'full_name': fullName.trim(),
        'title': _emptyToNull(title),
      },
    );
    return CurrentUser.fromJson(response.data!);
  }

  String? _emptyToNull(String? value) {
    final trimmed = value?.trim();
    return trimmed == null || trimmed.isEmpty ? null : trimmed;
  }
}
